"""Streaming file discovery and compact document reporting."""

from collections.abc import Iterator
from contextlib import AbstractContextManager
from os import DirEntry
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


def component(path: Path, name: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<component xmlns="{NS}"><vendor>v</vendor><library>l</library>'
        f"<name>{name}</name><version>1</version></component>"
    )
    return path


def test_streaming_walk_uses_deterministic_lexical_path_order(tmp_path: Path) -> None:
    files = [
        component(tmp_path / "a.xml", "a"),
        component(tmp_path / "foo" / "nested.xml", "nested"),
        component(tmp_path / "foo.xml", "foo-file"),
        component(tmp_path / "foo0.xml", "foo-zero"),
        component(tmp_path / "zdir" / "last.xml", "last"),
    ]

    assert list(loader._iter_xml_files([tmp_path])) == sorted(files)


def test_walk_yields_earlier_file_before_scanning_later_directory(tmp_path: Path) -> None:
    first = component(tmp_path / "a.xml", "first")
    component(tmp_path / "zdir" / "later.xml", "later")
    real_scandir = loader.os.scandir
    scanned: list[Path] = []

    def track_scandir(path: str | Path) -> AbstractContextManager[Iterator[DirEntry[str]]]:
        scanned.append(Path(path))
        return real_scandir(path)

    with patch.object(loader.os, "scandir", track_scandir):
        discovered = iter(loader._iter_xml_files([tmp_path]))
        assert next(discovered) == first
        assert scanned == [tmp_path]
        assert next(discovered) == tmp_path / "zdir" / "later.xml"


def test_walk_follows_file_symlinks_but_does_not_recurse_directory_symlinks(tmp_path: Path) -> None:
    source = component(tmp_path / "source.xml", "source")
    linked_file = tmp_path / "linked.xml"
    linked_dir = tmp_path / "linked_dir"
    try:
        linked_file.symlink_to(source)
        linked_dir.symlink_to(tmp_path, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")

    discovered = list(loader._iter_xml_files([tmp_path]))
    assert source in discovered
    assert not any(path.is_relative_to(linked_dir) for path in discovered)


def test_symlink_aliases_are_canonicalized_and_scanned_once(tmp_path: Path) -> None:
    source = component(tmp_path / "component.xml", "one")
    alias = tmp_path / "alias.xml"
    try:
        alias.symlink_to(source)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")

    with patch.object(loader, "_read_document", wraps=loader._read_document) as read:
        loader.load_registry_from_paths([str(tmp_path), str(alias)], cache_dir=tmp_path)

    assert read.call_count == 1
    assert registry.get_id(("v", "l", "one", "1")) is not None


def test_walk_preserves_relative_paths_for_relative_directory_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    component(tmp_path / "relative" / "nested.xml", "nested")
    monkeypatch.chdir(tmp_path)

    assert list(loader._iter_xml_files([Path("relative")])) == [Path("relative") / "nested.xml"]


def test_walk_warns_for_unreadable_directory_and_continues(tmp_path: Path) -> None:
    first = component(tmp_path / "a.xml", "first")
    (tmp_path / "zdir").mkdir()
    real_scandir = loader.os.scandir

    def fail_zdir(path: str | Path) -> AbstractContextManager[Iterator[DirEntry[str]]]:
        if Path(path) == tmp_path / "zdir":
            raise PermissionError("permission denied")
        return real_scandir(path)

    with patch.object(loader.os, "scandir", fail_zdir), patch.object(loader.logger, "warning") as warning:
        assert list(loader._iter_xml_files([tmp_path])) == [first]
    assert any("Cannot scan directory" in str(call) for call in warning.call_args_list)


def test_document_reporter_sees_filename_then_metadata_and_suppresses_parse_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = component(tmp_path / "component.xml", "one").resolve()
    reports: list[tuple[Path, str, str, str]] = []

    loader.load_registry_from_paths(
        [str(source)],
        cache_dir=tmp_path,
        document_reporter=lambda path, root, standard, version: reports.append((path, root, standard, version)),
    )

    assert reports == [
        (source, "", "", ""),
        (source, "component", "IPXACT", "1685-2022"),
    ]
    assert "Parsing" not in capsys.readouterr().out


def test_catalog_dependency_reports_each_document_once(tmp_path: Path) -> None:
    target = component(tmp_path / "target.xml", "target").resolve()
    root = tmp_path / "catalog.xml"
    root.write_text(
        f'<catalog xmlns="{NS}"><vendor>v</vendor><library>l</library><name>catalog</name><version>1</version>'
        '<components><ipxactFile><vlnv vendor="v" library="l" name="target" version="1" />'
        "<name>target.xml</name></ipxactFile></components></catalog>"
    )
    reports: list[tuple[Path, str, str, str]] = []

    loader.load_registry_from_paths(
        [str(root)],
        cache_dir=tmp_path,
        document_reporter=lambda path, name, standard, version: reports.append((path, name, standard, version)),
    )

    assert reports == [
        (root.resolve(), "", "", ""),
        (root.resolve(), "catalog", "IPXACT", "1685-2022"),
        (target, "", "", ""),
        (target, "component", "IPXACT", "1685-2022"),
    ]


def test_parse_progress_keeps_legacy_xml_document_output_without_reporter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = component(tmp_path / "component.xml", "one")

    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)

    output = capsys.readouterr().out
    assert "Parsing" in output
    assert "Found" in output
