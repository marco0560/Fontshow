"""
Generate deterministic end-to-end Fontshow test procedures.

This script generates or executes a deterministic, user-facing test
procedure for the Fontshow pipeline. The generated procedure exercises
all public pipeline stages and covers each user-facing option through a
bounded set of meaningful, artifact-driven scenarios rather than a
Cartesian product of flags.

The covered pipeline is:

- ``fontshow preflight``
- ``fontshow dump-fonts``
- ``fontshow parse-inventory``
- ``fontshow validate-inventory``
- ``fontshow create-catalog``
- ``lualatex`` compilation of generated catalog artifacts

Two operating modes are supported:

- ``interactive``: execute the procedure step by step and report rough
  completion percentage.
- ``script``: generate a Bash or PowerShell script containing the same
  deterministic procedure.

Artifact names are self-describing so the purpose of each generated file
is visible at a glance.

Parameters
----------
None
    Parameters are supplied via the command-line interface.

Returns
-------
int
    Process exit code. Returns ``0`` on success and non-zero on failure.

Raises
------
None
    All expected failures are converted into explicit exit codes and
    user-facing error messages.

Notes
-----
The procedure is state-driven. It follows real artifact transitions in
Fontshow's public pipeline instead of enumerating arbitrary option
combinations.

Examples
--------
Generate a Bash script::

    python scripts/generate_test_procedure.py \
        --mode script \
        --shell bash \
        --output scripts/run_fontshow_test_procedure.sh

Run the procedure interactively::

    python scripts/generate_test_procedure.py \
        --mode interactive \
        --artifact-dir procedure_artifacts
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class Step:
    """
    Represent one deterministic procedure step.

    Parameters
    ----------
    name : str
        Stable human-readable step name.
    description : str
        One-line explanation of the step intent.
    argv : tuple[str, ...]
        Command vector to execute.
    produces_artifact : bool, optional
        Whether the step produces a retained artifact.
    artifact_path : Path | None, optional
        Output artifact path associated with the step.
    """

    name: str
    description: str
    argv: tuple[str, ...]
    produces_artifact: bool = False
    artifact_path: Path | None = None


@dataclass(frozen=True)
class ProcedureContext:
    """
    Store normalized CLI configuration for procedure generation.

    Parameters
    ----------
    fontshow_command : str
        Command used to invoke the Fontshow CLI.
    artifact_dir : Path
        Directory receiving generated artifacts.
    shell : str
        Target shell name for script rendering.
    font_paths : tuple[Path, ...]
        Optional explicit font-discovery paths used to exercise
        ``dump-fonts --paths``.
    explicit_test_fonts : tuple[str, ...]
        Optional explicit font family names used to exercise
        ``create-catalog --test-font NAME``.
    python_command : str
        Command used to invoke Python for auxiliary file-copy steps.
    sample_languages : tuple[str, ...]
        Sample BCP-47 language selectors used in catalog filtering.
    sample_scripts : tuple[str, ...]
        Sample ISO 15924 script selectors used in catalog filtering.
    loadability_jobs : int
        Positive job count used when exercising loadability-related CLI
        options.
    catalog_limit : int
        Value used to exercise ``create-catalog --number``.
    """

    fontshow_command: str
    artifact_dir: Path
    shell: str
    font_paths: tuple[Path, ...]
    explicit_test_fonts: tuple[str, ...]
    python_command: str
    sample_languages: tuple[str, ...]
    sample_scripts: tuple[str, ...]
    loadability_jobs: int
    catalog_limit: int


def _positive_int(value: str) -> int:
    """
    Parse a strictly positive integer.

    Parameters
    ----------
    value : str
        Raw command-line value.

    Returns
    -------
    int
        Parsed positive integer.

    Raises
    ------
    argparse.ArgumentTypeError
        Raised when ``value`` is not a strictly positive integer.
    """
    try:
        parsed = int(value)
    except ValueError as exc:
        msg = "value must be a positive integer"
        raise argparse.ArgumentTypeError(msg) from exc
    if parsed < 1:
        msg = "value must be at least 1"
        raise argparse.ArgumentTypeError(msg)
    return parsed


def build_parser() -> argparse.ArgumentParser:
    """
    Build the command-line parser for the procedure generator.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.ArgumentParser
        Configured parser exposing help text, execution mode selection,
        artifact configuration, and optional coverage inputs.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate or execute a deterministic Fontshow test procedure. "
            "The procedure covers the public pipeline stages through "
            "artifact-driven scenarios and emits self-describing output "
            "artifact names."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=("interactive", "script"),
        default="script",
        help="Procedure operating mode",
    )
    parser.add_argument(
        "--shell",
        choices=("bash", "powershell"),
        default="bash",
        help="Target shell used when --mode script is selected",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination script path when --mode script is selected",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("test_procedure_artifacts"),
        help="Directory receiving all generated procedure artifacts",
    )
    parser.add_argument(
        "--fontshow-command",
        default="fontshow",
        help="Command used to invoke the Fontshow CLI",
    )
    parser.add_argument(
        "--font-path",
        dest="font_paths",
        action="append",
        type=Path,
        default=[],
        help=(
            "Explicit font discovery path used to exercise "
            "dump-fonts --paths. Repeatable."
        ),
    )
    parser.add_argument(
        "--explicit-test-font",
        action="append",
        default=[],
        help=(
            "Explicit family name used to exercise create-catalog "
            "--test-font NAME. Repeatable."
        ),
    )
    parser.add_argument(
        "--python-command",
        default="python",
        help="Command used for auxiliary Python one-liners",
    )
    parser.add_argument(
        "--sample-language",
        action="append",
        default=["en"],
        help=(
            "Sample BCP-47 language selector used to exercise "
            "create-catalog --language. Repeatable."
        ),
    )
    parser.add_argument(
        "--sample-script",
        action="append",
        default=["LATN"],
        help=(
            "Sample ISO 15924 script selector used to exercise "
            "create-catalog --script. Repeatable."
        ),
    )
    parser.add_argument(
        "--loadability-jobs",
        type=_positive_int,
        default=1,
        help=(
            "Positive job count used when exercising dump-fonts and "
            "parse-inventory loadability options"
        ),
    )
    parser.add_argument(
        "--catalog-limit",
        type=int,
        default=8,
        help="Value used to exercise create-catalog --number",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Execute interactive steps without pause prompts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render commands without executing them in interactive mode",
    )
    parser.add_argument(
        "--stop-after-stage",
        type=int,
        choices=(1, 2, 3),
        default=None,
        help=(
            "Stop procedure after stage: 1=preflight, 2=dump-fonts, 3=parse-inventory"
        ),
    )
    return parser


