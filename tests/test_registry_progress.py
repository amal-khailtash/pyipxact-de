"""Progress reporting for registry cache restoration and scans."""

import json
from collections.abc import Iterator
from os import stat_result
from pathlib import Path
from unittest.mock import patch

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi.core import registry
from amal.eda.ipxact_de import loader

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("IPXACT_XML_PATHS", raising=False)
    registry.clear()
    yield
    registry.clear()


def component(path: Path, name: str = "one") -> Path:
    path.write_text(
        f'<component xmlns="{NS}"><vendor>v</vendor><library>l</library>'
        f"<name>{name}</name><version>1</version></component>"
    )
    return path


def test_cache_progress_counts_skipped_snapshot_entries_without_source_stat(tmp_path: Path) -> None:
    valid = tmp_path / "deleted.xml"
    unsupported = tmp_path / "unsupported.xml"
    no_vlnv = tmp_path / "no-vlnv.xml"
    records = [
        {
            "path": str(valid),
            "mtime": 1,
            "element": "component",
            "standard": "ipxact",
            "version": "1685-2022",
            "vlnv": ["v", "l", "one", "1"],
        },
        {
            "path": str(unsupported),
            "mtime": 1,
            "element": "component",
            "standard": "ipxact",
            "version": "future",
            "vlnv": ["v", "l", "two", "1"],
        },
        {
            "path": str(no_vlnv),
            "mtime": 1,
            "element": "catalog",
            "standard": "ipxact",
            "version": "1685-2022",
            "vlnv": None,
        },
    ]
    (tmp_path / loader.CACHE_BASENAME).write_text(json.dumps(records))
    source_paths = {str(valid), str(unsupported), str(no_vlnv)}
    original_stat = Path.stat

    def reject_source_stat(path: Path, *args: object, **kwargs: object) -> stat_result:
        if str(path) in source_paths:
            raise AssertionError(f"snapshot load touched source file {path}")
        return original_stat(path, *args, **kwargs)

    events: list[tuple[str, int, int]] = []
    with patch.object(Path, "stat", reject_source_stat):
        assert loader.load_registry_from_cache(
            cache_dir=tmp_path,
            validate_files=False,
            progress=lambda phase, current, total: events.append((phase, current, total)),
        )

    assert registry.get_id(("v", "l", "one", "1")) is not None
    assert registry.get_id(("v", "l", "two", "1")) is None
    assert events == [
        ("reading_cache", 0, 0),
        ("loading", 0, 3),
        ("loading", 1, 3),
        ("loading", 2, 3),
        ("loading", 3, 3),
        ("completed", 3, 3),
    ]


def test_scan_progress_finishes_after_deleted_and_malformed_discoveries(tmp_path: Path) -> None:
    deleted = tmp_path / "deleted.xml"
    malformed = tmp_path / "malformed.xml"
    malformed.write_text("<broken")
    good = component(tmp_path / "valid.xml")
    events: list[tuple[str, int, int]] = []

    with patch.object(loader, "_iter_xml_files", return_value=iter([deleted, malformed, good])):
        loader.load_registry_from_paths(
            [str(tmp_path)],
            cache_dir=tmp_path,
            progress=lambda phase, current, total: events.append((phase, current, total)),
        )

    assert registry.get_id(("v", "l", "one", "1")) is not None
    assert [event for event in events if event[0] == "discovering"] == [
        ("discovering", 0, 0),
        ("discovering", 1, 0),
        ("discovering", 2, 0),
        ("discovering", 3, 0),
        ("discovering", 3, 3),
    ]
    assert [event for event in events if event[0] == "scanning"] == [
        ("scanning", 0, 3),
        ("scanning", 1, 3),
        ("scanning", 2, 3),
        ("scanning", 3, 3),
    ]
    assert events[-1] == ("completed", 3, 3)


def test_progress_callback_exceptions_propagate_from_scan(tmp_path: Path) -> None:
    source = component(tmp_path / "component.xml")

    def fail_during_scan(phase: str, current: int, total: int) -> None:
        if phase == "scanning" and current == 1:
            raise RuntimeError("progress callback failed")

    with pytest.raises(RuntimeError, match="progress callback failed"):
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path, progress=fail_during_scan)
