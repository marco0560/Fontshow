import json
import subprocess
import sys

import pytest


def _valid_inventory_from_cli(tmp_path, *_ignored):
    probe = tmp_path / "probe_env.json"

    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; "
                "from fontshow.inventory.platform_metadata import collect_platform_metadata; "
                f"open(r'{probe}', 'w').write(json.dumps(collect_platform_metadata()))"
            ),
        ],
        check=True,
    )

    env = json.loads(probe.read_text())

    return {
        "metadata": {
            "schema_version": "1.2",
            "input_inventory_tool": "fontshow",
            "input_inventory_tool_version": "test",
            "inference_level": "basic",
            "fonttools": {
                "available": False,
                "fontconfig_charset_included": False,
                "version": "unknown",
            },
            "run_environment": env,
        },
        "fonts": [],
    }


@pytest.mark.parametrize("stub_parse_inventory", ["ok"], indirect=True)
def test_parse_inventory_success(cli_runner, stub_parse_inventory, tmp_path):
    inp = tmp_path / "in.json"
    outp = tmp_path / "out.json"

    inp.write_text(json.dumps(_valid_inventory_from_cli(tmp_path, 0)))

    code, out = cli_runner(["fontshow", "parse-inventory", str(inp), "-o", str(outp)])

    assert code == 0


@pytest.mark.parametrize(
    "stub_parse_inventory, expected_code",
    [
        ("fail", 2),
        ("boom", 2),
    ],
    indirect=["stub_parse_inventory"],
)
def test_parse_inventory_failure(cli_runner, stub_parse_inventory, expected_code):
    code, out = cli_runner(["fontshow", "parse-inventory", "--input", "inv.json"])
    assert code == expected_code


def test_parse_inventory_accepts_strict_bcp47_flag(cli_runner, tmp_path):
    input_file = tmp_path / "in.json"
    output_file = tmp_path / "out.json"

    input_file.write_text(json.dumps(_valid_inventory_from_cli(tmp_path, 0)))

    code, out = cli_runner(
        [
            "fontshow",
            "parse-inventory",
            str(input_file),
            "-o",
            str(output_file),
            "--strict-bcp47",
        ]
    )

    assert code == 0
