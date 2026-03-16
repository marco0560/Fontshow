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

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the script ontology table.

    Returns
    -------
    None
    """
    monkeypatch.setattr(policy, "SCRIPT_INFO", {"ARAB": {"canonical_name": "Arabic"}})

    assert policy._format_script_display("arab") == "Arabic (ARAB)"
    assert policy._format_script_display("zzzz") == "ZZZZ"


def test_get_render_policy_uses_explicit_ontology_mapping_only(monkeypatch):
    """
    Ensure render policy never fabricates `Script=` values from ISO codes.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the script ontology table.

    Returns
    -------
    None
    """
    monkeypatch.setattr(
        policy,
        "SCRIPT_INFO",
        {
            "LATN": {"polyglossia_language": "english", "fontspec_opts": ""},
            "ARAB": {
                "polyglossia_language": "arabic",
                "fontspec_opts": "Script=Arabic",
            },
            "ARMN": {"polyglossia_language": "", "fontspec_opts": ""},
        },
    )

    assert policy._get_render_policy("LATN") == ("english", "")
    assert policy._get_render_policy("ARAB") == ("arabic", "Script=Arabic")
    assert policy._get_render_policy("ARMN") == ("", "")
    assert policy._get_render_policy("ZZZZ") == ("", "")


def test_collect_polyglossia_other_languages_is_sorted_and_filtered(monkeypatch):
    """
    Ensure ``latin`` is always present and ``english`` is excluded from extras.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the script ontology table.

    Returns
    -------
    None
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


def test_nfss_family_id_is_stable_and_uses_path():
    """
    Ensure NFSS ids are deterministic and vary across file paths.

    Returns
    -------
    None
    """
    base = {"path": "/tmp/font-a.ttf"}
    other = {"path": "/tmp/font-b.ttf"}

    assert policy.nfss_family_id(base) == policy.nfss_family_id(base)
    assert policy.nfss_family_id(base) != policy.nfss_family_id(other)


def test_render_helpers_strip_controls_and_toggle_renderer_prefix(monkeypatch):
    """
    Ensure control chars are removed and renderer prefix follows platform policy.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the Windows platform flag.

    Returns
    -------
    None
    """
    assert render.escape_latex(r"\&_{}~^<>%$#") == (
        r"\textbackslash{}\&\_\{\}\textasciitilde{}\textasciicircum{}\textless{}\textgreater{}\%\$\#"
    )
    assert render._strip_ascii_control_chars("A\x00B\x7f\n\tC") == "AB\n\tC"
    assert render._latex_detokenize_safe("A{\\}\x00B") == r"A\{\\\}B"

    monkeypatch.setattr(render, "IS_WINDOWS", True)
    assert render._renderer_option_prefix() == ""
    monkeypatch.setattr(render, "IS_WINDOWS", False)
    assert render._renderer_option_prefix() == "Renderer=Harfbuzz,"