def _ctx_from_args(args: argparse.Namespace) -> ProcedureContext:
    """
    Normalize parsed CLI arguments into one immutable context object.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    ProcedureContext
        Normalized procedure configuration.
    """
    return ProcedureContext(
        fontshow_command=str(args.fontshow_command),
        artifact_dir=Path(args.artifact_dir),
        shell=str(args.shell),
        font_paths=tuple(Path(path) for path in args.font_paths),
        explicit_test_fonts=tuple(str(name) for name in args.explicit_test_font),
        python_command=str(args.python_command),
        sample_languages=tuple(str(tag) for tag in args.sample_language),
        sample_scripts=tuple(str(code) for code in args.sample_script),
        loadability_jobs=int(args.loadability_jobs),
        catalog_limit=int(args.catalog_limit),
    )


def _artifact_path(ctx: ProcedureContext, name: str) -> Path:
    """
    Build one deterministic artifact path below the configured root.

    Parameters
    ----------
    ctx : ProcedureContext
        Procedure configuration.
    name : str
        Artifact filename.

    Returns
    -------
    Path
        Full artifact path.
    """
    return ctx.artifact_dir / name


def _latex_pass_count(argv: Sequence[str]) -> int:
    """
    Determine the required LuaLaTeX pass count for one catalog command.

    Parameters
    ----------
    argv : Sequence[str]
        Catalog command vector.

    Returns
    -------
    int
        ``2`` when indexed navigation is enabled, otherwise ``1``.

    Notes
    -----
    The pipeline documentation states that LuaLaTeX may require multiple
    passes to resolve indices and auxiliary constructs. ``--indexed-navigation``
    is the public catalog option that explicitly introduces index-like
    navigation features, so it is the deterministic trigger for a second
    pass in the generated procedure.
    """
    return 2 if "--indexed-navigation" in argv else 1


