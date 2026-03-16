"""
Ontology consistency checks.

This module implements the preflight check verifying that the internal
Fontshow ontology tables are structurally consistent.

Responsibilities
----------------
- Validate integrity of script metadata definitions.
- Verify language inference profiles reference valid scripts.
- Ensure representative languages and specimen samples are available.
- Guarantee deterministic resolution of script → language → specimen.

Design principles
-----------------
Ontology validation operates entirely on the static tables defined in
the ontology subsystem. The check ensures that ontology data remains
internally coherent and safe for use by inventory analysis and catalog
generation.

Architectural role
------------------
This module belongs to the **preflight subsystem** and implements the
ontology integrity check executed during environment validation.
"""

from __future__ import annotations

from fontshow.core.types import Severity
from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult


class OntologyCheck(BaseCheck):
    """
    Validate internal ontology consistency.

    This check ensures that the ontology tables defined in
    `fontshow.language_tables` are internally coherent and safe
    for the Fontshow pipeline.

    The ontology currently consists of two canonical tables:

        SCRIPT_INFO   → metadata about writing systems
        LANGUAGE_INFO → language inference profiles

    Invariants enforced
    -------------------

    1. Basic sanity
       - SCRIPT_INFO must not be empty
       - LANGUAGE_INFO must not be empty

    2. LANGUAGE → SCRIPT integrity
       - every language must define at least one script
       - every referenced script must exist in SCRIPT_INFO

    3. SCRIPT metadata completeness
       Each script entry must define the required fields used by
       rendering, specimen selection, and LaTeX generation.

    4. SCRIPT → LANGUAGE integrity
       - every script must reference a valid representative language
       - the representative language must exist in LANGUAGE_INFO

    5. Specimen availability invariant
       - the representative language must provide a specimen sample

    These invariants guarantee that:

        script → representative language → specimen

    always resolves deterministically.

    Notes
    -----
    The check operates entirely on in-repository static ontology data
    and performs no filesystem or network access.
    """

    check_id = "ontology"

    def _check_language_scripts(self, LANGUAGE_INFO, SCRIPT_INFO) -> list[str]:
        """
        Validate that language profiles reference known scripts.

        Parameters
        ----------
        LANGUAGE_INFO : Mapping
            Language metadata table to validate.
        SCRIPT_INFO : Mapping
            Script metadata table used as the source of valid script
            identifiers.

        Returns
        -------
        list[str]
            Validation errors describing missing canonical names,
            missing script assignments, or unknown referenced scripts.
        """
        scripts = set(SCRIPT_INFO.keys())
        errors: list[str] = []

        for lang, lang_info in LANGUAGE_INFO.items():
            canonical_name = lang_info.get("canonical_name")

            if not canonical_name or not str(canonical_name).strip():
                errors.append(f"Language '{lang}' missing canonical_name")

            lang_scripts = lang_info.get("scripts")

            if not lang_scripts:
                errors.append(f"Language '{lang}' has no scripts defined")
                continue

            primary_script = lang_info.get("primary_script")
            if primary_script is None:
                errors.append(f"Language '{lang}' missing primary_script")
            elif primary_script not in lang_scripts:
                errors.append(
                    f"Language '{lang}' primary_script '{primary_script}' "
                    "is not present in its scripts list"
                )

            for script in lang_scripts:
                if script not in scripts:
                    errors.append(
                        f"Language '{lang}' references unknown script '{script}'"
                    )

        return errors

    def _check_script_fields(self, SCRIPT_INFO) -> list[str]:
        """
        Validate that each script entry defines the required metadata fields.

        Parameters
        ----------
        SCRIPT_INFO : Mapping
            Script metadata table to validate.

        Returns
        -------
        list[str]
            Validation errors for script entries missing required fields.
        """
        required_fields = {
            "canonical_name",
            "display_language",
            "polyglossia_language",
            "fontspec_opts",
            "rtl",
            "requires_polyglossia",
            "specimen",
            "required_blocks",
            "optional_blocks",
            "suppresses",
            "inference_priority",
            "unicode_max_ranges",
            "block_match",
            "collapse_group",
            "preferred_over",
        }

        errors: list[str] = []

        for script, script_info in SCRIPT_INFO.items():
            missing = required_fields - set(script_info.keys())

            if missing:
                errors.append(
                    f"Script '{script}' missing fields: {', '.join(sorted(missing))}"
                )

        return errors

    def _check_script_display_language(self, LANGUAGE_INFO, SCRIPT_INFO) -> list[str]:
        """
        Validate that each script points to a known representative language.

        Parameters
        ----------
        LANGUAGE_INFO : Mapping
            Language metadata table containing valid language codes.
        SCRIPT_INFO : Mapping
            Script metadata table to validate.

        Returns
        -------
        list[str]
            Validation errors for unknown script display-language
            references.
        """
        languages = set(LANGUAGE_INFO.keys())
        errors: list[str] = []

        for script, script_info in SCRIPT_INFO.items():
            display_lang = script_info.get("display_language")

            if display_lang not in languages:
                errors.append(
                    f"Script '{script}' references unknown display language '{display_lang}'"
                )

        return errors

    def _check_specimens(self, LANGUAGE_INFO, SCRIPT_INFO) -> list[str]:
        """
        Validate specimen availability for representative script languages.

        Parameters
        ----------
        LANGUAGE_INFO : Mapping
            Language metadata table containing specimen samples.
        SCRIPT_INFO : Mapping
            Script metadata table containing representative languages.

        Returns
        -------
        list[str]
            Validation errors for representative languages missing usable
            specimen samples.
        """
        errors: list[str] = []

        for script, script_info in SCRIPT_INFO.items():
            display_lang = script_info.get("display_language")

            if display_lang not in LANGUAGE_INFO:
                continue

            lang_info = LANGUAGE_INFO[display_lang]
            specimen = lang_info.get("sample")

            if not isinstance(specimen, str) or not specimen.strip():
                errors.append(
                    f"Representative language '{display_lang}' "
                    f"for script '{script}' has no specimen sample"
                )

        return errors

    def _check_bidirectional_consistency(self, LANGUAGE_INFO, SCRIPT_INFO) -> list[str]:
        """
        Validate script-to-language references in both ontology directions.

        Parameters
        ----------
        LANGUAGE_INFO : Mapping
            Language metadata table to cross-check.
        SCRIPT_INFO : Mapping
            Script metadata table to cross-check.

        Returns
        -------
        list[str]
            Validation errors for representative language references that
            are not reciprocated in the language profile's script list.
        """
        errors: list[str] = []

        for script, script_info in SCRIPT_INFO.items():
            display_lang = script_info.get("display_language")

            if display_lang not in LANGUAGE_INFO:
                continue

            lang_info = LANGUAGE_INFO[display_lang]
            lang_scripts = lang_info.get("scripts") or []

            if script not in lang_scripts:
                errors.append(
                    f"Script '{script}' declares representative language "
                    f"'{display_lang}', but LANGUAGE_INFO['{display_lang}'] "
                    f"does not list script '{script}'"
                )

        return errors

    def _check_unicode_ranges(self, SCRIPT_INFO) -> list[str]:
        """
        Validate that every script in SCRIPT_INFO has Unicode coverage.

        Parameters
        ----------
        SCRIPT_INFO : Mapping
            Script metadata table to validate.

        Returns
        -------
        list[str]
            Validation errors for scripts missing Unicode range
            definitions.

        Notes
        -----
        Enforced invariant:
        each script must have either Unicode range coverage metadata or
        explicit block-driven inference metadata.
        """
        from fontshow.ontology.unicode_tables import UNICODE_SCRIPT_RANGES

        errors: list[str] = []

        for script, script_info in SCRIPT_INFO.items():
            if script in UNICODE_SCRIPT_RANGES:
                continue
            required_blocks = script_info.get("required_blocks") or []
            if required_blocks:
                continue
            errors.append(
                f"Script '{script}' has neither Unicode ranges nor required_blocks"
            )

        return errors

    def run(self) -> CheckResult:
        """
        Execute the ontology consistency check.

        Parameters
        ----------
        None

        Returns
        -------
        CheckResult
            Structured result reporting whether the ontology tables pass
            all enforced consistency invariants.
        """
        from fontshow.ontology.language_tables import LANGUAGE_INFO, SCRIPT_INFO

        errors: list[str] = []

        if not SCRIPT_INFO:
            errors.append("SCRIPT_INFO is empty")

        if not LANGUAGE_INFO:
            errors.append("LANGUAGE_INFO is empty")

        errors.extend(self._check_language_scripts(LANGUAGE_INFO, SCRIPT_INFO))
        errors.extend(self._check_script_fields(SCRIPT_INFO))
        errors.extend(self._check_script_display_language(LANGUAGE_INFO, SCRIPT_INFO))
        errors.extend(self._check_specimens(LANGUAGE_INFO, SCRIPT_INFO))
        errors.extend(self._check_bidirectional_consistency(LANGUAGE_INFO, SCRIPT_INFO))
        errors.extend(self._check_unicode_ranges(SCRIPT_INFO))

        if errors:
            return CheckResult(self.check_id, Severity.ERROR, "; ".join(errors))

        return CheckResult(self.check_id, Severity.OK, "Ontology tables validated")
