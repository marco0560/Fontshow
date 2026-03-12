"""
Language inference helpers.

This module implements deterministic inference of candidate languages
based on Unicode block coverage information.

Responsibilities
----------------
- Infer candidate languages from Unicode block coverage statistics.
- Compute confidence levels for inferred languages.
- Produce structured language inference metadata used by the inventory.

Design principles
-----------------
Language inference operates exclusively on Unicode coverage data
produced during inventory generation. Platform-specific charset
metadata is intentionally ignored to ensure deterministic behavior
across environments.

Architectural role
------------------
This module belongs to the **inventory subsystem** and performs
language inference used during the inventory parsing stage.
"""

from __future__ import annotations

from typing import Any, cast

from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import (
    Confidence,
    LanguageInferenceInfo,
    ScriptISO,
    normalize_script_iso,
)
from fontshow.ontology.language_tables import (
    LANGUAGE_INFO,
    SCRIPT_INFO,
)
from fontshow.ontology.unicode_tables import UNICODE_BLOCK_SIZES

# Minimum fraction of a Unicode block that must be covered
# to infer a language from that block.
LANGUAGE_BLOCK_COVERAGE_THRESHOLD = 0.40


def _block_coverage_ratio(
    block_name: str,
    block_coverage: dict[str, int],
    block_sizes: dict[str, int],
) -> float:
    """
    Compute coverage ratio for a Unicode block.

    Parameters
    ----------
    block_name : str
        Name of the Unicode block.
    block_coverage : dict[str, int]
        Mapping of block names to covered codepoint counts.
    block_sizes : dict[str, int]
        Mapping of block names to normative block sizes.

    Returns
    -------
    float
        Fraction of the block covered (covered / size).
        Returns 0.0 if the block size is unknown or zero.

    Notes
    -----
    The ratio is purely arithmetic and does not clamp values above 1.0
    if the provided coverage counts exceed normative block sizes.
    """
    covered = block_coverage.get(block_name, 0)
    size = block_sizes.get(block_name, 0)

    if size <= 0:
        return 0.0

    return covered / size


# ------------------------------------------------------------------
# Phase 6.3 — block ratio cache (behavior-preserving)
# ------------------------------------------------------------------


def _build_block_ratio_cache(
    *,
    block_coverage: dict[str, int],
    block_sizes: dict[str, int],
) -> dict[str, float]:
    """
    Precompute Unicode block coverage ratios.

    Parameters
    ----------
    block_coverage : dict[str, int]
        Mapping of block names to covered codepoint counts.
    block_sizes : dict[str, int]
        Mapping of block names to normative block sizes.

    Returns
    -------
    dict[str, float]
        Mapping of block names to precomputed coverage ratios.

    Notes
    -----
    Pure optimization equivalent to repeated calls to
    `_block_coverage_ratio`.
    """
    ratios: dict[str, float] = {}

    for block_name, block_size in block_sizes.items():
        if block_size <= 0:
            ratios[block_name] = 0.0
            continue

        covered = block_coverage.get(block_name, 0)
        ratios[block_name] = covered / block_size

    return ratios


def _infer_allowed_languages_from_scripts(
    scripts_public: object,
) -> set[str] | None:
    """
    Restrict language candidates to those compatible with inferred scripts.

    Parameters
    ----------
    scripts_public : object
        Public script list extracted from coverage metadata.

    Returns
    -------
    set[str] | None
        Set of allowed language codes derived from script membership, or
        None when no usable script list is available.

    Notes
    -----
    Script identifiers are normalized to uppercase ISO form before
    comparing them against language profile script memberships.
    """
    inferred_scripts = (
        [str(s).lower() for s in scripts_public]
        if isinstance(scripts_public, list)
        else None
    )
    if not inferred_scripts:
        return None

    scripts_upper = {str(normalize_script_iso(s)) for s in inferred_scripts}
    return {
        lang
        for lang, profile in LANGUAGE_INFO.items()
        if any(str(script) in scripts_upper for script in profile.get("scripts", []))
    }


