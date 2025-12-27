from types import SimpleNamespace


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


def make_fc_query_output(
    *,
    lang: str | None = None,
    scripts: list[str] | None = None,
    decorative: bool | None = None,
    color: bool | None = None,
    variable: bool | None = None,
):
    """
    Factory helper for mocking fc-query output.

    Returns an object compatible with the result of run_command(),
    exposing a 'stdout' attribute.
    """
    lines: list[str] = []

    if lang:
        lines.append(f"lang: {lang}")

    if scripts:
        caps = " ".join(f"otlayout:{s}" for s in scripts)
        lines.append(f'capability: "{caps}"')

    if decorative is not None:
        lines.append(f"decorative: {'true' if decorative else 'false'}")

    if color is not None:
        lines.append(f"color: {'true' if color else 'false'}")

    if variable is not None:
        lines.append(f"variable: {'true' if variable else 'false'}")

    return SimpleNamespace(stdout="\n".join(lines))
