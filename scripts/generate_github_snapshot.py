#!python
"""
Generate paginated GitHub planning snapshots.

This maintenance script writes repository-local ``issues.json`` and
``milestones.json`` snapshots used by planning workflows. It uses the GitHub
CLI GraphQL API and follows every relevant connection until pagination is
complete.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sops_exec import SopsExecutionError, run_with_github_secret

OWNER = "marco0560"
REPOSITORY = "Fontshow"
ISSUES_PAGE_SIZE = 100
MILESTONES_PAGE_SIZE = 20
NESTED_ISSUES_PAGE_SIZE = 100


class SnapshotError(RuntimeError):
    """
    Represent a controlled snapshot generation failure.

    Parameters
    ----------
    message : str
        Human-readable failure reason.

    Returns
    -------
    None
    """


def _snapshot_error(message: str) -> SnapshotError:
    """
    Build a snapshot error with a caller-provided message.

    Parameters
    ----------
    message : str
        Human-readable failure reason.

    Returns
    -------
    SnapshotError
        Controlled snapshot generation exception.
    """
    return SnapshotError(message)


def _graphql_string(value: str) -> str:
    """
    Render a Python string as a GraphQL string literal.

    Parameters
    ----------
    value : str
        Value to encode.

    Returns
    -------
    str
        JSON-compatible string literal suitable for GraphQL query text.
    """
    return json.dumps(value)


def _after_clause(cursor: str | None) -> str:
    """
    Render the GraphQL ``after`` argument for a connection.

    Parameters
    ----------
    cursor : str or None
        Cursor returned by the previous connection page. ``None`` renders as
        ``null`` for the first page.

    Returns
    -------
    str
        GraphQL literal for the ``after`` argument.
    """
    if cursor is None:
        return "null"
    return _graphql_string(cursor)


def _run_graphql(query: str) -> dict[str, object]:
    """
    Execute a GitHub GraphQL query and return the decoded JSON response.

    Parameters
    ----------
    query : str
        Complete GraphQL query document.

    Returns
    -------
    dict[str, object]
        Decoded JSON payload returned by ``gh api graphql``.

    Raises
    ------
    SnapshotError
        Raised when the GitHub CLI command fails or returns malformed JSON.
    """
    try:
        completed = run_with_github_secret(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            capture_output=True,
            text=True,
        )
    except (SopsExecutionError, subprocess.CalledProcessError) as exc:
        stderr = getattr(exc, "stderr", "") or ""
        stderr = stderr.strip()
        detail = f": {stderr}" if stderr else ""
        message = f"GitHub GraphQL query failed{detail}"
        raise _snapshot_error(message) from exc

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        message = "GitHub GraphQL query returned invalid JSON"
        raise _snapshot_error(message) from exc

    if not isinstance(payload, dict):
        message = "GitHub GraphQL query returned non-object JSON"
        raise _snapshot_error(message)

    return cast("dict[str, object]", payload)


def _page_info(connection: dict[str, object]) -> dict[str, object]:
    """
    Return a connection's ``pageInfo`` object.

    Parameters
    ----------
    connection : dict[str, object]
        GraphQL connection object.

    Returns
    -------
    dict[str, object]
        The connection ``pageInfo`` object.

    Raises
    ------
    SnapshotError
        Raised when the connection lacks a valid ``pageInfo`` object.
    """
    page_info = connection.get("pageInfo")
    if not isinstance(page_info, dict):
        message = "GraphQL connection is missing pageInfo"
        raise _snapshot_error(message)
    return cast("dict[str, object]", page_info)


def _nodes(connection: dict[str, object]) -> list[dict[str, object]]:
    """
    Return a connection's node list.

    Parameters
    ----------
    connection : dict[str, object]
        GraphQL connection object.

    Returns
    -------
    list[dict[str, object]]
        GraphQL node objects.

    Raises
    ------
    SnapshotError
        Raised when the connection lacks a valid ``nodes`` list.
    """
    nodes = connection.get("nodes")
    if not isinstance(nodes, list) or not all(isinstance(node, dict) for node in nodes):
        message = "GraphQL connection is missing nodes"
        raise _snapshot_error(message)
    return cast("list[dict[str, object]]", nodes)


def _repository_connection(payload: dict[str, object], name: str) -> dict[str, object]:
    """
    Return a named repository connection from a GraphQL response.

    Parameters
    ----------
    payload : dict[str, object]
        Decoded GitHub GraphQL response.
    name : str
        Repository connection field name.

    Returns
    -------
    dict[str, object]
        Connection object.

    Raises
    ------
    SnapshotError
        Raised when the expected response path is missing.
    """
    data = payload.get("data")
    if not isinstance(data, dict):
        message = "GraphQL response is missing data"
        raise _snapshot_error(message)

    repository = data.get("repository")
    if not isinstance(repository, dict):
        message = "GraphQL response is missing repository"
        raise _snapshot_error(message)

    connection = repository.get(name)
    if not isinstance(connection, dict):
        message = f"GraphQL response is missing repository.{name}"
        raise _snapshot_error(message)

    return cast("dict[str, object]", connection)


def _issue_page_query(cursor: str | None) -> str:
    """
    Build the open-issue page query.

    Parameters
    ----------
    cursor : str or None
        Cursor for the next issue page.

    Returns
    -------
    str
        GraphQL query text.
    """
    return f"""
