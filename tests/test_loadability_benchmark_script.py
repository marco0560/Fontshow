"""Exercise the loadability benchmark replay helper."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "run_loadability_probe.py"
)
_SPEC = importlib.util.spec_from_file_location("run_loadability_probe", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
run_loadability_probe = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = run_loadability_probe
_SPEC.loader.exec_module(run_loadability_probe)


def test_run_probe_passes_jobs_to_loadability_probe(tmp_path, monkeypatch):
    """
    Ensure the replay helper forwards benchmark job-count settings.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Temporary directory fixture used to stage inventory input/output.
    monkeypatch : pytest.MonkeyPatch
        Fixture used to replace the real LuaLaTeX probe.

    Returns
    -------
    None
    """
    inventory_path = tmp_path / "inventory.json"
    output_path = tmp_path / "out" / "inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "validation": {
                        "lualatex": {
                            "attempted": True,
                            "runtime_fingerprint": "fp-1",
                        }
                    }
                },
                "fonts": [
                    {
                        "family": "Alpha",
                        "loadability": {
                            "lualatex": {
                                "attempted": True,
                                "loadable": True,
                                "reason": None,
                                "runtime_fingerprint": "fp-1",
                                "probe_input": "U+0041",
                            }
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    calls: list[dict[str, int]] = []

    def _fake_probe(fonts, *, validation_metadata, batch_size, jobs):
        calls.append({"batch_size": batch_size, "jobs": jobs})
        validation_metadata["attempted"] = True
        fonts[0]["loadability"]["lualatex"].update(
            {
                "attempted": True,
                "loadable": True,
                "runtime_fingerprint": validation_metadata["runtime_fingerprint"],
                "probe_input": "U+0041",
            }
        )

    monkeypatch.setattr(
        run_loadability_probe,
        "probe_and_persist_lualatex_loadability",
        _fake_probe,
    )

    rc = run_loadability_probe.run_probe(
        inventory_path,
        output_path,
        batch_size=7,
        jobs=3,
    )

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert calls == [{"batch_size": 7, "jobs": 3}]
    assert data["metadata"]["validation"]["lualatex"]["attempted"] is True
    assert data["fonts"][0]["loadability"]["lualatex"]["loadable"] is True