def _catalog_latex_steps(catalog_output: Path) -> list[Step]:
    """
    Build LuaLaTeX compilation steps for one generated catalog artifact.

    Parameters
    ----------
    catalog_output : Path
        Path to the generated ``.tex`` catalog.

    Returns
    -------
    list[Step]
        Ordered LuaLaTeX compilation steps.
    """
    argv = ("lualatex", "-interaction=nonstopmode", str(catalog_output))
    return [
        Step(
            name=f"compile_{catalog_output.stem}_pass_{pass_index}",
            description=(
                f"Compile {catalog_output.name} with LuaLaTeX (pass {pass_index})."
            ),
            argv=argv,
        )
        for pass_index in range(1, 3)
    ]


def _append_catalog_case(
    steps: list[Step], name: str, description: str, argv: list[str]
) -> None:
    """
    Append one catalog-generation case and its LuaLaTeX compilation steps.

    Parameters
    ----------
    steps : list[Step]
        Mutable procedure step list.
    name : str
        Stable case identifier.
    description : str
        Human-readable case description.
    argv : list[str]
        Catalog command vector.

    Returns
    -------
    None
    """
    catalog_output = Path(argv[argv.index("--output") + 1])
    steps.append(
        Step(
            name=name,
            description=description,
            argv=tuple(argv),
            produces_artifact=True,
            artifact_path=catalog_output,
        )
    )
    for latex_step in _catalog_latex_steps(catalog_output)[: _latex_pass_count(argv)]:
        steps.append(latex_step)


