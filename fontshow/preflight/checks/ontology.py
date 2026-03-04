from __future__ import annotations

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult
from fontshow.types import Severity


class OntologyCheck(BaseCheck):
    """
    Validate internal ontology consistency.

    Invariants enforced
    -------------------
    1. SCRIPT_INFO and LANGUAGE_INFO must not be empty.
    2. Every language must reference at least one script.
    3. Every referenced script must exist in SCRIPT_INFO.
    4. SCRIPT_INFO entries must contain required fields.
    """

    check_id = "ontology"

    def run(self) -> CheckResult:
        from fontshow.language_tables import LANGUAGE_INFO, SCRIPT_INFO

        errors: list[str] = []

        # ------------------------------------------------------------
        # basic sanity
        # ------------------------------------------------------------

        if not SCRIPT_INFO:
            errors.append("SCRIPT_INFO is empty")

        if not LANGUAGE_INFO:
            errors.append("LANGUAGE_INFO is empty")

        scripts = set(SCRIPT_INFO.keys())

        # ------------------------------------------------------------
        # validate language → script references
        # ------------------------------------------------------------

        for lang, lang_info in LANGUAGE_INFO.items():

            lang_scripts = lang_info.get("scripts")

            if not lang_scripts:
                errors.append(f"Language '{lang}' has no scripts defined")
                continue

            for script in lang_scripts:
                if script not in scripts:
                    errors.append(
                        f"Language '{lang}' references unknown script '{script}'"
                    )

        # ------------------------------------------------------------
        # validate script metadata fields
        # ------------------------------------------------------------

        required_fields = {
            "canonical_name",
            "display_language",
            "polyglossia_language",
            "fontspec_opts",
            "rtl",
            "requires_polyglossia",
            "specimen",
        }

        for script, script_info in SCRIPT_INFO.items():
            missing = required_fields - set(script_info.keys())
            if missing:
                errors.append(
                    f"Script '{script}' missing fields: {', '.join(sorted(missing))}"
                )

        # ------------------------------------------------------------
        # result
        # ------------------------------------------------------------

        if errors:
            return CheckResult(
                self.check_id,
                Severity.ERROR,
                "; ".join(errors),
            )

        return CheckResult(
            self.check_id,
            Severity.OK,
            "Ontology tables validated",
        )
