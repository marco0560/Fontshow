"""
Shared specimen texts and selectors.

This module is pure data + deterministic selectors.
It must not import parsing or rendering stages.
"""

from __future__ import annotations

SAMPLE_TEXTS: dict[str, str] = {
    "ar": "صِفْ خَلْقَ خَوْدٍ كَمِثْلِ الشَّمْسِ",
    "cop": "Ⲡⲁⲓ ⲙⲉⲧⲁⲛⲟⲓⲁ",
    "de": "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich",
    "el": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    "en": "The quick brown fox jumps over the lazy dog",
    "es": "El veloz murciélago hindú comía feliz cardillo y kiwi",
    "fr": "Portez ce vieux whisky au juge blond qui fume",
    "he": "דג סקרן שט בים מאוכזב ולפתע מצא לו חברה",
    "hy": "Վարդագույն աղվեսը ցատկում է ծույլ շան վրայով",
    "it": "Ma la volpe col suo balzo ha raggiunto il quieto Fido",
    "ja": "いろはにほへと ちりぬるを",
    "ko": "키스의 고유조건은 입술끼리 만나야 하고 특별한 기술은 필요치 않다",
    "ru": "Съешь же ещё этих мягких французских булок",
    "ta": "யாதும் ஊரே யாவரும் கேளிர்",
    "te": "అన్ని మానవజాతులు స్వేచ్ఛగా జన్మింయి, అందరికీ సమానమైన గౌరవం మరియు హక్కులు ఉన్నాయి",
    "ti": "ሰላም እንታይ ከመይ ኢኻ",
    "vi": "Chữ Việt rất phong phú và đa dạng",
    "zh": "天地玄黃 宇宙洪荒",
}

# ------------------------------------------------------------------
# Representative language fallback (script → language)
# Used when language inference is empty but script is known.
# ------------------------------------------------------------------

SCRIPT_DEFAULT_LANGUAGE: dict[str, str] = {
    "arab": "ar",
    "armn": "hy",
    "beng": "bn",
    "cyrl": "ru",
    "deva": "hi",
    "ethi": "ti",
    "grek": "el",
    "hang": "ko",
    "hani": "zh",
    "hebr": "he",
    "jpan": "ja",
    "khmr": "km",
    "laoo": "lo",
    "latn": "en",
    "mymr": "my",
    "taml": "ta",
    "thai": "th",
    "yiii": "ii",
}


def choose_language_sample(
    languages: list[str] | None,
    scripts: list[str] | None = None,
) -> str | None:
    """
    Choose a deterministic language-aware sample text, if available.

    Priority is the existing order of `inferred_languages`.
    """
    if not languages:
        return None

    # 1. Try inferred languages first
    for lang in languages:
        sample = SAMPLE_TEXTS.get(lang)
        if sample:
            return sample

    # 2. Representative fallback from dominant script
    if scripts:
        primary = scripts[0].lower()
        fallback_lang = SCRIPT_DEFAULT_LANGUAGE.get(primary)
        if fallback_lang:
            sample = SAMPLE_TEXTS.get(fallback_lang)
            if sample:
                return sample

    return None
