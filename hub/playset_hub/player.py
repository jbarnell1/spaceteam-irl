"""Audio playback with interrupt or queue behaviour.

The hub talks to a Player. SubprocessPlayer runs one external process per
clip (mpv by default); killing it is the interrupt. RecordingPlayer is for
tests and for running without audio.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from collections import deque
from pathlib import Path

log = logging.getLogger(__name__)


class Player:
    async def play(self, path: Path, volume: int, interrupt: bool) -> None:
        raise NotImplementedError

    async def stop(self) -> None:
        raise NotImplementedError


class SubprocessPlayer(Player):
    def __init__(self, cmd_template: list[str], queue_limit: int = 3):
        self.cmd_template = cmd_template
        self.queue_limit = queue_limit
        self._proc: asyncio.subprocess.Process | None = None
        self._pending: deque[tuple[Path, int]] = deque()
        self._worker: asyncio.Task | None = None
        if shutil.which(cmd_template[0]) is None:
            log.warning("audio player %r not found on PATH; presses will be silent", cmd_template[0])

    def _cmd(self, path: Path, volume: int) -> list[str]:
        return [part.format(path=str(path), volume=volume) for part in self.cmd_template]

    async def play(self, path: Path, volume: int, interrupt: bool) -> None:
        if interrupt:
            self._pending.clear()
            await self._kill_current()
            await self._start(path, volume)
            return
        if self._is_playing() or self._pending:
            if len(self._pending) < self.queue_limit:
                self._pending.append((path, volume))
            self._ensure_worker()
        else:
            await self._start(path, volume)
            self._ensure_worker()

    async def stop(self) -> None:
        self._pending.clear()
        await self._kill_current()

    def _is_playing(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def _start(self, path: Path, volume: int) -> None:
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *self._cmd(path, volume),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except (FileNotFoundError, PermissionError) as exc:
            log.error("could not start player: %s", exc)
            self._proc = None

    async def _kill_current(self) -> None:
        proc = self._proc
        if proc and proc.returncode is None:
            proc.kill()
            await proc.wait()
        self._proc = None

    def _ensure_worker(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._drain())

    async def _drain(self) -> None:
        while True:
            if self._proc is not None:
                await self._proc.wait()
            if not self._pending:
                return
            path, volume = self._pending.popleft()
            await self._start(path, volume)


class RecordingPlayer(Player):
    """Records what would have played. Used by tests and `--no-audio`."""

    def __init__(self):
        self.played: list[tuple[Path, int, bool]] = []
        self.stops = 0

    async def play(self, path: Path, volume: int, interrupt: bool) -> None:
        log.info("play %s at volume %d (%s)", path, volume, "interrupt" if interrupt else "queue")
        self.played.append((path, volume, interrupt))

    async def stop(self) -> None:
        self.stops += 1