query {{
  repository(owner: "{OWNER}", name: "{REPOSITORY}") {{
    issues(
      first: {ISSUES_PAGE_SIZE}
      after: {_after_clause(cursor)}
      states: OPEN
      orderBy: {{field: CREATED_AT, direction: ASC}}
    ) {{
      totalCount
      pageInfo {{ hasNextPage endCursor }}
      nodes {{
        number
        title
        body
        url
        state
        createdAt
        updatedAt
        author {{ login }}
        assignees(first: 20) {{ nodes {{ login }} }}
        labels(first: 20) {{ nodes {{ name }} }}
        milestone {{ number title }}
        comments {{ totalCount }}
      }}
    }}
  }}
}}
"""


def _milestone_page_query(cursor: str | None) -> str:
    """
    Build the open-milestone page query.

    Parameters
    ----------
    cursor : str or None
        Cursor for the next milestone page.

    Returns
    -------
    str
        GraphQL query text.
    """
    return f"""
query {{
  repository(owner: "{OWNER}", name: "{REPOSITORY}") {{
    milestones(
      first: {MILESTONES_PAGE_SIZE}
      after: {_after_clause(cursor)}
      states: OPEN
      orderBy: {{field: DUE_DATE, direction: ASC}}
    ) {{
      totalCount
      pageInfo {{ hasNextPage endCursor }}
      nodes {{
        number
        title
        description
        dueOn
        progressPercentage
        issues(first: {NESTED_ISSUES_PAGE_SIZE}) {{
          totalCount
          pageInfo {{ hasNextPage endCursor }}
          nodes {{
            number
            title
            url
            state
            createdAt
            updatedAt
            labels(first: 20) {{ nodes {{ name }} }}
          }}
        }}
      }}
    }}
  }}
}}
"""


def _milestone_issue_page_query(*, milestone_number: int, cursor: str | None) -> str:
    """
    Build a nested milestone issue page query.

    Parameters
    ----------
    milestone_number : int
        GitHub milestone number.
    cursor : str or None
        Cursor for the next nested issue page.

    Returns
    -------
    str
        GraphQL query text.
    """
    return f"""
