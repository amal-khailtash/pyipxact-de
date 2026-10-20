"""Repository discovery behavior using offline XML fixtures."""

from unittest.mock import patch

import pytest
from lxml import etree

from amal.eda.ipxact_de import loader
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import registry, resolve_handle

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
VLNV = ("vendor", "library", "component", "1.0")


def document(path, prefix=""):
    tag = f"{prefix}:" if prefix else ""
    declaration = f'xmlns:{prefix}' if prefix else "xmlns"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<{tag}component {declaration}="{NS}">'
        + "".join(f"<{tag}{key}>{value}</{tag}{key}>" for key, value in zip(VLNV_KEYS, VLNV, strict=True))
        + f"</{tag}component>"
    )
    return path


VLNV_KEYS = ("vendor", "library", "name", "version")


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    monkeypatch.delenv("IPXACT_XML_PATHS", raising=False)
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("prefix", ["", "custom", "ipxact"])
def test_scan_namespace_independent(tmp_path, prefix):
    path = document(tmp_path / "component.xml", prefix)
    loader.load_registry_from_paths([str(path)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None
    assert loader._extract_vlnv_from_root(etree.parse(str(path)).getroot()) == VLNV


def test_discover_uppercase_and_ignore_non_xml(tmp_path):
    upper = document(tmp_path / "nested" / "component.XML")
    (tmp_path / "other.txt").write_text("not xml")
    assert list(loader._iter_xml_files([tmp_path])) == [upper]


@pytest.mark.parametrize("cached", [False, True])
def test_first_search_path_wins_with_duplicate_diagnostic(tmp_path, cached):
    first = document(tmp_path / "z-first" / "component.xml")
    second = document(tmp_path / "a-second" / "component.xml")
    paths = [str(first.parent), str(second.parent)]
    if cached:
        loader.load_registry_from_paths(paths, cache_dir=tmp_path)
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths(paths, cache_dir=tmp_path)
    assert resolve_handle(registry.get_id(VLNV)).xml_path == str(first)
    assert any("Duplicate VLNV" in str(call) for call in warning.call_args_list)


def test_overlapping_paths_parse_once(tmp_path):
    path = document(tmp_path / "nested" / "component.xml")
    with patch.object(loader, "XmlDocument", wraps=loader.XmlDocument) as parse:
        loader.load_registry_from_paths([str(tmp_path), str(path)], cache_dir=tmp_path)
    assert parse.call_count == 1


def test_disappearing_file_does_not_abort_scan(tmp_path):
    missing = tmp_path / "gone.xml"
    surviving = document(tmp_path / "component.xml")
    with patch.object(loader, "_iter_xml_files", return_value=iter([missing, surviving])):
        loader.load_registry_from_paths([str(tmp_path)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None