def build_steps(ctx: ProcedureContext) -> list[Step]:
    """
    Build the full deterministic procedure step list.

    Parameters
    ----------
    ctx : ProcedureContext
        Procedure configuration.

    Returns
    -------
    list[Step]
        Ordered procedure steps covering the public Fontshow pipeline.

    Notes
    -----
    The procedure is artifact-driven and bounded. It covers every
    user-facing option through a small set of meaningful scenarios.
    Cases that require optional caller-supplied inputs (for example
    ``dump-fonts --paths`` or explicit named test fonts) are included
    only when those inputs are provided.
    """
    fontshow = ctx.fontshow_command
    steps: list[Step] = []

    preflight_report_verbose = _artifact_path(ctx, "report__preflight_verbose.txt")
    preflight_report_quiet = _artifact_path(ctx, "report__preflight_quiet.txt")
    inventory_raw = _artifact_path(ctx, "inventory__raw.json")
    inventory_raw_fc = _artifact_path(ctx, "inventory__raw_fc_charset.json")
    inventory_raw_paths = _artifact_path(ctx, "inventory__raw_paths.json")
    inventory_infer_conservative = _artifact_path(
        ctx, "inventory__infer_conservative.json"
    )
    inventory_infer_medium = _artifact_path(ctx, "inventory__infer_medium.json")
    inventory_infer_aggressive = _artifact_path(ctx, "inventory__infer_aggressive.json")

    steps.append(
        Step(
            name="preflight_verbose_report",
            description="Run preflight in verbose mode and persist the report.",
            argv=(
                fontshow,
                "preflight",
                "--verbose",
                "--output",
                str(preflight_report_verbose),
            ),
            produces_artifact=True,
            artifact_path=preflight_report_verbose,
        )
    )
    steps.append(
        Step(
            name="preflight_quiet_report",
            description="Run preflight in quiet mode and persist the report.",
            argv=(
                fontshow,
                "preflight",
                "--quiet",
                "--output",
                str(preflight_report_quiet),
            ),
            produces_artifact=True,
            artifact_path=preflight_report_quiet,
        )
    )

    steps.append(
        Step(
            name="dump_fonts_baseline",
            description="Discover system fonts with the default dump-fonts pipeline.",
            argv=(
                fontshow,
                "dump-fonts",
                "--cache-dir",
                str(_artifact_path(ctx, "cache__dump_fonts_default")),
                "--loadability-jobs",
                str(ctx.loadability_jobs),
                "--verbose",
                "--output",
                str(inventory_raw),
            ),
            produces_artifact=True,
            artifact_path=inventory_raw,
        )
    )
    steps.append(
        Step(
            name="dump_fonts_fc_charset",
            description="Discover fonts including Fontconfig charset enrichment.",
            argv=(
                fontshow,
                "dump-fonts",
                "--cache-dir",
                str(_artifact_path(ctx, "cache__dump_fonts_fc_charset")),
                "--include-fc-charset",
                "--loadability-jobs",
                str(ctx.loadability_jobs),
                "--output",
                str(inventory_raw_fc),
            ),
            produces_artifact=True,
            artifact_path=inventory_raw_fc,
        )
    )
    steps.append(
        Step(
            name="dump_fonts_no_cache",
            description="Discover fonts with cache reuse disabled.",
            argv=(
                fontshow,
                "dump-fonts",
                "--no-cache",
                "--quiet",
                "--output",
                str(_artifact_path(ctx, "inventory__raw_no_cache.json")),
            ),
            produces_artifact=True,
            artifact_path=_artifact_path(ctx, "inventory__raw_no_cache.json"),
        )
    )

    if ctx.font_paths:
        path_args: list[str] = []
        for path in ctx.font_paths:
            path_args.append(str(path))
        steps.append(
            Step(
                name="dump_fonts_paths",
                description="Discover fonts from caller-supplied explicit paths only.",
                argv=(
                    fontshow,
                    "dump-fonts",
                    "--paths",
                    *path_args,
                    "--output",
                    str(inventory_raw_paths),
                ),
                produces_artifact=True,
                artifact_path=inventory_raw_paths,
            )
        )

    steps.append(
        Step(
            name="parse_inventory_conservative",
            description="Enrich the baseline inventory with conservative inference.",
            argv=(
                fontshow,
                "parse-inventory",
                str(inventory_raw),
                "--infer-level",
                "conservative",
                "--loadability-jobs",
                str(ctx.loadability_jobs),
                "--verbose",
                "--output",
                str(inventory_infer_conservative),
            ),
            produces_artifact=True,
            artifact_path=inventory_infer_conservative,
        )
    )
    steps.append(
        Step(
            name="parse_inventory_medium",
            description="Enrich the baseline inventory with medium inference.",
            argv=(
                fontshow,
                "parse-inventory",
                str(inventory_raw),
                "--infer-level",
                "medium",
                "--strict-bcp47",
                "--output",
                str(inventory_infer_medium),
            ),
            produces_artifact=True,
            artifact_path=inventory_infer_medium,
        )
    )
    steps.append(
        Step(
            name="parse_inventory_aggressive",
            description="Enrich the baseline inventory with aggressive inference.",
            argv=(
                fontshow,
                "parse-inventory",
                str(inventory_raw_fc),
                "--infer-level",
                "aggressive",
                "--quiet",
                "--output",
                str(inventory_infer_aggressive),
            ),
            produces_artifact=True,
            artifact_path=inventory_infer_aggressive,
        )
    )
    steps.append(
        Step(
            name="parse_inventory_validate_only",
            description="Validate the raw inventory structure without generating output.",
            argv=(
                fontshow,
                "parse-inventory",
                str(inventory_raw),
                "--validate-inventory",
            ),
        )
    )
    steps.append(
        Step(
            name="parse_inventory_missing_language_summary",
            description="List fonts missing language coverage in summary mode.",
            argv=(
                fontshow,
                "parse-inventory",
                str(inventory_raw),
                "--list-missing-language-coverage",
            ),
        )
    )
    steps.append(
        Step(
            name="parse_inventory_missing_language_detailed",
            description="List fonts missing language coverage with one line per match.",
            argv=(
                fontshow,
                "parse-inventory",
                str(inventory_raw),
                "--list-missing-language-coverage",
                "--show-all-missing-language-coverage",
            ),
        )
    )

    steps.append(
        Step(
            name="validate_inventory_conservative",
            description="Validate the conservative enriched inventory.",
            argv=(
                fontshow,
                "validate-inventory",
                str(inventory_infer_conservative),
                "--verbose",
            ),
        )
    )
    steps.append(
        Step(
            name="validate_inventory_default_path",
            description=(
                "Validate the default inventory path after copying the medium "
                "inference artifact into the default filename."
            ),
            argv=(
                ctx.python_command,
                "-c",
                (
                    "from pathlib import Path; "
                    f"src=Path({str(inventory_infer_medium)!r}); "
                    "dst=Path('font_inventory.json'); "
                    "dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')"
                ),
            ),
            produces_artifact=True,
            artifact_path=Path("font_inventory.json"),
        )
    )
    steps.append(
        Step(
            name="validate_inventory_default_call",
            description="Validate inventory using validate-inventory default path resolution.",
            argv=(fontshow, "validate-inventory", "--quiet"),
        )
    )

    _append_catalog_case(
        steps,
        name="create_catalog_baseline",
        description="Generate a baseline catalog from the conservative inventory.",
        argv=[
            fontshow,
            "create-catalog",
            "--inventory",
            str(inventory_infer_conservative),
            "--catalog-detail",
            "compact",
            "--number",
            str(ctx.catalog_limit),
            "--verbose",
            "--output",
            str(_artifact_path(ctx, "catalog__baseline_compact.tex")),
        ],
    )
    _append_catalog_case(
        steps,
        name="create_catalog_extended_filtered",
        description="Generate an extended catalog filtered by language and script.",
        argv=[
            fontshow,
            "create-catalog",
            "--inventory",
            str(inventory_infer_medium),
            "--catalog-detail",
            "extended",
            *sum([["--language", lang] for lang in ctx.sample_languages], []),
            *sum([["--script", script] for script in ctx.sample_scripts], []),
            "--sort-by",
            "language",
            "--sort-by",
            "script",
            "--output",
            str(_artifact_path(ctx, "catalog__extended_filtered.tex")),
        ],
    )
    _append_catalog_case(
        steps,
        name="create_catalog_indexed_appendix",
        description=(
            "Generate a catalog with indexed navigation and ontology-backed appendix descriptions."
        ),
        argv=[
            fontshow,
            "create-catalog",
            "--inventory",
            str(inventory_infer_aggressive),
            "--indexed-navigation",
            "--appendix-descriptions",
            "--output",
            str(_artifact_path(ctx, "catalog__indexed_appendix.tex")),
        ],
    )
    _append_catalog_case(
        steps,
        name="create_catalog_test_subset",
        description="Generate a catalog for the default test subset.",
        argv=[
            fontshow,
            "create-catalog",
            "--inventory",
            str(inventory_infer_medium),
            "--test",
            "--test-font",
            "--output",
            str(_artifact_path(ctx, "catalog__test_subset.tex")),
        ],
    )
    steps.append(
        Step(
            name="create_catalog_list_test_fonts",
            description="List the effective test-font subset without generating a catalog.",
            argv=(
                fontshow,
                "create-catalog",
                "--inventory",
                str(inventory_infer_medium),
                "--list-test-fonts",
                "--quiet",
            ),
        )
    )

    if ctx.explicit_test_fonts:
        explicit_catalog_argv = [
            fontshow,
            "create-catalog",
            "--inventory",
            str(inventory_infer_medium),
        ]
        for font_name in ctx.explicit_test_fonts:
            explicit_catalog_argv.extend(["--test-font", font_name])
        explicit_catalog_argv.extend(
            [
                "--output",
                str(_artifact_path(ctx, "catalog__explicit_test_fonts.tex")),
            ]
        )
        _append_catalog_case(
            steps,
            name="create_catalog_explicit_test_fonts",
            description="Generate a catalog restricted to caller-supplied explicit test fonts.",
            argv=explicit_catalog_argv,
        )

    return steps


