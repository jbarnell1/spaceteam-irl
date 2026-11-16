import pytest

from playset_hub.web import create_app


@pytest.fixture
async def client(aiohttp_client, make_hub):
    hub = make_hub()
    c = await aiohttp_client(create_app(hub))
    c.hub = hub
    return c


async def test_index_and_state(client):
    r = await client.get("/")
    assert r.status == 200 and "Playset" in await r.text()
    state = await (await client.get("/api/state")).json()
    assert [t["id"] for t in state["themes"]] == ["pirate-ship", "spaceship"]
    assert len(state["buttons"]) == 5
    assert state["settings"]["max_volume"] == 70


async def test_set_theme(client):
    r = await client.post("/api/theme", json={"id": "spaceship"})
    assert r.status == 200 and (await r.json())["active_theme"] == "spaceship"
    assert (await client.post("/api/theme", json={"id": "nope"})).status == 404
    assert (await client.post("/api/theme", data="not json")).status == 400


async def test_settings_and_validation(client):
    r = await client.post("/api/settings", json={"volume": 30, "play_mode": "queue"})
    s = (await r.json())["settings"]
    assert s["volume"] == 30 and s["play_mode"] == "queue"
    r = await client.post("/api/settings", json={"quiet_hours": {"start": "nope"}})
    assert r.status == 400


async def test_cannot_raise_volume_ceiling_from_ui(client):
    await client.post("/api/settings", json={"max_volume": 100, "volume": 100})
    state = await (await client.get("/api/state")).json()
    assert state["settings"]["max_volume"] == 70


async def test_preview_and_simulated_press(client):
    await client.post("/api/theme", json={"id": "spaceship"})
    r = await client.post("/api/buttons/2/preview")
    assert (await r.json())["clip"] == "shields.wav"
    r = await client.post("/api/buttons/1/press")
    assert (await r.json())["accepted"] is True
    assert client.hub.buttons[1].presses == 1
    assert (await client.post("/api/buttons/x/press")).status == 400