query {{
  repository(owner: "{OWNER}", name: "{REPOSITORY}") {{
    milestone(number: {milestone_number}) {{
      issues(first: {NESTED_ISSUES_PAGE_SIZE}, after: {_after_clause(cursor)}) {{
        totalCount
        pageInfo {{ hasNextPage endCursor }}
        nodes {{
          number
          title
          url
          state
          createdAt
          updatedAt
          labels(first: 20) {{ nodes {{ name }} }}
        }}
      }}
    }}
  }}
}}
"""


def _build_connection(first_page: dict[str, object]) -> dict[str, object]:
    """
    Copy a GraphQL connection into the snapshot shape.

    Parameters
    ----------
    first_page : dict[str, object]
        First page of a GraphQL connection.

    Returns
    -------
    dict[str, object]
        Snapshot connection object with a mutable node list.
    """
    page_info = dict(_page_info(first_page))
    return {
        "totalCount": first_page.get("totalCount", 0),
        "pageInfo": page_info,
        "nodes": list(_nodes(first_page)),
    }


def build_issues_snapshot() -> dict[str, object]:
    """
    Build a complete open-issues snapshot.

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, object]
        Snapshot payload using the ``data.repository.issues`` schema.

    Raises
    ------
    SnapshotError
        Raised when GraphQL pagination or response shape is incomplete.
    """
    cursor: str | None = None
    snapshot_connection: dict[str, object] | None = None

    while True:
        payload = _run_graphql(_issue_page_query(cursor))
        page = _repository_connection(payload, "issues")

        if snapshot_connection is None:
            snapshot_connection = _build_connection(page)
        else:
            cast("list[dict[str, object]]", snapshot_connection["nodes"]).extend(
                _nodes(page)
            )
            snapshot_connection["pageInfo"] = dict(_page_info(page))

        page_info = _page_info(page)
        if not page_info.get("hasNextPage"):
            break
        cursor_value = page_info.get("endCursor")
        if not isinstance(cursor_value, str) or not cursor_value:
            message = "Issue pagination did not provide endCursor"
            raise _snapshot_error(message)
        cursor = cursor_value

    if snapshot_connection is None:
        message = "Issue snapshot generation produced no pages"
        raise _snapshot_error(message)

    return {"data": {"repository": {"issues": snapshot_connection}}}


def _complete_milestone_issues(milestone: dict[str, object]) -> None:
    """
    Complete the nested issue connection for one milestone in place.

    Parameters
    ----------
    milestone : dict[str, object]
        Milestone node containing an ``issues`` connection.

    Returns
    -------
    None

    Raises
    ------
    SnapshotError
        Raised when nested pagination cannot continue deterministically.
    """
    milestone_number = milestone.get("number")
    if not isinstance(milestone_number, int):
        message = "Milestone node is missing numeric number"
        raise _snapshot_error(message)

    issues = milestone.get("issues")
    if not isinstance(issues, dict):
        message = "Milestone node is missing issues connection"
        raise _snapshot_error(message)

    issue_connection = cast("dict[str, object]", issues)
    page_info = _page_info(issue_connection)

    while page_info.get("hasNextPage"):
        cursor_value = page_info.get("endCursor")
        if not isinstance(cursor_value, str) or not cursor_value:
            message = "Nested milestone issue pagination missing endCursor"
            raise _snapshot_error(message)

        payload = _run_graphql(
            _milestone_issue_page_query(
                milestone_number=milestone_number,
                cursor=cursor_value,
            )
        )
        data = payload.get("data")
        if not isinstance(data, dict):
            message = "GraphQL response is missing data"
            raise _snapshot_error(message)
        repository = data.get("repository")
        if not isinstance(repository, dict):
            message = "GraphQL response is missing repository"
            raise _snapshot_error(message)
        milestone_payload = repository.get("milestone")
        if not isinstance(milestone_payload, dict):
            message = "GraphQL response is missing repository.milestone"
            raise _snapshot_error(message)
        page = milestone_payload.get("issues")
        if not isinstance(page, dict):
            message = "GraphQL response is missing milestone issues"
            raise _snapshot_error(message)

        cast("list[dict[str, object]]", issue_connection["nodes"]).extend(_nodes(page))
        issue_connection["pageInfo"] = dict(_page_info(page))
        page_info = _page_info(issue_connection)


def build_milestones_snapshot() -> dict[str, object]:
    """
    Build a complete open-milestones snapshot.

    Parameters
    ----------
    None

    Returns
    -------
    dict[str, object]
        Snapshot payload using the ``data.repository.milestones`` schema.

    Raises
    ------
    SnapshotError
        Raised when GraphQL pagination or response shape is incomplete.
    """
    cursor: str | None = None
    snapshot_connection: dict[str, object] | None = None

    while True:
        payload = _run_graphql(_milestone_page_query(cursor))
        page = _repository_connection(payload, "milestones")

        if snapshot_connection is None:
            snapshot_connection = _build_connection(page)
        else:
            cast("list[dict[str, object]]", snapshot_connection["nodes"]).extend(
                _nodes(page)
            )
            snapshot_connection["pageInfo"] = dict(_page_info(page))

        page_info = _page_info(page)
        if not page_info.get("hasNextPage"):
            break
        cursor_value = page_info.get("endCursor")
        if not isinstance(cursor_value, str) or not cursor_value:
            message = "Milestone pagination did not provide endCursor"
            raise _snapshot_error(message)
        cursor = cursor_value

    if snapshot_connection is None:
        message = "Milestone snapshot generation produced no pages"
        raise _snapshot_error(message)

    for milestone in cast("list[dict[str, object]]", snapshot_connection["nodes"]):
        _complete_milestone_issues(milestone)

    return {"data": {"repository": {"milestones": snapshot_connection}}}


def write_snapshot(payload: dict[str, object], output: Path) -> None:
    """
    Atomically write a snapshot JSON payload.

    Parameters
    ----------
    payload : dict[str, object]
        Snapshot payload to serialize.
    output : pathlib.Path
        Destination file path.

    Returns
    -------
    None
    """
    output_parent = output.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output_parent,
        delete=False,
    ) as handle:
        tmp_path = Path(handle.name)
        handle.write(rendered)

    tmp_path.replace(output)


def build_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.ArgumentParser
        Parser for the snapshot generator CLI.
    """
    parser = argparse.ArgumentParser(
        description="Generate paginated GitHub planning snapshots."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    issues = subparsers.add_parser("issues", help="Generate issues.json")
    issues.add_argument(
        "--output",
        type=Path,
        default=Path("issues.json"),
        help="Output path (default: issues.json)",
    )

    milestones = subparsers.add_parser("milestones", help="Generate milestones.json")
    milestones.add_argument(
        "--output",
        type=Path,
        default=Path("milestones.json"),
        help="Output path (default: milestones.json)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Generate the requested GitHub planning snapshot.

    Parameters
    ----------
    argv : list[str] or None, optional
        Command-line arguments. If ``None``, arguments are read from
        ``sys.argv``.

    Returns
    -------
    int
        ``0`` on success, ``1`` for controlled generation failures.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "issues":
            payload = build_issues_snapshot()
        elif args.command == "milestones":
            payload = build_milestones_snapshot()
        else:
            parser.error(f"unsupported command: {args.command}")
        write_snapshot(payload, args.output)
    except SnapshotError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