def _quote_command(argv: Sequence[str], shell: str) -> str:
    """
    Render one command line for a target shell.

    Parameters
    ----------
    argv : Sequence[str]
        Command vector to render.
    shell : str
        Target shell identifier.

    Returns
    -------
    str
        Shell-escaped command line.
    """
    if shell == "powershell":
        quoted_parts = []
        for item in argv:
            escaped = str(item).replace("'", "''")
            quoted_parts.append(f"'{escaped}'")
        return " ".join(quoted_parts)
    return shlex.join([str(item) for item in argv])


def render_script(steps: Sequence[Step], ctx: ProcedureContext) -> str:
    """
    Render a deterministic script for the selected shell.

    Parameters
    ----------
    steps : Sequence[Step]
        Ordered procedure steps.
    ctx : ProcedureContext
        Procedure configuration.

    Returns
    -------
    str
        Complete script text.
    """
    lines: list[str] = []
    artifact_dir_text = str(ctx.artifact_dir)

    if ctx.shell == "powershell":
        lines.extend(
            [
                "$ErrorActionPreference = 'Stop'",
                f"New-Item -ItemType Directory -Force -Path '{artifact_dir_text}' | Out-Null",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f"mkdir -p {shlex.quote(artifact_dir_text)}",
                "",
            ]
        )

    for index, step in enumerate(steps, start=1):
        lines.append(f"# Step {index}: {step.name}")
        lines.append(f"# {step.description}")
        lines.append(_quote_command(step.argv, ctx.shell))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _interactive_progress(index: int, total: int) -> int:
    """
    Compute one rough completion percentage for interactive execution.

    Parameters
    ----------
    index : int
        One-based step index.
    total : int
        Total number of procedure steps.

    Returns
    -------
    int
        Rounded-down percentage in the inclusive range ``[0, 100]``.
    """
    return (100 * index) // total


