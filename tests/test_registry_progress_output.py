"""Compact registry diagnostics and separation of progress from streamed output."""

import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from amal.eda.ipxact_de import cli


def test_compact_document_report_keeps_filename_and_metadata_on_one_line() -> None:
    status = cli._RegistryProgress("Registry scan", paths=(Path("/repo"),))
    sink = StringIO()
    status.target = Console(file=sink, width=80, height=25, force_terminal=False)
    path = Path("/repo") / ("long_directory_" * 8) / "component.xml"
    status.document(path, "", "", "")
    assert sink.getvalue() == ""
    status.document(path, "component", "IPXACT", "1685-2022")
    lines = sink.getvalue().splitlines()
    assert len(lines) == 1
    assert len(lines[0]) <= 80
    assert "component.xml" in lines[0]
    assert "IP-XACT 1685-2022 component" in lines[0]


def test_progress_is_visible_before_the_first_loader_event(capsys: pytest.CaptureFixture[str]) -> None:
    with cli._RegistryProgress("Registry scan"):
        assert "Registry scan..." in capsys.readouterr().err


def test_disabled_progress_does_not_print(capsys: pytest.CaptureFixture[str]) -> None:
    with cli._RegistryProgress("Registry scan", enabled=False) as status:
        status.update("discovering", 1, 2)
        status.document(Path("component.xml"), "component", "IPXACT", "1685-2022")
    assert capsys.readouterr().err == ""


def test_scan_and_list_keep_compact_progress_on_stderr(tmp_path: Path) -> None:
    namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
    for name, root in (("component", "component"), ("bus", "busDefinition")):
        (tmp_path / f"{name}.xml").write_text(
            f'<{root} xmlns="{namespace}"><vendor>v</vendor><library>l</library>'
            f"<name>{name}</name><version>1</version></{root}>"
        )
    command = [sys.executable, "-m", "amal.eda.ipxact_de.cli"]
    scan = subprocess.run(
        command + ["registry", "scan", str(tmp_path)], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert scan.returncode == 0, scan.stderr
    assert "Parsing ..." not in scan.stdout + scan.stderr
    assert "Registry scan..." in scan.stderr
    assert "bus.xml  IP-XACT 1685-2022 busDefinition" in scan.stderr
    assert "component.xml  IP-XACT 1685-2022 component" in scan.stderr
    assert "2/2" in scan.stderr
    assert "Scan completed." in scan.stdout
    listing = subprocess.run(
        command + ["registry", "list", "--flat"], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert listing.returncode == 0, listing.stderr
    assert "Loading inventory" in listing.stderr
    assert "Registry loading" in listing.stderr
    assert "Loading inventory" not in listing.stdout
    assert "v:l:component:1" in listing.stdout
    assert "v:l:bus:1" in listing.stdout
    quiet = subprocess.run(
        command + ["-s", "registry", "list", "--flat"], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert quiet.returncode == 0, quiet.stderr
    assert "Loading inventory" not in quiet.stderr
