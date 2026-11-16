"""Modes decide what a press does.

The alpha has one mode: play the button's clip for the active theme.
Mini games (Captain's orders, Sequence, Mission story, Race the clock) will be
new Mode subclasses that the phone UI switches to and from.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .events import ButtonEvent

if TYPE_CHECKING:
    from .hub import Hub


class Mode:
    id = "base"
    name = "Base"

    async def on_enter(self, hub: "Hub") -> None:
        pass

    async def on_exit(self, hub: "Hub") -> None:
        pass

    async def on_press(self, hub: "Hub", event: ButtonEvent) -> None:
        raise NotImplementedError


class FreePlayMode(Mode):
    """Default: each button plays one of its clips from the active theme."""

    id = "free-play"
    name = "Free play"

    async def on_press(self, hub: "Hub", event: ButtonEvent) -> None:
        await hub.play_button_clip(event.button)