def _limit_steps_by_stage(
    steps: Sequence[Step], stop_after_stage: int | None
) -> list[Step]:
    """
    Limit the procedure to steps up to and including one pipeline stage.

    Parameters
    ----------
    steps : Sequence[Step]
        Full ordered procedure steps.
    stop_after_stage : int | None
        Stage cutoff where ``1`` means preflight, ``2`` means dump-fonts,
        ``3`` means parse-inventory, and ``None`` means no cutoff.

    Returns
    -------
    list[Step]
        Possibly truncated step list.
    """
    if stop_after_stage is None:
        return list(steps)

    stage_prefixes = {
        1: ("preflight",),
        2: ("preflight", "dump_fonts"),
        3: ("preflight", "dump_fonts", "parse_inventory"),
    }
    allowed_prefixes = stage_prefixes[stop_after_stage]
    limited_steps: list[Step] = []

    for step in steps:
        if step.name.startswith(allowed_prefixes):
            limited_steps.append(step)

    return limited_steps


def run_interactive(
    steps: Sequence[Step],
    ctx: ProcedureContext,
    *,
    no_prompt: bool,
    dry_run: bool,
) -> int:
    """
    Execute the procedure interactively.

    Parameters
    ----------
    steps : Sequence[Step]
        Ordered procedure steps.
    ctx : ProcedureContext
        Procedure configuration.
    no_prompt : bool
        Whether to suppress step-by-step prompts.
    dry_run : bool
        Whether to print commands without executing them.

    Returns
    -------
    int
        ``0`` on success, otherwise the failing subprocess exit code.
    """
    ctx.artifact_dir.mkdir(parents=True, exist_ok=True)
    total = len(steps)

    for index, step in enumerate(steps, start=1):
        progress = _interactive_progress(index, total)
        command_text = _quote_command(step.argv, shell="bash")
        print(f"[{progress:3d}%] Step {index}/{total}: {step.name}")
        print(f"        {step.description}")
        print(f"        {command_text}")
        if not no_prompt and not dry_run:
            response = input("        Press Enter to execute, or type 'q' to abort: ")
            if response.strip().lower() == "q":
                return 130
        if dry_run:
            continue
        completed = subprocess.run(step.argv, check=False)
        if completed.returncode != 0:
            print(
                f"ERROR: step '{step.name}' failed with exit code {completed.returncode}",
                file=sys.stderr,
            )
            return int(completed.returncode)

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """
    Execute the procedure generator CLI.

    Parameters
    ----------
    argv : Sequence[str] | None, optional
        Optional argument vector used for testing.

    Returns
    -------
    int
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    ctx = _ctx_from_args(args)
    steps = _limit_steps_by_stage(build_steps(ctx), args.stop_after_stage)

    if args.mode == "interactive":
        return run_interactive(
            steps,
            ctx,
            no_prompt=bool(args.no_prompt),
            dry_run=bool(args.dry_run),
        )

    script_text = render_script(steps, ctx)
    if args.output is None:
        print(script_text, end="")
        return 0

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(script_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
