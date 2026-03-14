"""
Exercise low-level LaTeX policy and render helpers.

Responsibilities
----------------
- Cover script display and render-policy fallbacks.
- Verify Polyglossia language collection and NFSS id stability.
- Cover renderer prefix and detokenize sanitization behavior.
"""

from fontshow.latex import policy, render


def test_format_script_display_uses_canonical_name_when_available(monkeypatch):
    """
    Ensure known scripts render as ``Name (CODE)`` and unknown ones stay uppercase.
    """
    monkeypatch.setattr(policy, "SCRIPT_INFO", {"ARAB": {"canonical_name": "Arabic"}})

    assert policy._format_script_display("arab") == "Arabic (ARAB)"
    assert policy._format_script_display("zzzz") == "ZZZZ"


def test_get_render_policy_supplies_non_latin_script_option(monkeypatch):
    """
    Ensure missing fontspec options fall back to ``Script=...`` for non-Latin scripts.
    """
    monkeypatch.setattr(
        policy,
        "SCRIPT_INFO",
        {
            "LATN": {"polyglossia_language": "english", "fontspec_opts": ""},
            "ARAB": {"polyglossia_language": "arabic", "fontspec_opts": ""},
        },
    )

    assert policy._get_render_policy("LATN") == ("english", "")
    assert policy._get_render_policy("ARAB") == ("arabic", "Script=Arab")
    assert policy._get_render_policy("ZZZZ") == ("", "")


def test_collect_polyglossia_other_languages_is_sorted_and_filtered(monkeypatch):
    """
    Ensure ``latin`` is always present and ``english`` is excluded from extras.
    """
    monkeypatch.setattr(
        policy,
        "SCRIPT_INFO",
        {
            "LATN": {"polyglossia_language": "english"},
            "ARAB": {"polyglossia_language": "arabic"},
            "HEBR": {"polyglossia_language": "hebrew"},
        },
    )

    result = policy._collect_polyglossia_other_languages(
        [
            {"inference": {"scripts": ["arab", "", 1]}},
            {"inference": {"scripts": ["hebr", "latn"]}},
            {"inference": "bad"},
        ]
    )

    assert (
        result
        == "\\setotherlanguage{arabic}\n\\setotherlanguage{hebrew}\n\\setotherlanguage{latin}\n"
    )


def test_nfss_family_id_is_stable_and_uses_ttc_index():
    """
    Ensure NFSS ids are deterministic and vary across TTC faces.
    """
    base = {"identity": {"file": "/tmp/font.ttc", "ttc_index": 0}}
    other = {"identity": {"file": "/tmp/font.ttc", "ttc_index": 1}}

    assert policy.nfss_family_id(base) == policy.nfss_family_id(base)
    assert policy.nfss_family_id(base) != policy.nfss_family_id(other)


def test_render_helpers_strip_controls_and_toggle_renderer_prefix(monkeypatch):
    """
    Ensure control chars are removed and renderer prefix follows platform policy.
    """
    assert render.escape_latex(r"\&_{}~^<>%$#") == (
        r"\textbackslash{}\&\_\{\}\textasciitilde{}\textasciicircum{}\textless{}\textgreater{}\%\$\#"
    )
    assert render._strip_ascii_control_chars("A\x00B\x7f\n\tC") == "AB\n\tC"
    assert render._latex_detokenize_safe("A}\x00B") == r"A\}B"

    monkeypatch.setattr(render, "IS_WINDOWS", True)
    assert render._renderer_option_prefix() == ""
    monkeypatch.setattr(render, "IS_WINDOWS", False)
    assert render._renderer_option_prefix() == "Renderer=Harfbuzz,"
