import random

from playset_hub.themes import ClipPicker, ThemeLibrary


def test_library_scans_themes(themes_dir):
    lib = ThemeLibrary(themes_dir)
    assert list(lib.themes) == ["pirate-ship", "spaceship"]  # _system skipped
    space = lib.get("spaceship")
    assert space.name == "Spaceship" and space.icon == "🚀"
    assert [p.name for p in space.clips[1]] == ["countdown.mp3", "launch.mp3"]
    assert space.clips[5] == []
    assert space.select_sound.name == "select.wav"
    pirate = lib.get("pirate-ship")
    assert pirate.name == "Pirate Ship"  # from folder name
    assert [p.name for p in pirate.clips[1]] == ["arr.ogg"]  # notes.txt ignored
    assert lib.system_sound("startup").name == "startup.wav"
    assert lib.system_sound("missing") is None


def test_picker_never_repeats_back_to_back(themes_dir):
    theme = ThemeLibrary(themes_dir).get("spaceship")
    picker = ClipPicker(random.Random(0))
    picks = [picker.pick(theme, 1) for _ in range(50)]
    assert all(a != b for a, b in zip(picks, picks[1:]))
    assert {p.name for p in picks} == {"launch.mp3", "countdown.mp3"}


def test_picker_single_clip_and_empty(themes_dir):
    theme = ThemeLibrary(themes_dir).get("spaceship")
    picker = ClipPicker(random.Random(0))
    assert picker.pick(theme, 2).name == "shields.wav"
    assert picker.pick(theme, 2).name == "shields.wav"
    assert picker.pick(theme, 4) is None


def test_missing_root_is_empty(tmp_path):
    assert ThemeLibrary(tmp_path / "nope").themes == {}
