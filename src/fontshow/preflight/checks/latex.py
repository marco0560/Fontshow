"""
LuaLaTeX capability checks.

This module implements the preflight check verifying that the LuaLaTeX
engine required for catalog generation is available on the system.

Responsibilities
----------------
- Detect availability of the `lualatex` executable.
- Evaluate LuaLaTeX capability according to the current platform.
- Audit whether the local TeX surface can satisfy ontology-driven
  rendering requirements.
- Produce structured results describing LaTeX support.

Design principles
-----------------
The module uses lightweight runtime checks only. It does not compile
TeX documents. Platform-specific behavior is evaluated based on runtime
environment detection and read-only inspection of local TeX resources.

Architectural role
------------------
This module belongs to the **preflight subsystem** and implements the
LaTeX capability check executed during environment validation.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from fontshow.constants.runtime import SUBPROCESS_TIMEOUT_SECONDS
from fontshow.core.types import Severity
from fontshow.ontology.language_tables import SCRIPT_INFO
from fontshow.preflight.checks import environment
from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult

_FONTSPEC_SCRIPT_PATTERN = re.compile(r"\\newfontscript\{([^}]+)\}\{")


@dataclass(frozen=True)
class _TeXOntologyCapabilityGap:
    """
    Structured summary of ontology capabilities missing from local TeX.

    Parameters
    ----------
    missing_fontspec_scripts : tuple[str, ...]
        Canonically sorted ontology script names not declared by local
        ``fontspec`` support files.
    missing_polyglossia_languages : tuple[str, ...]
        Canonically sorted ontology languages lacking a local
        Polyglossia ``gloss-*.ldf`` module.
    """

    missing_fontspec_scripts: tuple[str, ...]
    missing_polyglossia_languages: tuple[str, ...]


def _read_command_stdout(*argv: str) -> str | None:
    """
    Execute a command and return decoded standard output.

    Parameters
    ----------
    *argv : str
        Command and arguments to execute.

    Returns
    -------
    str | None
        Decoded stdout when the command succeeds, otherwise ``None``.
    """
    try:
        proc = subprocess.run(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    stdout = proc.stdout.strip()
    return stdout or None


def _find_tex_resource(filename: str) -> Path | None:
    """
    Locate a TeX resource file via ``kpsewhich``.

    Parameters
    ----------
    filename : str
        TeX resource filename to resolve.

    Returns
    -------
    pathlib.Path | None
        Resolved path when ``kpsewhich`` can find the file, otherwise
        ``None``.
    """
    kpsewhich_bin = shutil.which("kpsewhich")
    if kpsewhich_bin is None:
        return None
    stdout = _read_command_stdout(kpsewhich_bin, filename)
    if not stdout:
        return None
    return Path(stdout.splitlines()[0].strip())


def _normalize_fontspec_script_name(name: str) -> str:
    """
    Normalize a fontspec script name for deterministic comparison.

    Parameters
    ----------
    name : str
        Raw script name from ontology or local ``fontspec`` data.

    Returns
    -------
    str
        Normalized script name with TeX tildes removed and surrounding
        whitespace collapsed.
    """
    return " ".join(name.replace("~", " ").split())


def _extract_fontspec_scripts(fontspec_text: str) -> list[str]:
    """
    Extract declared ``fontspec`` script names from a style file.

    Parameters
    ----------
    fontspec_text : str
        Raw contents of ``fontspec-luatex.sty``.

    Returns
    -------
    list[str]
        Sorted unique script names accepted by the local ``fontspec``
        installation.
    """
    return sorted(
        {
            _normalize_fontspec_script_name(name)
            for name in _FONTSPEC_SCRIPT_PATTERN.findall(fontspec_text)
        }
    )


def _extract_polyglossia_languages(polyglossia_dir: Path) -> list[str]:
    """
    Extract installed Polyglossia language modules from a directory.

    Parameters
    ----------
    polyglossia_dir : pathlib.Path
        Directory containing ``gloss-*.ldf`` files.

    Returns
    -------
    list[str]
        Sorted unique Polyglossia module names.
    """
    return sorted(
        {
            path.stem.replace("gloss-", "")
            for path in polyglossia_dir.glob("gloss-*.ldf")
            if path.is_file()
        }
    )


def _fontspec_script_from_opts(fontspec_opts: str) -> str | None:
    """
    Extract the ontology script name referenced by ``fontspec_opts``.

    Parameters
    ----------
    fontspec_opts : str
        Ontology ``fontspec_opts`` field.

    Returns
    -------
    str | None
        Normalized script name from a ``Script=...`` option when
        present, otherwise ``None``.
    """
    for part in fontspec_opts.split(","):
        stripped = part.strip()
        if not stripped.startswith("Script="):
            continue
        value = stripped.removeprefix("Script=").strip()
        if value.startswith("{") and value.endswith("}") and len(value) >= 2:
            value = value[1:-1]
        normalized = _normalize_fontspec_script_name(value)
        return normalized or None
    return None


def _required_ontology_fontspec_scripts() -> set[str]:
    """
    Collect fontspec script names required by the current ontology.

    Parameters
    ----------
    None

    Returns
    -------
    set[str]
        Normalized script names referenced by ontology
        ``fontspec_opts`` fields.
    """
    required: set[str] = set()
    for script_info in SCRIPT_INFO.values():
        fontspec_opts = script_info.get("fontspec_opts")
        if not isinstance(fontspec_opts, str) or not fontspec_opts.strip():
            continue
        script_name = _fontspec_script_from_opts(fontspec_opts)
        if script_name is not None:
            required.add(script_name)
    return required


def _required_ontology_polyglossia_languages() -> set[str]:
    """
    Collect Polyglossia modules required by the current ontology.

    Parameters
    ----------
    None

    Returns
    -------
    set[str]
        Ontology language identifiers that expect a local Polyglossia
        module.
    """
    required: set[str] = set()
    for script_info in SCRIPT_INFO.values():
        normalized = script_info["polyglossia_language"].strip()
        if normalized:
            required.add(normalized)
    return required


def audit_ontology_tex_capabilities(
    *,
    fontspec_path: Path | None = None,
    polyglossia_dir: Path | None = None,
) -> _TeXOntologyCapabilityGap:
    """
    Audit local TeX support against ontology rendering requirements.

    Parameters
    ----------
    fontspec_path : pathlib.Path | None, optional
        Explicit path to ``fontspec-luatex.sty`` for testing or
        deterministic overrides.
    polyglossia_dir : pathlib.Path | None, optional
        Explicit directory containing ``gloss-*.ldf`` files for testing
        or deterministic overrides.

    Returns
    -------
    _TeXOntologyCapabilityGap
        Structured list of ontology requirements missing from local
        ``fontspec`` or Polyglossia resources.
    """
    resolved_fontspec_path = (
        fontspec_path
        if fontspec_path is not None
        else _find_tex_resource("fontspec-luatex.sty")
    )
    resolved_polyglossia_dir = polyglossia_dir
    if resolved_polyglossia_dir is None:
        polyglossia_style = _find_tex_resource("polyglossia.sty")
        if polyglossia_style is not None:
            resolved_polyglossia_dir = polyglossia_style.parent

    available_fontspec_scripts: set[str] = set()
    if resolved_fontspec_path is not None and resolved_fontspec_path.exists():
        fontspec_text = resolved_fontspec_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        available_fontspec_scripts = set(_extract_fontspec_scripts(fontspec_text))

    available_polyglossia_languages: set[str] = set()
    if resolved_polyglossia_dir is not None and resolved_polyglossia_dir.exists():
        available_polyglossia_languages = set(
            _extract_polyglossia_languages(resolved_polyglossia_dir)
        )

    missing_fontspec_scripts = tuple(
        sorted(_required_ontology_fontspec_scripts() - available_fontspec_scripts)
    )
    missing_polyglossia_languages = tuple(
        sorted(
            _required_ontology_polyglossia_languages() - available_polyglossia_languages
        )
    )

    return _TeXOntologyCapabilityGap(
        missing_fontspec_scripts=missing_fontspec_scripts,
        missing_polyglossia_languages=missing_polyglossia_languages,
    )


def _render_capability_gap_message(gap: _TeXOntologyCapabilityGap) -> str:
    """
    Build a deterministic preflight message for a TeX capability gap.

    Parameters
    ----------
    gap : _TeXOntologyCapabilityGap
        Missing-capability summary to render.

    Returns
    -------
    str
        User-facing deterministic message describing the missing local
        TeX surface.
    """
    parts: list[str] = []
    if gap.missing_fontspec_scripts:
        preview = ", ".join(gap.missing_fontspec_scripts[:5])
        suffix = "" if len(gap.missing_fontspec_scripts) <= 5 else ", ..."
        parts.append(f"missing fontspec scripts: {preview}{suffix}")
    if gap.missing_polyglossia_languages:
        preview = ", ".join(gap.missing_polyglossia_languages[:5])
        suffix = "" if len(gap.missing_polyglossia_languages) <= 5 else ", ..."
        parts.append(f"missing Polyglossia modules: {preview}{suffix}")
    return (
        "LuaLaTeX available, but the local LaTeX installation lacks "
        "ontology-driven rendering support: " + "; ".join(parts)
    )


def _windows_lualatex_candidates() -> list[Path]:
    """
    Return deterministic Windows fallback locations for LuaLaTeX.

    Parameters
    ----------
    None

    Returns
    -------
    list[pathlib.Path]
        Candidate executable paths checked when ``lualatex`` is not
        discoverable via ``PATH`` on Windows.

    Notes
    -----
    The fallback is intentionally conservative and limited to common
    TeX Live installation roots. It does not recurse the filesystem or
    execute any external commands.
    """
    candidates: list[Path] = []

    texlive_root = Path("C:/texlive")
    if texlive_root.exists():
        for year_dir in sorted(texlive_root.iterdir(), reverse=True):
            if not year_dir.is_dir():
                continue
            candidates.append(year_dir / "bin" / "windows" / "lualatex.exe")

    profile_root = os.environ.get("USERPROFILE")
    if profile_root:
        candidates.append(
            Path(profile_root)
            / "AppData"
            / "Local"
            / "Programs"
            / "TeX Live"
            / "bin"
            / "win32"
            / "lualatex.exe"
        )

    return candidates


def has_lualatex() -> bool:
    """
    Detect availability of the LuaLaTeX engine.

    Parameters
    ----------
    None

    Returns
    -------
    bool
        True if `lualatex` is discoverable in `PATH` or in a supported
        Windows fallback location.

    Notes
    -----
    This function performs a simple executable lookup only. It does not
    verify that the engine can successfully compile a document.

    On Windows, the check also inspects a small set of common TeX Live
    installation paths so preflight remains useful when the TeX Live
    bin directory is installed but not exported into ``PATH``.
    """
    if shutil.which("lualatex") is not None:
        return True

    if environment.detect_os() != "windows":
        return False

    return any(candidate.is_file() for candidate in _windows_lualatex_candidates())


def _capability_gap_result(
    *,
    os_name: str,
    execution_mode: str,
) -> CheckResult | None:
    """
    Build a preflight result when local TeX lacks ontology capabilities.

    Parameters
    ----------
    os_name : str
        Normalized operating-system identifier.
    execution_mode : str
        Normalized execution-mode identifier.

    Returns
    -------
    CheckResult | None
        Warning result when ontology-required TeX capabilities are
        missing from the local LaTeX installation, otherwise ``None``.
    """
    _ = (os_name, execution_mode)
    gap = audit_ontology_tex_capabilities()
    if not gap.missing_fontspec_scripts and not gap.missing_polyglossia_languages:
        return None

    return CheckResult(
        "latex.capability",
        Severity.WARN,
        _render_capability_gap_message(gap),
    )


class LuaLatexCheck(BaseCheck):
    """
    Preflight check for LuaLaTeX availability.

    Notes
    -----
    The check evaluates tool availability, coarse platform support, and
    ontology-required local TeX capabilities without compiling any TeX.
    """

    check_id = "latex.capability"

    def run(self) -> CheckResult:
        """
        Execute the LuaLaTeX capability check.

        Parameters
        ----------
        None

        Returns
        -------
        CheckResult
            Structured result describing whether the `lualatex` engine is
            available and supported in the current environment.

        Notes
        -----
        Linux bare-metal environments require LuaLaTeX for a successful
        result. CI and Windows environments use downgraded result
        severities to reflect partial or experimental support.
        """
        os_name = environment.detect_os()
        execution_mode = environment.detect_execution_mode()

        if os_name == "linux":
            if execution_mode == "ci":
                if has_lualatex():
                    gap_result = _capability_gap_result(
                        os_name=os_name,
                        execution_mode=execution_mode,
                    )
                    if gap_result is not None:
                        return gap_result
                    return CheckResult(
                        self.check_id,
                        Severity.INFO,
                        "LuaLaTeX available (CI environment)",
                        skipped=True,
                    )
                return CheckResult(
                    self.check_id,
                    Severity.ERROR,
                    "LuaLaTeX not available in CI",
                )

            if has_lualatex():
                gap_result = _capability_gap_result(
                    os_name=os_name,
                    execution_mode=execution_mode,
                )
                if gap_result is not None:
                    return gap_result
                return CheckResult(
                    self.check_id,
                    Severity.OK,
                    "LuaLaTeX available",
                )
            return CheckResult(
                self.check_id,
                Severity.ERROR,
                "LuaLaTeX not available",
            )

        if os_name == "windows":
            if has_lualatex():
                gap_result = _capability_gap_result(
                    os_name=os_name,
                    execution_mode=execution_mode,
                )
                if gap_result is not None:
                    return gap_result
                return CheckResult(
                    self.check_id,
                    Severity.WARN,
                    "LuaLaTeX available on Windows (experimental)",
                )
            return CheckResult(
                self.check_id,
                Severity.ERROR,
                "LuaLaTeX not available on Windows",
            )

        return CheckResult(
            self.check_id,
            Severity.ERROR,
            "LuaLaTeX not supported on this OS",
        )
