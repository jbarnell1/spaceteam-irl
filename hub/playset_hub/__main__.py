"""Run the hub: `uv run python -m playset_hub --themes themes --serial /dev/ttyACM0`."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from aiohttp import web

from .config import Config
from .hub import Hub
from .player import RecordingPlayer, SubprocessPlayer
from .sources import run_serial, run_stdin
from .themes import ThemeLibrary
from .web import create_app

log = logging.getLogger("playset_hub")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="playset_hub", description="Playset Buttons hub")
    p.add_argument("--themes", type=Path, default=Path("themes"), help="themes folder")
    p.add_argument("--config", type=Path, default=Path("config.json"), help="hand-edited config (optional)")
    p.add_argument("--data", type=Path, default=Path("data"), help="where state.json and presses.csv go")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--serial", help="dongle serial port, e.g. /dev/ttyACM0 or COM5")
    src.add_argument("--stdin", action="store_true", help="type 1-5 + Enter to simulate presses")
    p.add_argument("--no-audio", action="store_true", help="log clips instead of playing them")
    p.add_argument("--host", help="override bind address from config")
    p.add_argument("--port", type=int, help="override port from config")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


async def main_async(args: argparse.Namespace) -> None:
    config = Config.load(args.config)
    library = ThemeLibrary(args.themes, button_count=len(config.buttons))
    player = RecordingPlayer() if args.no_audio else SubprocessPlayer(config.player_cmd, config.queue_limit)
    hub = Hub(config, library, player, state_path=args.data / "state.json", press_log_path=args.data / "presses.csv")
    log.info("themes: %s (active: %s)", ", ".join(library.themes) or "none", hub.state.active_theme)

    runner = web.AppRunner(create_app(hub))
    await runner.setup()
    host, port = args.host or config.host, args.port or config.port
    await web.TCPSite(runner, host, port).start()
    log.info("phone UI on http://%s:%d", host, port)

    await hub.startup()

    try:
        if args.serial:
            await run_serial(args.serial, hub.handle_event)
        elif args.stdin:
            await run_stdin(hub.handle_event)
        await asyncio.Event().wait()  # web-only, or stdin closed: keep serving
    finally:
        await runner.cleanup()


def main(argv=None) -> None:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
