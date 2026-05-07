#!/usr/bin/env python3
"""
Synchronize schema documentation with the canonical JSON schema.

This maintenance script updates generated sections in the active
inventory schema documentation so the rendered markdown stays aligned
with the authoritative schema file in the repository.

Responsibilities
----------------
- Read the canonical inventory schema JSON document.
- Generate a deterministic field-reference section from schema metadata.
- Replace marker-bounded generated blocks in the schema markdown file.
- Write updated documentation only when the rendered output changes.

Design principles
-----------------
Schema documentation must be derived from the canonical schema source
rather than edited manually. The script performs marker-bounded updates
so documentation remains synchronized while preserving surrounding prose.

Architectural role
------------------
This module belongs to the developer tooling layer and provides a
documentation-maintenance utility for schema-related project artifacts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[1]
CONSTANTS = ROOT / "src/fontshow/core/global_constants.py"

FIELD_REFERENCE_START = "<!-- FIELD_REFERENCE_START -->"
FIELD_REFERENCE_END = "<!-- FIELD_REFERENCE_END -->"
SCHEMA_JSON_START = "<!-- SCHEMA_JSON_START -->"
SCHEMA_JSON_END = "<!-- SCHEMA_JSON_END -->"


class FieldReferenceRow(TypedDict):
    """
    One flattened schema field rendered in the generated reference table.

    Parameters
    ----------
    path : str
        Deterministic field path using dot notation and ``[]`` for arrays.
    type : str
        Human-readable JSON Schema type summary.
    required : str
        ``yes`` when the field is required by its parent object, else ``no``.
    description : str
        Description copied from the schema or a deterministic placeholder.
    """

    path: str
    type: str
    required: str
    description: str


def _read_schema_version(constants_path: Path = CONSTANTS) -> str:
    """
    Read the active schema version from the core constants module.

    Parameters
    ----------
    constants_path : pathlib.Path, optional
        Path to the constants module containing ``SCHEMA_VERSION``.

    Returns
    -------
    str
        Active schema version string, for example ``"1.5"``.

    Raises
    ------
    SystemExit
        Raised when the version constant cannot be located.
    """
    constants_text = constants_path.read_text(encoding="utf-8")
    match = re.search(r'SCHEMA_VERSION = "([^"]+)"', constants_text)
    if match is None:
        msg = "ERROR: could not determine SCHEMA_VERSION from core constants"
        raise SystemExit(msg)
    return match.group(1)


def _schema_paths(
    root: Path = ROOT, schema_version: str | None = None
) -> tuple[Path, Path]:
    """
    Resolve the active schema JSON file and documentation path.

    Parameters
    ----------
    root : pathlib.Path, optional
        Repository root used to resolve relative paths.
    schema_version : str | None, optional
        Explicit schema version. When ``None``, read from core constants.

    Returns
    -------
    tuple[pathlib.Path, pathlib.Path]
        Canonical schema JSON path and matching documentation path.
    """
    version = schema_version or _read_schema_version()
    version_token = version.replace(".", "_")
    schema_path = root / f"src/fontshow/schema/inventory_v{version_token}.json"
    doc_path = root / f"docs/schema/inventory_v{version_token}.md"
    return schema_path, doc_path


def _resolve_ref(schema: dict[str, object], ref: str) -> dict[str, object]:
    """
    Resolve one local JSON Schema reference against the loaded schema.

    Parameters
    ----------
    schema : dict[str, object]
        Root JSON schema document.
    ref : str
        Local reference string such as ``"#/$defs/font_entry"``.

    Returns
    -------
    dict[str, object]
        Resolved schema node.

    Raises
    ------
    TypeError
        Raised when the resolved reference target is not a schema object.
    ValueError
        Raised when the reference is unsupported or cannot be resolved.
    """
    if not ref.startswith("#/"):
        msg = f"Unsupported schema reference: {ref}"
        raise ValueError(msg)

    target: object = schema
    for token in ref.removeprefix("#/").split("/"):
        if not isinstance(target, dict) or token not in target:
            msg = f"Unresolvable schema reference: {ref}"
            raise ValueError(msg)
        target = target[token]

    if not isinstance(target, dict):
        msg = f"Schema reference does not resolve to an object: {ref}"
        raise TypeError(msg)
    return target


def _merge_schema_node(
    schema: dict[str, object], node: dict[str, object]
) -> dict[str, object]:
    """
    Merge one schema node with its referenced target when present.

    Parameters
    ----------
    schema : dict[str, object]
        Root JSON schema document.
    node : dict[str, object]
        Schema node to normalize.

    Returns
    -------
    dict[str, object]
        Node with local ``$ref`` content merged in and local keys taking
        precedence over referenced keys.
    """
    ref = node.get("$ref")
    if not isinstance(ref, str):
        return dict(node)

    resolved = _resolve_ref(schema, ref)
    merged = dict(resolved)
    for key, value in node.items():
        if key == "$ref":
            continue
        merged[key] = value
    return merged


def _render_type(node: dict[str, object]) -> str:
    """
    Render a deterministic human-readable type description for one node.

    Parameters
    ----------
    node : dict[str, object]
        Normalized schema node.

    Returns
    -------
    str
        Type label derived from ``type`` and related schema metadata.
    """
    type_value = node.get("type")
    if isinstance(type_value, list):
        parts = [str(item) for item in type_value]
        return " | ".join(parts)
    if isinstance(type_value, str):
        if type_value == "array":
            items = node.get("items")
            if isinstance(items, dict):
                item_type = _render_type(items)
                return f"array[{item_type}]"
        return type_value
    if "enum" in node:
        return "enum"
    if "$ref" in node:
        return "object"
    return "unknown"


def _collect_field_rows(
    schema: dict[str, object],
    node: dict[str, object],
    *,
    base_path: str = "",
    required: bool = False,
) -> list[FieldReferenceRow]:
    """
    Flatten schema object properties into deterministic field-reference rows.

    Parameters
    ----------
    schema : dict[str, object]
        Root JSON schema document.
    node : dict[str, object]
        Schema node whose fields should be flattened.
    base_path : str, optional
        Dot-path prefix for the current node.
    required : bool, optional
        Whether the current node is required by its parent object.

    Returns
    -------
    list[FieldReferenceRow]
        Flattened rows in stable schema order.
    """
    merged = _merge_schema_node(schema, node)
    path_value = base_path or "$"
    description = str(merged.get("description") or "No description.")
    rows: list[FieldReferenceRow] = [
        {
            "path": path_value,
            "type": _render_type(merged),
            "required": "yes" if required else "no",
            "description": description,
        }
    ]

    properties = merged.get("properties")
    required_fields = merged.get("required")
    required_set = (
        {str(item) for item in required_fields if isinstance(item, str)}
        if isinstance(required_fields, list)
        else set()
    )
    if isinstance(properties, dict):
        for property_name, property_schema in properties.items():
            if not isinstance(property_schema, dict):
                continue
            child_path = (
                property_name if not base_path else f"{base_path}.{property_name}"
            )
            rows.extend(
                _collect_field_rows(
                    schema,
                    property_schema,
                    base_path=child_path,
                    required=property_name in required_set,
                )
            )

    items = merged.get("items")
    if isinstance(items, dict):
        child_path = f"{base_path}[]" if base_path else "$[]"
        rows.extend(
            _collect_field_rows(
                schema,
                items,
                base_path=child_path,
                required=False,
            )
        )

    return rows


def generate_field_reference_markdown(schema: dict[str, object]) -> str:
    """
    Generate the markdown field-reference section from the active schema.

    Parameters
    ----------
    schema : dict[str, object]
        Loaded JSON schema document.

    Returns
    -------
    str
        Marker-bounded markdown fragment containing the generated table.
    """
    rows = _collect_field_rows(schema, schema)
    table_lines = [
        "## Field Reference",
        "",
        "| Field | Type | Required | Description |",
        "| ------ | ------ | ---------- | ------------- |",
    ]
    for row in rows:
        table_lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row['path']}`",
                    row["type"].replace("|", "\\|"),
                    row["required"],
                    row["description"].replace("\n", " "),
                )
            )
            + " |"
        )
    body = "\n".join(table_lines)
    return f"{FIELD_REFERENCE_START}\n\n{body}\n\n{FIELD_REFERENCE_END}"


def generate_schema_json_markdown(schema: dict[str, object]) -> str:
    """
    Generate the marker-bounded pretty-printed JSON schema block.

    Parameters
    ----------
    schema : dict[str, object]
        Loaded JSON schema document.

    Returns
    -------
    str
        Marker-bounded markdown fragment containing the schema JSON.
    """
    pretty = json.dumps(schema, indent=2, ensure_ascii=False)
    return f"{SCHEMA_JSON_START}\n\n```json\n{pretty}\n```\n\n{SCHEMA_JSON_END}"


def _replace_marker_block(text: str, start: str, end: str, replacement: str) -> str:
    """
    Replace one marker-bounded documentation block.

    Parameters
    ----------
    text : str
        Existing document content.
    start : str
        Start marker string.
    end : str
        End marker string.
    replacement : str
        Full replacement block including markers.

    Returns
    -------
    str
        Document content with the marker-bounded block replaced.

    Raises
    ------
    SystemExit
        Raised when the marker pair is missing or malformed.
    """
    if start not in text or end not in text:
        msg = f"ERROR: documentation markers not found or malformed: {start} ... {end}"
        raise SystemExit(msg)

    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.DOTALL)
    return pattern.sub(lambda _match: replacement, text)


def update_schema_doc(doc_path: Path, schema: dict[str, object]) -> bool:
    """
    Update the active schema documentation file in place.

    Parameters
    ----------
    doc_path : pathlib.Path
        Markdown document to update.
    schema : dict[str, object]
        Loaded JSON schema document.

    Returns
    -------
    bool
        ``True`` when the document changed, otherwise ``False``.
    """
    original_text = doc_path.read_text(encoding="utf-8")
    text_with_field_reference = _replace_marker_block(
        original_text,
        FIELD_REFERENCE_START,
        FIELD_REFERENCE_END,
        generate_field_reference_markdown(schema),
    )
    new_text = _replace_marker_block(
        text_with_field_reference,
        SCHEMA_JSON_START,
        SCHEMA_JSON_END,
        generate_schema_json_markdown(schema),
    )
    if new_text == original_text:
        return False
    doc_path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    """
    Synchronize the active schema markdown document with the runtime schema.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Process exit code. Returns ``0`` on success.
    """
    schema_path, doc_path = _schema_paths()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    changed = update_schema_doc(doc_path, schema)
    if changed:
        print(f"Updated {doc_path.relative_to(ROOT)}")
    else:
        print("Schema documentation already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