def _infer_languages_from_profiles(
    *,
    unicode_blocks: dict[str, int],
    allowed_languages: set[str] | None,
) -> dict[str, LanguageInferenceInfo]:
    """
    Infer candidate languages from Unicode block coverage using
    deterministic language profiles.

    This function evaluates each language profile defined in
    `LANGUAGE_PROFILES_ISO` against measured Unicode block coverage
    for a font. A language is accepted if at least one of its required
    Unicode blocks meets the configured coverage threshold.

    Inference model
    ---------------
    Each language profile defines:

    - required_blocks:
        Blocks that must reach a minimum coverage ratio for the
        language to be considered present.

    - optional_blocks:
        Additional blocks that increase confidence when present,
        but are not required.

    Confidence levels
    -----------------
    - "medium":
        At least one required block passes the coverage threshold.
    - "high":
        Required block(s) pass and at least one optional block is present.

    Performance
    -----------
    Unicode block coverage ratios are computed once per invocation
    and cached locally to avoid repeated division inside the
    language evaluation loop.

    Determinism
    -----------
    The algorithm is fully deterministic:
    - no probabilistic scoring
    - stable ordering via sorted evidence lists
    - identical inputs always produce identical outputs.

    Parameters
    ----------
    unicode_blocks : dict[str, int]
        Mapping of Unicode block name to number of covered codepoints.
    allowed_languages : set[str] | None
        Optional whitelist restricting evaluated languages.

    Returns
    -------
    dict[str, LanguageInferenceInfo]
        Mapping of inferred language codes to inference metadata.
        Only accepted language candidates are included.
    """
    _block_ratio_cache: dict[str, float] | None = None

    inferred: dict[str, LanguageInferenceInfo] = {}

    for lang, profile in LANGUAGE_INFO.items():
        if allowed_languages is not None and lang not in allowed_languages:
            continue

        required = set(profile["required_blocks"])
        optional = set(profile.get("optional_blocks", []))

        passed_blocks: list[str] = []
        for block in required:
            if _block_ratio_cache is None:
                _block_ratio_cache = _build_block_ratio_cache(
                    block_coverage=unicode_blocks,
                    block_sizes=UNICODE_BLOCK_SIZES,
                )

            ratio = _block_ratio_cache.get(block, 0.0)
            if ratio >= LANGUAGE_BLOCK_COVERAGE_THRESHOLD:
                passed_blocks.append(block)

        if not passed_blocks:
            log_trace_cat(
                log,
                "infer",
                "language candidate rejected",
                extra={
                    "lang": lang,
                    "reason": "no_required_block_passed",
                    "required_blocks": sorted(required),
                },
            )
            continue

        evidence = sorted(set(passed_blocks))
        optional_hits = sorted(optional & unicode_blocks.keys())

        confidence: Confidence = "medium"
        if optional_hits:
            confidence = "high"
            evidence.extend(optional_hits)

        log_trace_cat(
            log,
            "infer",
            "language candidate accepted",
            extra={
                "lang": lang,
                "confidence": confidence,
                "evidence_count": len(evidence),
                "required_blocks": sorted(required),
                "optional_hits": optional_hits,
                "evidence": evidence,
            },
        )

        inferred[lang] = LanguageInferenceInfo(
            confidence=confidence,
            evidence=evidence,
        )

    return inferred


def _apply_script_authoritative_fallbacks(
    *,
    inferred: dict[str, LanguageInferenceInfo],
    unicode_blocks: dict[str, int],
    coverage: dict[str, Any],
) -> dict[str, LanguageInferenceInfo]:
    """
    Apply deterministic script-based fallbacks to inferred languages.

    Parameters
    ----------
    inferred : dict[str, LanguageInferenceInfo]
        Current inferred language mapping.
    unicode_blocks : dict[str, int]
        Unicode block coverage counts used for special-case fallbacks.
    coverage : dict[str, Any]
        Coverage structure containing public script information.

    Returns
    -------
    dict[str, LanguageInferenceInfo]
        Possibly reduced or augmented language inference mapping.

    Notes
    -----
    The helper preserves script-authoritative behavior. It may narrow a
    Latin-only result to English for Basic Latin coverage, or inject a
    script-default display language when no language could be inferred.
    """
    scripts_public = coverage.get("scripts")
    scripts_lower: list[str] | None = None
    if isinstance(scripts_public, list) and scripts_public:
        scripts_lower = [str(s).lower() for s in scripts_public]

    if inferred:
        if (
            isinstance(scripts_lower, list)
            and set(scripts_lower) == {"latn"}
            and "en" in inferred
        ):
            blocks_present = set(unicode_blocks.keys())
            if blocks_present == {"Basic Latin"}:
                return {"en": inferred["en"]}
        return inferred

    if isinstance(scripts_lower, list) and scripts_lower:
        primary = sorted(str(s).lower() for s in scripts_lower)[0]
        info = SCRIPT_INFO.get(cast("ScriptISO", normalize_script_iso(primary)))
        lang = info["display_language"] if info else ""
        if lang:
            inferred[lang] = LanguageInferenceInfo(
                confidence="medium",
                evidence=["script-default"],
            )

    return inferred


