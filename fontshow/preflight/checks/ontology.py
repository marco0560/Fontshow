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
    """

    check_id = "ontology"

    def _check_language_scripts(self, LANGUAGE_INFO, SCRIPT_INFO) -> list[str]:
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

            for script in lang_scripts:
                if script not in scripts:
                    errors.append(
                        f"Language '{lang}' references unknown script '{script}'"
                    )

        return errors

    def _check_script_fields(self, SCRIPT_INFO) -> list[str]:
        required_fields = {
            "canonical_name",
            "display_language",
            "polyglossia_language",
            "fontspec_opts",
            "rtl",
            "requires_polyglossia",
            "specimen",
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

        Enforced invariant
        ------------------

        SCRIPT_INFO.keys() ⊆ UNICODE_SCRIPT_RANGES.keys()
        """
        from fontshow.ontology.unicode_tables import UNICODE_SCRIPT_RANGES

        script_info_scripts = set(SCRIPT_INFO.keys())
        unicode_range_scripts = set(UNICODE_SCRIPT_RANGES.keys())

        missing_ranges = script_info_scripts - unicode_range_scripts

        errors: list[str] = []

        if missing_ranges:
            errors.append(
                "Scripts missing Unicode ranges: " + ", ".join(sorted(missing_ranges))
            )

        return errors

    def run(self) -> CheckResult:
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
