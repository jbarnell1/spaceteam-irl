from datetime import datetime

from playset_hub.config import QuietHours, State
from playset_hub.events import ButtonEvent
from playset_hub.hub import Hub
from playset_hub.player import RecordingPlayer
from playset_hub.themes import ThemeLibrary


async def test_press_plays_clip_from_active_theme(make_hub):
    hub = make_hub()
    await hub.set_theme("spaceship")
    hub.player.played.clear()
    assert await hub.handle_event(ButtonEvent(1, 1))
    (path, volume, interrupt), = hub.player.played
    assert path.parent.name == "button-1" and path.parent.parent.name == "spaceship"
    assert interrupt is True  # default play mode
    assert volume == 50


async def test_duplicate_retry_plays_once(make_hub):
    hub = make_hub()
    await hub.handle_event(ButtonEvent(1, 7))
    assert not await hub.handle_event(ButtonEvent(1, 7))
    assert len(hub.player.played) == 1
    assert hub.buttons[1].presses == 1


async def test_volume_capped_by_config(make_hub):
    hub = make_hub(max_volume=40)
    hub.update_settings({"volume": 100})
    await hub.handle_event(ButtonEvent(1, 1))
    assert hub.player.played[-1][1] == 40
    assert hub.snapshot()["settings"]["volume"] == 100  # remembers the slider, plays at the cap


async def test_queue_mode_passes_interrupt_false(make_hub):
    hub = make_hub()
    hub.update_settings({"play_mode": "queue"})
    await hub.handle_event(ButtonEvent(1, 1))
    assert hub.player.played[-1][2] is False


async def test_quiet_hours_silence_presses_but_not_parent_actions(make_hub):
    hub = make_hub(now=datetime(2026, 11, 16, 21, 0))
    hub.update_settings({"quiet_hours": {"enabled": True, "start": "19:30", "end": "07:00"}})
    assert await hub.handle_event(ButtonEvent(1, 1))  # accepted and logged...
    assert hub.player.played == []  # ...but silent
    assert await hub.play_button_clip(1, force=True) is not None  # phone preview still plays
    await hub.set_theme("pirate-ship")  # theme confirmation still plays
    assert len(hub.player.played) == 2


def test_quiet_hours_windows():
    from datetime import time as t
    overnight = QuietHours(enabled=True, start="19:30", end="07:00")
    assert overnight.active_at(t(23, 0)) and overnight.active_at(t(6, 59))
    assert not overnight.active_at(t(7, 0)) and not overnight.active_at(t(12, 0))
    nap = QuietHours(enabled=True, start="13:00", end="15:00")
    assert nap.active_at(t(14, 0)) and not nap.active_at(t(15, 0))
    assert not QuietHours(enabled=False).active_at(t(23, 0))


async def test_theme_persists_and_confirm_sound(make_hub, tmp_path):
    hub = make_hub()
    assert await hub.set_theme("spaceship")
    assert hub.player.played[-1][0].name == "select.wav"
    assert hub.player.played[-1][0].parent.name == "spaceship"
    await hub.set_theme("pirate-ship")  # no theme select sound: falls back to _system
    assert hub.player.played[-1][0].parent.name == "_system"
    assert not await hub.set_theme("nope")
    assert State.load(hub.state_path).active_theme == "pirate-ship"


async def test_defaults_to_first_theme_and_startup_chime(make_hub):
    hub = make_hub()
    assert hub.state.active_theme == "pirate-ship"
    await hub.startup()
    assert hub.player.played[-1][0].name == "startup.wav"


async def test_button_without_clips_is_silent(make_hub):
    hub = make_hub()
    await hub.set_theme("spaceship")
    hub.player.played.clear()
    assert await hub.handle_event(ButtonEvent(5, 1))
    assert hub.player.played == []


async def test_battery_tracking_and_press_log(make_hub):
    hub = make_hub(low_battery_mv=3500)
    await hub.handle_event(ButtonEvent(2, 1, battery_mv=3400, rssi=-60))
    await hub.handle_event(ButtonEvent(3, 1, battery_mv=4000))
    await hub.handle_event(ButtonEvent(3, 2, battery_mv=0))  # unknown reading keeps the last one
    snap = {b["id"]: b for b in hub.snapshot()["buttons"]}
    assert snap[2]["battery_low"] and snap[2]["battery_mv"] == 3400
    assert not snap[3]["battery_low"] and snap[3]["battery_mv"] == 4000
    assert snap[1]["battery_mv"] is None and snap[1]["last_press"] is None
    rows = hub.press_log_path.read_text().strip().splitlines()
    assert rows[0].startswith("time,button,seq") and len(rows) == 4


async def test_bad_quiet_hours_rejected(make_hub):
    hub = make_hub()
    try:
        hub.update_settings({"quiet_hours": {"enabled": True, "start": "late", "end": "07:00"}})
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    assert hub.state.quiet_hours.start == "19:30"


async def test_state_survives_restart(tmp_path, themes_dir):
    def new_hub():
        from playset_hub.config import Config
        return Hub(Config(), ThemeLibrary(themes_dir), RecordingPlayer(), state_path=tmp_path / "s.json")

    hub = new_hub()
    await hub.set_theme("spaceship")
    hub.update_settings({"volume": 35, "play_mode": "queue"})
    again = new_hub()
    assert (again.state.active_theme, again.state.volume, again.state.play_mode) == ("spaceship", 35, "queue")
