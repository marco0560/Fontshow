"""
Fontshow — language_tables
==========================

Authoritative language ↔ script semantic mappings.

These mappings are NOT Unicode ontology.
They represent Fontshow's linguistic policy layer and are shared
between parsing and inference modules to avoid circular imports.
"""

from __future__ import annotations

# ------------------------------------------------------------------
# Primary script per language (ISO-639 → ISO-15924)
# ------------------------------------------------------------------

LANGUAGE_PRIMARY_SCRIPT: dict[str, str] = {
    "ar": "ARAB",
    "bg": "CYRL",
    "cop": "COPT",
    "da": "LATN",
    "de": "LATN",
    "el": "GREK",
    "en": "LATN",
    "es": "LATN",
    "fi": "LATN",
    "fr": "LATN",
    "he": "HEBR",
    "hi": "DEVA",
    "hy": "ARMN",
    "it": "LATN",
    "ja": "JPAN",
    "ko": "HANG",
    "mk": "CYRL",
    "ne": "DEVA",
    "nl": "LATN",
    "no": "LATN",
    "pt": "LATN",
    "ru": "CYRL",
    "sr": "CYRL",
    "sv": "LATN",
    "th": "THAI",
    "ti": "ETHI",
    "uk": "CYRL",
    "vi": "LATN",
    "zh": "HANI",
}
