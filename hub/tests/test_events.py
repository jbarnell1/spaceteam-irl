from playset_hub.events import ButtonEvent, Deduper, parse_line


def test_parse_press_line():
    line = '{"t":"btn","v":1,"b":3,"e":1,"seq":4021,"mv":3912,"rssi":-58,"src":"34:85:18:aa:bb:cc"}\n'
    ev = parse_line(line)
    assert ev is not None
    assert (ev.button, ev.seq, ev.event, ev.battery_mv, ev.rssi) == (3, 4021, 1, 3912, -58)


def test_parse_ignores_noise_hello_and_other_versions():
    assert parse_line("ESP-ROM:esp32s3-20210327") is None
    assert parse_line('{"t":"hello","fw":"dongle-0.1","mac":"x","ch":1}') is None
    assert parse_line('{"t":"btn","v":2,"b":1,"seq":1}') is None
    assert parse_line('{"t":"btn","v":1,"seq":1}') is None  # no button id
    assert parse_line('{"t":"btn","v":1,"b":1,') is None  # truncated
    assert parse_line("[1,2]") is None


def test_dedupe_drops_retries_within_window(clock):
    d = Deduper(window_s=2.0, clock=clock)
    assert not d.is_duplicate(ButtonEvent(1, 10))
    clock.t += 0.05
    assert d.is_duplicate(ButtonEvent(1, 10))  # radio retry
    assert not d.is_duplicate(ButtonEvent(2, 10))  # other button, same seq
    assert not d.is_duplicate(ButtonEvent(1, 11))  # next press


def test_dedupe_accepts_same_seq_after_window(clock):
    # A button that cold-boots can reuse a seq; after the window it must be heard.
    d = Deduper(window_s=2.0, clock=clock)
    assert not d.is_duplicate(ButtonEvent(1, 5))
    clock.t += 2.5
    assert not d.is_duplicate(ButtonEvent(1, 5))
