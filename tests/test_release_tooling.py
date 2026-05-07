"""
Verify deterministic release tooling configuration.

This module protects the release workflow from drifting back to floating
Node dependency installation.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_JSON = REPO_ROOT / "package.json"
PACKAGE_LOCK = REPO_ROOT / "package-lock.json"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DOCS_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "docs.yml"
DOCS_PAGES_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "docs-pages.yml"

RELEASE_PACKAGES = {
    "@semantic-release/changelog",
    "@semantic-release/commit-analyzer",
    "@semantic-release/git",
    "@semantic-release/github",
    "@semantic-release/release-notes-generator",
    "conventional-changelog-conventionalcommits",
    "semantic-release",
}


def test_release_tool_versions_are_exactly_pinned() -> None:
    """
    Verify release tooling avoids floating semver ranges.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    package_data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    dev_dependencies = package_data["devDependencies"]

    for package_name in RELEASE_PACKAGES:
        version = dev_dependencies[package_name]
        assert version[0].isdigit(), package_name


def test_release_lockfile_pins_release_tooling() -> None:
    """
    Verify release tooling is represented in the npm lockfile.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    lock_data = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    root_package = lock_data["packages"][""]
    locked_dev_dependencies = root_package["devDependencies"]

    for package_name in RELEASE_PACKAGES:
        assert locked_dev_dependencies[package_name][0].isdigit(), package_name
        assert f"node_modules/{package_name}" in lock_data["packages"]


def test_release_workflow_installs_from_lockfile() -> None:
    """
    Verify release CI installs the committed Node dependency graph.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    workflow_text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "npm ci" in workflow_text
    assert "npm install \\" not in workflow_text


def test_documentation_workflows_delegate_to_single_reusable_workflow() -> None:
    """
    Verify documentation deployment logic is centralized in a single
    reusable workflow and uses uv-managed tooling.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    ci_workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    docs_workflow_text = DOCS_WORKFLOW.read_text(encoding="utf-8")
    docs_pages_workflow_text = DOCS_PAGES_WORKFLOW.read_text(encoding="utf-8")

    assert "uses: ./.github/workflows/docs-pages.yml" in ci_workflow_text
    assert "uses: ./.github/workflows/docs-pages.yml" in docs_workflow_text
    assert "pip install mkdocs" not in ci_workflow_text
    assert "pip install mkdocs" not in docs_workflow_text
    assert "pip install mkdocs" not in docs_pages_workflow_text
    assert "mkdocs build --strict" not in ci_workflow_text
    assert "mkdocs build --strict" not in docs_workflow_text
    assert "uv sync --frozen --extra dev --extra docs" in (docs_pages_workflow_text)
    assert "uv run mkdocs build --strict" in (docs_pages_workflow_text)
    assert docs_pages_workflow_text.count("uv run mkdocs build --strict") == 1
