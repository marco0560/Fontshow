def minimal_valid_entry(extra: dict | None = None) -> dict:
    entry = {
        "path": "/usr/share/fonts/test.ttf",
        "format": "TrueType",
        "style": "Regular",
        "family": "Test Family",
        "identity": {"family": "Test Family"},
        "base_names": ["Test Family"],
    }
    if extra:
        entry.update(extra)
    return entry