def infer_languages(
    coverage: dict[str, Any],
    policy: str = "permissive",
    *,
    scripts_list: list[str] | None = None,
) -> dict[str, LanguageInferenceInfo]:
    """
    Infer candidate languages from parsed Unicode coverage metadata.

    This function represents the *language inference phase* of the
    Fontshow parsing pipeline and operates strictly after script
    identification has been completed by ``parse_inventory``.

    Language inference is therefore **script-authoritative**:
    languages are inferred only when canonical scripts are available.

    Parameters
    ----------
    coverage : dict[str, Any]
        Parsed coverage metadata for a font entry. Expected to contain
        canonical script information produced by the parse phase
        (``primary_script`` or ``scripts``).
    policy : str, optional
        Language inference policy selector (currently informational).
    scripts_list : list[str] | None, keyword-only
        Canonical script list provided explicitly by the parse layer.
        When supplied, this takes precedence over values stored in
        ``coverage``.

    Returns
    -------
    dict[str, LanguageInferenceInfo]
        Mapping of inferred language tags to supporting evidence.
        The mapping is deterministically ordered by language code.

    Inference Model
    ---------------
    The function follows a strict staged model:

    1. Canonical script resolution.
    2. Phase gate — inference runs only if scripts are known.
    3. Non-discriminative script filtering (e.g. LATN-only fonts).
    4. Unicode block profile evaluation.
    5. Script-authoritative fallback rules.
    6. Deterministic ordering of results.

    Notes
    -----
    * Language inference never consumes FontConfig charset data or
      declared languages.
    * Absence of scripts disables inference entirely.
    * Latin-only coverage is treated as non-discriminative and does
      not produce language candidates.
    * The result represents *capability inference*, not linguistic
      classification.
    """
    log_trace_cat(
        log,
        "infer",
        "language inference started",
        extra={
            "policy": policy,
            "unicode_blocks_count": len(coverage.get("unicode_blocks", {}) or {}),
        },
    )

    unicode_blocks: dict[str, int] = coverage.get("unicode_blocks", {}) or {}

    # --------------------------------------------------------------
    # Canonical script resolution
    # Priority:
    #   1. explicit scripts_list (parse layer canonical)
    #   2. coverage.primary_script (post-v0.41 invariant)
    #   3. coverage.scripts (legacy fallback)
    # --------------------------------------------------------------
    scripts_public: list[str] | None

    # --------------------------------------------------------------
    # when scripts_list is not None we are in
    # Pipeline mode: parse layer supplies canonical scripts.
    # otherwise we are in
    # Standalone mode: infer directly from unicode_blocks without
    # requiring parse-phase script inference.
    # --------------------------------------------------------------
    scripts_public = scripts_list if scripts_list is not None else None

    # --------------------------------------------------------------
    # UNKNOWN script handling
    #
    # In pipeline mode, UNKNOWN means script inference failed,
    # therefore language inference must not proceed.
    # In standalone mode (scripts_list is None), heuristic
    # inference is still allowed.
    # --------------------------------------------------------------
    if scripts_public == ["UNKNOWN"] and scripts_list is not None:
        return {}
    if scripts_public == ["LATN"]:
        blocks_present = set(unicode_blocks.keys())
        if blocks_present == {"Basic Latin"}:
            return {}

    allowed_languages = _infer_allowed_languages_from_scripts(scripts_public)

    inferred = _infer_languages_from_profiles(
        unicode_blocks=unicode_blocks,
        allowed_languages=allowed_languages,
    )

    log_trace_cat(
        log,
        "infer",
        "language inference completed",
        extra={
            "policy": policy,
            "languages_inferred": len(inferred),
            "profiles_total": len(LANGUAGE_INFO),
        },
    )

    inferred = _apply_script_authoritative_fallbacks(
        inferred=inferred,
        unicode_blocks=unicode_blocks,
        coverage=coverage,
    )

    return dict(sorted(inferred.items(), key=lambda kv: kv[0]))
