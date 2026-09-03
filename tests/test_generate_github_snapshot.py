"""Verify the paginated GitHub planning snapshot generator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "generate_github_snapshot.py"
)
_SPEC = importlib.util.spec_from_file_location("generate_github_snapshot", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
generate_github_snapshot = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = generate_github_snapshot
_SPEC.loader.exec_module(generate_github_snapshot)


def _issues_payload(
    *,
    numbers: list[int],
    has_next_page: bool,
    end_cursor: str | None,
    total_count: int,
) -> dict[str, object]:
    """
    Build a minimal GitHub issues GraphQL payload.

    Parameters
    ----------
    numbers : list[int]
        Issue numbers to include in the page.
    has_next_page : bool
        Pagination flag for the page.
    end_cursor : str or None
        Cursor to expose in ``pageInfo``.
    total_count : int
        Total open issue count reported by GitHub.

    Returns
    -------
    dict[str, object]
        GraphQL response payload.
    """
    return {
        "data": {
            "repository": {
                "issues": {
                    "totalCount": total_count,
                    "pageInfo": {
                        "hasNextPage": has_next_page,
                        "endCursor": end_cursor,
                    },
                    "nodes": [
                        {
                            "number": number,
                            "title": f"Issue {number}",
                            "body": "",
                            "url": f"https://example.test/issues/{number}",
                            "state": "OPEN",
                            "createdAt": "2026-01-01T00:00:00Z",
                            "updatedAt": "2026-01-01T00:00:00Z",
                            "author": {"login": "author"},
                            "assignees": {"nodes": []},
                            "labels": {"nodes": []},
                            "milestone": None,
                            "comments": {"totalCount": 0},
                        }
                        for number in numbers
                    ],
                }
            }
        }
    }


def _milestones_payload(
    *,
    numbers: list[int],
    has_next_page: bool,
    end_cursor: str | None,
    nested_has_next_page: bool = False,
) -> dict[str, object]:
    """
    Build a minimal GitHub milestones GraphQL payload.

    Parameters
    ----------
    numbers : list[int]
        Milestone numbers to include in the page.
    has_next_page : bool
        Pagination flag for the milestone page.
    end_cursor : str or None
        Cursor to expose in milestone ``pageInfo``.
    nested_has_next_page : bool, optional
        Whether the first milestone's nested issues require another page.

    Returns
    -------
    dict[str, object]
        GraphQL response payload.
    """
    return {
        "data": {
            "repository": {
                "milestones": {
                    "totalCount": 2,
                    "pageInfo": {
                        "hasNextPage": has_next_page,
                        "endCursor": end_cursor,
                    },
                    "nodes": [
                        {
                            "number": number,
                            "title": f"Milestone {number}",
                            "description": "",
                            "dueOn": None,
                            "progressPercentage": 0,
                            "issues": {
                                "totalCount": 2 if nested_has_next_page else 1,
                                "pageInfo": {
                                    "hasNextPage": nested_has_next_page,
                                    "endCursor": f"nested-{number}",
                                },
                                "nodes": [
                                    {
                                        "number": number * 10,
                                        "title": f"Nested {number}",
                                        "url": f"https://example.test/issues/{number * 10}",
                                        "state": "OPEN",
                                        "createdAt": "2026-01-01T00:00:00Z",
                                        "updatedAt": "2026-01-01T00:00:00Z",
                                        "labels": {"nodes": []},
                                    }
                                ],
                            },
                        }
                        for number in numbers
                    ],
                }
            }
        }
    }


def _nested_issue_payload(milestone_number: int) -> dict[str, object]:
    """
    Build a nested milestone issue page payload.

    Parameters
    ----------
    milestone_number : int
        Milestone number used to derive the issue number.

    Returns
    -------
    dict[str, object]
        GraphQL response payload.
    """
    return {
        "data": {
            "repository": {
                "milestone": {
                    "issues": {
                        "totalCount": 2,
                        "pageInfo": {
                            "hasNextPage": False,
                            "endCursor": f"nested-final-{milestone_number}",
                        },
                        "nodes": [
                            {
                                "number": milestone_number * 10 + 1,
                                "title": f"Nested more {milestone_number}",
                                "url": (
                                    "https://example.test/issues/"
                                    f"{milestone_number * 10 + 1}"
                                ),
                                "state": "OPEN",
                                "createdAt": "2026-01-01T00:00:00Z",
                                "updatedAt": "2026-01-01T00:00:00Z",
                                "labels": {"nodes": []},
                            }
                        ],
                    }
                }
            }
        }
    }


def test_build_issues_snapshot_follows_all_issue_pages(monkeypatch) -> None:
    """
    Ensure open issue pagination is followed until complete.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the GitHub GraphQL subprocess layer.

    Returns
    -------
    None
    """
    pages = [
        _issues_payload(
            numbers=[1, 2],
            has_next_page=True,
            end_cursor="issue-cursor",
            total_count=3,
        ),
        _issues_payload(
            numbers=[3],
            has_next_page=False,
            end_cursor="issue-final",
            total_count=3,
        ),
    ]
    seen_queries: list[str] = []

    def _fake_run_graphql(query: str) -> dict[str, object]:
        seen_queries.append(query)
        return pages.pop(0)

    monkeypatch.setattr(generate_github_snapshot, "_run_graphql", _fake_run_graphql)

    snapshot = generate_github_snapshot.build_issues_snapshot()

    issues = snapshot["data"]["repository"]["issues"]
    assert [node["number"] for node in issues["nodes"]] == [1, 2, 3]
    assert issues["totalCount"] == 3
    assert issues["pageInfo"]["hasNextPage"] is False
    assert "after: null" in seen_queries[0]
    assert 'after: "issue-cursor"' in seen_queries[1]


def test_build_milestones_snapshot_follows_milestone_and_nested_pages(
    monkeypatch,
) -> None:
    """
    Ensure milestone and nested milestone issue pagination are followed.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the GitHub GraphQL subprocess layer.

    Returns
    -------
    None
    """
    pages = [
        _milestones_payload(
            numbers=[1],
            has_next_page=True,
            end_cursor="milestone-cursor",
            nested_has_next_page=True,
        ),
        _milestones_payload(
            numbers=[2],
            has_next_page=False,
            end_cursor="milestone-final",
        ),
        _nested_issue_payload(1),
    ]
    seen_queries: list[str] = []

    def _fake_run_graphql(query: str) -> dict[str, object]:
        seen_queries.append(query)
        return pages.pop(0)

    monkeypatch.setattr(generate_github_snapshot, "_run_graphql", _fake_run_graphql)

    snapshot = generate_github_snapshot.build_milestones_snapshot()

    milestones = snapshot["data"]["repository"]["milestones"]
    assert [node["number"] for node in milestones["nodes"]] == [1, 2]
    assert milestones["pageInfo"]["hasNextPage"] is False
    first_nested = milestones["nodes"][0]["issues"]
    assert [node["number"] for node in first_nested["nodes"]] == [10, 11]
    assert first_nested["pageInfo"]["hasNextPage"] is False
    assert "milestones(" in seen_queries[0]
    assert 'after: "milestone-cursor"' in seen_queries[1]
    assert "milestone(number: 1)" in seen_queries[2]
    assert 'after: "nested-1"' in seen_queries[2]


def test_main_writes_requested_snapshot_output(tmp_path, monkeypatch) -> None:
    """
    Ensure ``--output`` only controls the destination path.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory for the output file.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace snapshot construction.

    Returns
    -------
    None
    """
    output = tmp_path / "custom.json"
    payload = {"data": {"repository": {"issues": {"nodes": []}}}}
    monkeypatch.setattr(
        generate_github_snapshot, "build_issues_snapshot", lambda: payload
    )

    result = generate_github_snapshot.main(["issues", "--output", str(output)])

    assert result == 0
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert not (tmp_path / "issues.json").exists()


def test_main_reports_github_cli_failure(capsys, monkeypatch) -> None:
    """
    Ensure controlled GitHub CLI failures return a non-zero exit code.

    Parameters
    ----------
    capsys : pytest.CaptureFixture[str]
        Fixture used to inspect stderr.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the subprocess layer.

    Returns
    -------
    None
    """

    def _fake_run_with_github_secret(
        *_args: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["gh"],
            stderr="authentication required",
        )

    monkeypatch.setattr(
        generate_github_snapshot,
        "run_with_github_secret",
        _fake_run_with_github_secret,
    )

    result = generate_github_snapshot.main(["issues"])

    assert result == 1
    assert "authentication required" in capsys.readouterr().err
