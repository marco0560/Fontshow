from __future__ import annotations

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult
from fontshow.types import Severity


class OntologyCheck(BaseCheck):
    """
    Validate internal ontology table consistency.
    """

    check_id = "ontology"

    def run(self) -> CheckResult:
        from fontshow.language_tables import (
            LANGUAGE_PROFILES_ISO,
            SCRIPT_ISO_TO_DISPLAY_LANGUAGE,
            SCRIPT_ISO_TO_POLYGLOSSIA,
            SCRIPT_SAMPLES,
        )

        script_keys = set(SCRIPT_ISO_TO_DISPLAY_LANGUAGE.keys())

        # LANGUAGE_PROFILES_ISO references
        for lang, profile in LANGUAGE_PROFILES_ISO.items():
            for script in profile.get("scripts", []):
                if script not in script_keys:
                    return CheckResult(
                        self.check_id,
                        Severity.ERROR,
                        f"Language '{lang}' references unknown script '{script}'",
                    )

        # SCRIPT_SAMPLES coherence
        for script in SCRIPT_SAMPLES:
            if script not in script_keys:
                return CheckResult(
                    self.check_id,
                    Severity.ERROR,
                    f"Specimen defined for unknown script '{script}'",
                )

        # Polyglossia mapping coherence
        for script in SCRIPT_ISO_TO_POLYGLOSSIA:
            if script not in script_keys:
                return CheckResult(
                    self.check_id,
                    Severity.ERROR,
                    f"Polyglossia mapping references unknown script '{script}'",
                )

        return CheckResult(
            self.check_id,
            Severity.OK,
            "Ontology tables validated",
        )
