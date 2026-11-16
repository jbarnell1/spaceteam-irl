import asyncio
import sys
from pathlib import Path

from playset_hub.player import SubprocessPlayer


def sleeper(seconds: float) -> list[str]:
    # Stand-in for mpv: a process that "plays" for `seconds`.
    return [sys.executable, "-c", f"import time; time.sleep({seconds})", "{path}", "{volume}"]


async def test_interrupt_kills_current_clip():
    player = SubprocessPlayer(sleeper(10))
    await player.play(Path("a.wav"), 50, interrupt=True)
    first = player._proc
    await player.play(Path("b.wav"), 50, interrupt=True)
    assert first.returncode is not None  # killed
    assert player._proc is not first and player._proc.returncode is None
    await player.stop()
    assert player._proc is None


async def test_queue_waits_and_respects_limit():
    player = SubprocessPlayer(sleeper(0.3), queue_limit=2)
    await player.play(Path("a.wav"), 50, interrupt=False)
    first = player._proc
    for name in ("b", "c", "d"):  # d is over the limit and dropped
        await player.play(Path(f"{name}.wav"), 50, interrupt=False)
    assert first.returncode is None  # not interrupted
    assert [p.name for p, _ in player._pending] == ["b.wav", "c.wav"]
    await asyncio.wait_for(player._worker, timeout=5)
    assert not player._pending


async def test_missing_player_binary_is_not_fatal():
    player = SubprocessPlayer(["definitely-not-a-real-player-binary", "{path}"])
    await player.play(Path("a.wav"), 50, interrupt=True)
    assert player._proc is None
