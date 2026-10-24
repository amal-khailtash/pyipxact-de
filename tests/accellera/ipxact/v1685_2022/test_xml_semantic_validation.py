"""File and CLI validation expose scoped semantic failures after XSD validation."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from amal.eda.ipxact_de.xml_validation import validate_ipxact_xml

SCHEMAS = "submodules/accellera-schemas"


def write_abstraction(path: Path, clock: str = "clk") -> None:
    path.write_text(f'''<abstractionDefinition xmlns="http://www.accellera.org/XMLSchema/IPXACT/1685-2022">
<vendor>v</vendor><library>l</library><name>a</name><version>1</version>
<busType vendor="v" library="l" name="b" version="1"/>
<ports><port><logicalName>data</logicalName><wire><onInitiator><direction>in</direction>
<modeConstraints><timingConstraint clockName="{clock}">0</timingConstraint></modeConstraints>
</onInitiator></wire></port><port><logicalName>clk</logicalName><wire>
<qualifier><isClock>true</isClock></qualifier></wire></port></ports>
</abstractionDefinition>''')


@pytest.mark.parametrize("clock,valid", [("clk", True), ("data", False)])
def test_file_semantics_and_source_locations(tmp_path: Path, clock: str, valid: bool) -> None:
    path = tmp_path / "a.xml"
    write_abstraction(path, clock)
    assert validate_ipxact_xml(path, schema_root=SCHEMAS).ok
    result = validate_ipxact_xml(path, schema_root=SCHEMAS, semantic=True)
    assert result.ok is valid
    assert len(result.checked_semantic_rules) == 5
    if not valid:
        assert result.issues[0].rule_id == "SCR 12.8"
        assert result.issues[0].line == 5
        assert result.issues[0].path.endswith("/@clockName")


def test_schema_failure_skips_semantics(tmp_path: Path) -> None:
    path = tmp_path / "a.xml"
    write_abstraction(path)
    path.write_text(path.read_text().replace("<direction>in</direction>", "<direction>wrong</direction>"))
    result = validate_ipxact_xml(path, schema_root=SCHEMAS, semantic=True)
    assert not result.ok
    assert result.checked_semantic_rules == ()
    assert all(issue.rule_id is None for issue in result.issues)


def test_unsupported_root_is_explicit(tmp_path: Path) -> None:
    path = tmp_path / "bus.xml"
    path.write_text("""<busDefinition xmlns="http://www.accellera.org/XMLSchema/IPXACT/1685-2022">
<vendor>v</vendor><library>l</library><name>b</name><version>1</version>
<directConnection>false</directConnection><isAddressable>false</isAddressable></busDefinition>""")
    result = validate_ipxact_xml(path, schema_root=SCHEMAS, semantic=True)
    assert not result.ok
    assert "only" in result.issues[0].message
    assert result.checked_semantic_rules == ()


@pytest.mark.parametrize("clock,code", [("clk", 0), ("data", 1)])
def test_cli_semantic_status_and_rule_coverage(tmp_path: Path, clock: str, code: int) -> None:
    path = tmp_path / "a.xml"
    write_abstraction(path, clock)
    result = subprocess.run(
        [sys.executable, "-m", "amal.eda.ipxact_de.cli", "validate", "--schema-root", SCHEMAS, "--semantic", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == code, result.stderr
    assert "Checked semantic rules:" in result.stdout
    assert "SCR 12.8" in result.stdout
    if code:
        assert "Clock 'data'" in result.stdout


def test_cli_validates_all_inputs_and_returns_failure(tmp_path: Path) -> None:
    good, bad = tmp_path / "good.xml", tmp_path / "bad.xml"
    write_abstraction(good)
    write_abstraction(bad, "data")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "amal.eda.ipxact_de.cli",
            "validate",
            "--schema-root",
            SCHEMAS,
            "--semantic",
            str(bad),
            str(good),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "COLUMNS": "240"},
    )
    assert result.returncode == 1
    assert "bad.xml: invalid" in " ".join(result.stdout.split())
    assert "good.xml: valid" in " ".join(result.stdout.split())
