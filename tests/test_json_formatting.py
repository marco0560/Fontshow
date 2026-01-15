from fontshow.json_format import dumps_pretty


def test_dumps_pretty_compacts_short_numeric_lists():
    data = {"ranges": [[32, 95], [97, 127]]}
    s = dumps_pretty(data, indent=2, ensure_ascii=False)

    assert "  [32, 95]" in s
    assert "  [97, 127]" in s
    assert '"ranges": [\n' in s


def test_dumps_pretty_does_not_compact_long_numeric_lists():
    data = {"nums": list(range(20))}
    s = dumps_pretty(data, indent=2, ensure_ascii=False)

    assert '"nums": [\n' in s
    assert "[0, 1, 2, 3" not in s
