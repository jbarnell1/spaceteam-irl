"""Phone UI and JSON API served by the hub."""

from __future__ import annotations

import itertools
from pathlib import Path

from aiohttp import web

from .events import ButtonEvent
from .hub import Hub

STATIC_DIR = Path(__file__).parent / "static"
HUB_KEY = web.AppKey("hub", Hub)

_sim_seq = itertools.count(1_000_000_000)


def create_app(hub: Hub) -> web.Application:
    app = web.Application()
    app[HUB_KEY] = hub
    app.add_routes([
        web.get("/", index),
        web.get("/manifest.webmanifest", manifest),
        web.get("/api/state", get_state),
        web.post("/api/theme", set_theme),
        web.post("/api/themes/reload", reload_themes),
        web.post("/api/settings", update_settings),
        web.post("/api/buttons/{id}/preview", preview_button),
        web.post("/api/buttons/{id}/press", simulate_press),
        web.post("/api/stop", stop_audio),
    ])
    return app


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC_DIR / "index.html")


async def manifest(request: web.Request) -> web.Response:
    return web.json_response({
        "name": "Playset",
        "short_name": "Playset",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f1222",
        "theme_color": "#0f1222",
    }, content_type="application/manifest+json")


async def get_state(request: web.Request) -> web.Response:
    return web.json_response(request.app[HUB_KEY].snapshot())


async def _json_body(request: web.Request) -> dict:
    try:
        data = await request.json()
    except ValueError:
        raise web.HTTPBadRequest(text="expected JSON body")
    if not isinstance(data, dict):
        raise web.HTTPBadRequest(text="expected JSON object")
    return data


def _button_id(request: web.Request) -> int:
    try:
        return int(request.match_info["id"])
    except ValueError:
        raise web.HTTPBadRequest(text="bad button id")


async def set_theme(request: web.Request) -> web.Response:
    hub = request.app[HUB_KEY]
    data = await _json_body(request)
    if not await hub.set_theme(str(data.get("id", ""))):
        raise web.HTTPNotFound(text="no such theme")
    return web.json_response(hub.snapshot())


async def reload_themes(request: web.Request) -> web.Response:
    hub = request.app[HUB_KEY]
    hub.reload_themes()
    return web.json_response(hub.snapshot())


async def update_settings(request: web.Request) -> web.Response:
    hub = request.app[HUB_KEY]
    data = await _json_body(request)
    try:
        hub.update_settings(data)
    except (TypeError, ValueError) as exc:
        raise web.HTTPBadRequest(text=f"bad settings: {exc}")
    return web.json_response(hub.snapshot())


async def preview_button(request: web.Request) -> web.Response:
    """Parent taps a button card: hear one of its clips, even during quiet hours."""
    hub = request.app[HUB_KEY]
    clip = await hub.play_button_clip(_button_id(request), force=True)
    return web.json_response({"clip": clip.name if clip else None})


async def simulate_press(request: web.Request) -> web.Response:
    """Same path as a real press (dedupe, quiet hours, mode). For testing without hardware."""
    hub = request.app[HUB_KEY]
    accepted = await hub.handle_event(ButtonEvent(button=_button_id(request), seq=next(_sim_seq)))
    return web.json_response({"accepted": accepted})


async def stop_audio(request: web.Request) -> web.Response:
    await request.app[HUB_KEY].player.stop()
    return web.json_response({"ok": True})
