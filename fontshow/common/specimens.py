"""
Shared specimen texts and selectors.

This module is pure data + deterministic selectors.
It must not import parsing or rendering stages.
"""

from __future__ import annotations

SAMPLE_TEXTS: dict[str, str] = {
    "en": "The quick brown fox jumps over the lazy dog",
    "it": "Ma la volpe col suo balzo ha raggiunto il quieto Fido",
    "fr": "Portez ce vieux whisky au juge blond qui fume",
    "de": "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich",
    "es": "El veloz murciélago hindú comía feliz cardillo y kiwi",
    "el": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία",
    "ru": "Съешь же ещё этих мягких французских булок",
    "hy": "Վարդագույն աղվեսը ցատկում է ծույլ շան վրայով",
    "ja": "いろはにほへと ちりぬるを",
    "vi": "Chữ Việt rất phong phú và đa dạng",
    "zh": "天地玄黃 宇宙洪荒",
    "ar": "صِفْ خَلْقَ خَوْدٍ كَمِثْلِ الشَّمْسِ",
    "he": "דג סקרן שט בים מאוכזב ולפתע מצא לו חברה",
    "ko": "키스의 고유조건은 입술끼리 만나야 하고 특별한 기술은 필요치 않다",
    "cop": "Ⲡⲁⲓ ⲙⲉⲧⲁⲛⲟⲓⲁ",
    "ti": "ሰላም እንታይ ከመይ ኢኻ",
    "ta": "யாதும் ஊரே யாவரும் கேளிர்",
    "te": "అన్ని మానవజాతులు స్వేచ్ఛగా జన్మించాయి, అందరికీ సమానమైన గౌరవం మరియు హక్కులు ఉన్నాయి",
}

# ------------------------------------------------------------------
# Representative language fallback (script → language)
# Used when language inference is empty but script is known.
# ------------------------------------------------------------------

SCRIPT_DEFAULT_LANGUAGE: dict[str, str] = {
    "latn": "en",
    "cyrl": "ru",
    "grek": "el",
    "arab": "ar",
    "hebr": "he",
    "deva": "hi",
    "beng": "bn",
    "taml": "ta",
    "mymr": "my",
    "hang": "ko",
    "jpan": "ja",
    "hani": "zh",
    "ethi": "ti",
    "armn": "hy",
    "khmr": "km",
    "thai": "th",
    "laoo": "lo",
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
