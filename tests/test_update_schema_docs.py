"""Verify schema documentation generation and live-schema doc layout."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import yaml

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_schema_docs.py"
_SPEC = importlib.util.spec_from_file_location("update_schema_docs", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
update_schema_docs = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = update_schema_docs
_SPEC.loader.exec_module(update_schema_docs)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_generate_field_reference_markdown_flattens_schema_deterministically() -> None:
    """
    Verify field-reference generation flattens nested object and array paths.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    schema = {
        "type": "object",
        "description": "Root schema.",
        "required": ["metadata", "fonts"],
        "properties": {
            "metadata": {
                "type": "object",
                "description": "Metadata object.",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "description": "Schema version identifier.",
                    }
                },
            },
            "fonts": {
                "type": "array",
                "description": "Font entries.",
                "items": {
                    "$ref": "#/$defs/font_entry",
                },
            },
        },
        "$defs": {
            "font_entry": {
                "type": "object",
                "description": "Font entry.",
                "required": ["path"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Font file path.",
                    }
                },
            }
        },
    }

    markdown = update_schema_docs.generate_field_reference_markdown(schema)

    assert "## Field Reference" in markdown
    assert "| `metadata` | object | yes | Metadata object. |" in markdown
    assert (
        "| `metadata.schema_version` | string | yes | Schema version identifier. |"
        in markdown
    )
    assert "| `fonts` | array[object] | yes | Font entries. |" in markdown
    assert "| `fonts[]` | object | no | Font entry. |" in markdown
    assert "| `fonts[].path` | string | yes | Font file path. |" in markdown


def test_update_schema_doc_replaces_both_generated_blocks(tmp_path: Path) -> None:
    """
    Verify schema doc updates rewrite field-reference and JSON marker blocks.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage the markdown document.

    Returns
    -------
    None
    """
    doc_path = tmp_path / "inventory.md"
    doc_path.write_text(
        "\n".join(
            [
                "# Title",
                update_schema_docs.FIELD_REFERENCE_START,
                "OLD FIELD CONTENT",
                update_schema_docs.FIELD_REFERENCE_END,
                update_schema_docs.SCHEMA_JSON_START,
                "OLD JSON CONTENT",
                update_schema_docs.SCHEMA_JSON_END,
            ]
        ),
        encoding="utf-8",
    )

    schema = {
        "type": "object",
        "description": "Root schema.",
        "properties": {
            "metadata": {
                "type": "object",
                "description": "Metadata object.",
                "properties": {},
            }
        },
    }

    changed = update_schema_docs.update_schema_doc(doc_path, schema)
    rendered = doc_path.read_text(encoding="utf-8")

    assert changed is True
    assert "OLD FIELD CONTENT" not in rendered
    assert "OLD JSON CONTENT" not in rendered
    assert "## Field Reference" in rendered
    assert '"description": "Root schema."' in rendered


def test_live_schema_docs_only_expose_current_pages_in_docs_and_nav() -> None:
    """
    Verify docs/schema and MkDocs navigation expose only current schema pages.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    schema_docs = sorted(
        path.name for path in (REPO_ROOT / "docs" / "schema").glob("*.md")
    )
    assert schema_docs == [
        "index.md",
        "inventory_v1_5.md",
        "language-normalization.md",
    ]

    mkdocs_text = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "schema/inventory_v1_5.md" in mkdocs_text
    assert "schema/inventory_v1_3.md" not in mkdocs_text
    assert "schema/inventory_v1_4.md" not in mkdocs_text

    docs_index_text = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    assert "schema/index.md" in docs_index_text
    assert "schema/inventory_v1_5.md" in docs_index_text
    assert "schema/language-normalization.md" in docs_index_text


def test_live_schema_doc_matches_generated_output() -> None:
    """
    Verify the checked-in live schema doc matches the generator output.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    schema_path, doc_path = update_schema_docs._schema_paths()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    doc_text = doc_path.read_text(encoding="utf-8")

    assert update_schema_docs.generate_field_reference_markdown(schema) in doc_text
    assert update_schema_docs.generate_schema_json_markdown(schema) in doc_text


def test_mkdocs_navigation_covers_all_live_markdown_docs() -> None:
    """
    Verify every live markdown page under docs is reachable from MkDocs nav.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """

    class _MkDocsLoader(yaml.SafeLoader):
        """
        YAML loader that tolerates MkDocs extension-specific Python tags.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

    def _construct_unknown(
        loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node
    ) -> str:
        """
        Convert unsupported tagged scalar values into plain strings.

        Parameters
        ----------
        loader : yaml.SafeLoader
            Active YAML loader instance.
        tag_suffix : str
            Unknown tag suffix accepted for interface compatibility.
        node : yaml.Node
            YAML node being constructed.

        Returns
        -------
        str
            Scalar node value preserved as plain text.
        """
        _ = loader, tag_suffix
        if isinstance(node, yaml.ScalarNode):
            return node.value
        return ""

    _MkDocsLoader.add_multi_constructor("", _construct_unknown)

    mkdocs_config = yaml.load(
        (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"),
        Loader=_MkDocsLoader,
    )

    def _flatten_nav(items: object) -> set[str]:
        paths: set[str] = set()
        if isinstance(items, list):
            for item in items:
                paths |= _flatten_nav(item)
            return paths
        if isinstance(items, dict):
            for value in items.values():
                if isinstance(value, str) and value.endswith(".md"):
                    paths.add(value)
                else:
                    paths |= _flatten_nav(value)
        return paths

    nav_paths = _flatten_nav(mkdocs_config["nav"])
    live_docs = {
        path.relative_to(REPO_ROOT / "docs").as_posix()
        for path in (REPO_ROOT / "docs").rglob("*.md")
        if "_archive" not in path.parts
    }

    assert live_docs == nav_paths
