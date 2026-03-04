from __future__ import annotations

from fontshow.preflight.checks.base import BaseCheck
from fontshow.preflight.model import CheckResult
from fontshow.types import ScriptISO, Severity, iso_to_tag, tag_to_iso


class OntologyCheck(BaseCheck):
    """
    Validate internal ontology table consistency.
    """

    check_id = "ontology"

    def run(self) -> CheckResult:
        from fontshow.language_tables import (
            LANGUAGE_PRIMARY_SCRIPT,
            LANGUAGE_PROFILES_ISO,
            SCRIPT_HUMAN_TO_ISO,
            SCRIPT_ISO_TO_DISPLAY_LANGUAGE,
            SCRIPT_ISO_TO_POLYGLOSSIA,
            SCRIPT_SAMPLES,
        )

        iso_script_keys: set[ScriptISO] = set(SCRIPT_ISO_TO_DISPLAY_LANGUAGE.keys())
        human_script_keys: set[str] = set(SCRIPT_HUMAN_TO_ISO.keys())
        human_script_values: set[ScriptISO] = set(SCRIPT_HUMAN_TO_ISO.values())

        errors: list[str] = []

        # ------------------------------------------------------------------
        # Script identifier round-trip invariant
        # ------------------------------------------------------------------

        for iso_id in LANGUAGE_PRIMARY_SCRIPT.values():
            if tag_to_iso(iso_to_tag(iso_id)) != iso_id:
                errors.append(
                    f"Invalid ISO script identifier round-trip for '{iso_id}'"
                )

        # ------------------------------------------------------------------
        # Language inference safety invariant
        # ------------------------------------------------------------------

        for lang, profile in LANGUAGE_PROFILES_ISO.items():
            for script in profile.get("scripts", []):
                if script not in human_script_values:
                    errors.append(
                        f"Language '{lang}' references ISO script '{script}' not defined in ontology"
                    )

        # LANGUAGE_PROFILES_ISO references (ISO scripts)
        for lang, profile in LANGUAGE_PROFILES_ISO.items():
            for script in profile.get("scripts", []):
                if script not in iso_script_keys:
                    errors.append(
                        f"Language '{lang}' references unknown script '{script}'"
                    )

        # SCRIPT_SAMPLES coherence (human scripts)
        for human_script in SCRIPT_SAMPLES:
            if human_script not in human_script_keys:
                errors.append(f"Specimen defined for unknown script '{human_script}'")

        # Polyglossia mapping coherence (ISO scripts)
        for script in SCRIPT_ISO_TO_POLYGLOSSIA:
            if script not in iso_script_keys:
                errors.append(
                    f"Polyglossia mapping references unknown script '{script}'"
                )

        # Optional but recommended: ensure every human script has a specimen
        missing_specimens = human_script_keys - set(SCRIPT_SAMPLES.keys())
        if missing_specimens:
            errors.append(
                "Missing specimen for scripts: " + ", ".join(sorted(missing_specimens))
            )

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
