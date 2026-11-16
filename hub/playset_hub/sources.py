"""Where button events come from: the USB dongle, or the keyboard for bench testing."""

from __future__ import annotations

import asyncio
import itertools
import json
import logging
import sys
import threading
import time
from typing import Awaitable, Callable

from .events import ButtonEvent, parse_line

log = logging.getLogger(__name__)

EventHandler = Callable[[ButtonEvent], Awaitable[object]]


async def run_serial(port: str, handler: EventHandler, baud: int = 115200) -> None:
    """Read JSON lines from the dongle forever, reconnecting if it is unplugged."""
    import serial  # pyserial

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[ButtonEvent] = asyncio.Queue()

    def reader() -> None:
        while True:
            try:
                with serial.Serial(port, baud, timeout=1) as ser:
                    log.info("dongle connected on %s", port)
                    ser.write(b"?\n")
                    while True:
                        raw = ser.readline()
                        if not raw:
                            continue
                        line = raw.decode("utf-8", errors="replace")
                        event = parse_line(line)
                        if event is not None:
                            loop.call_soon_threadsafe(queue.put_nowait, event)
                        elif line.startswith('{"t":"hello"'):
                            try:
                                log.info("dongle: %s", json.loads(line))
                            except json.JSONDecodeError:
                                pass
            except (serial.SerialException, OSError) as exc:
                log.warning("dongle on %s unavailable (%s); retrying in 2s", port, exc)
                time.sleep(2)

    threading.Thread(target=reader, name="dongle-reader", daemon=True).start()
    while True:
        await handler(await queue.get())


async def run_stdin(handler: EventHandler) -> None:
    """Bench mode: type a button number (1-5) and Enter to simulate a press."""
    loop = asyncio.get_running_loop()
    seq = itertools.count(1)
    print("stdin mode: type 1-5 and Enter to press a button", flush=True)
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            return
        for token in line.split():
            if token.isdigit():
                await handler(ButtonEvent(button=int(token), seq=next(seq)))
