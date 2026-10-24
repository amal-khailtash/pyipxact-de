"""Repository discovery behavior using offline XML fixtures."""

from unittest.mock import patch

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi.core import registry, resolve_handle
from amal.eda.ipxact_de import loader

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


def catalog(path, entries, name="catalog"):
    path.parent.mkdir(parents=True, exist_ok=True)
    root = etree.Element(f"{{{NS}}}catalog", nsmap={None: NS})
    for key, value in zip(VLNV_KEYS, ("vendor", "library", name, "1.0"), strict=True):
        etree.SubElement(root, f"{{{NS}}}{key}").text = value
    files = etree.SubElement(root, f"{{{NS}}}components")
    for uri, vlnv in entries:
        entry = etree.SubElement(files, f"{{{NS}}}ipxactFile")
        etree.SubElement(entry, f"{{{NS}}}vlnv", dict(zip(VLNV_KEYS, vlnv, strict=True)))
        etree.SubElement(entry, f"{{{NS}}}name").text = uri
    path.write_bytes(etree.tostring(root))
    return path


@pytest.mark.parametrize("uri_kind", ["relative", "absolute", "file"])
def test_catalog_discovers_local_uri(tmp_path, uri_kind):
    target = document(tmp_path / "external" / "with space.xml")
    uris = {"relative": "../external/with%20space.xml", "absolute": str(target), "file": target.as_uri()}
    source = catalog(tmp_path / "catalogs" / "root.xml", [(uris[uri_kind], VLNV)])
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert resolve_handle(registry.get_id(VLNV)).xml_path == str(target)


def test_nested_catalog_cycle_and_shared_target(tmp_path):
    target = document(tmp_path / "target.xml")
    a_vlnv = ("vendor", "library", "a", "1.0")
    b_vlnv = ("vendor", "library", "b", "1.0")
    a = catalog(tmp_path / "a.xml", [("b.xml", b_vlnv), ("target.xml", VLNV)], "a")
    catalog(tmp_path / "b.xml", [("a.xml", a_vlnv), ("target.xml", VLNV)], "b")
    with patch.object(loader.logger, "warning") as warning, patch.object(
        loader, "XmlDocument", wraps=loader.XmlDocument
    ) as parse:
        loader.load_registry_from_paths([str(a)], cache_dir=tmp_path)
    assert parse.call_count == 3
    assert registry.get_id(VLNV) is not None
    assert target.exists()
    assert any("cycle" in str(call) for call in warning.call_args_list)


def test_catalog_mismatch_and_missing_targets(tmp_path):
    document(tmp_path / "target.xml")
    source = catalog(tmp_path / "root.xml", [("target.xml", ("wrong", *VLNV[1:])), ("missing.xml", VLNV)])
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    messages = str(warning.call_args_list)
    assert "VLNV mismatch" in messages
    assert "Cannot read catalog target" in messages
    assert registry.get_id(VLNV) is not None


def test_unchanged_catalog_rechecks_deleted_dependency(tmp_path):
    target = document(tmp_path / "target.xml")
    source = catalog(tmp_path / "root.xml", [("target.xml", VLNV)])
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None
    target.unlink()
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is None
    document(target)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None


def test_remote_catalog_uri_is_not_fetched(tmp_path):
    source = catalog(tmp_path / "root.xml", [("https://example.org/target.xml", VLNV)])
    with patch.object(loader, "XmlDocument", wraps=loader.XmlDocument) as parse:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert parse.call_count == 1
    assert registry.get_id(VLNV) is None


def test_catalog_incomplete_entry_diagnostic(tmp_path):
    source = catalog(tmp_path / "root.xml", [("", VLNV)])
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert any("Incomplete catalog entry" in str(call) for call in warning.call_args_list)


@pytest.mark.parametrize("uri", ["file:", "file://[bad", "target.xml?query=1", "target.xml#fragment"])
def test_invalid_uri_does_not_stop_valid_sibling(tmp_path, uri):
    document(tmp_path / "target.xml")
    source = catalog(tmp_path / "root.xml", [(uri, VLNV), ("target.xml", VLNV)])
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None
    assert any("catalog URI" in str(call) for call in warning.call_args_list)


def test_incomplete_vlnv_is_not_followed(tmp_path):
    source = catalog(tmp_path / "root.xml", [("target.xml", ("", *VLNV[1:]))])
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert any("Incomplete catalog VLNV" in str(call) for call in warning.call_args_list)
    assert registry.get_id(VLNV) is None


def test_catalog_category_mismatch_diagnostic(tmp_path):
    document(tmp_path / "target.xml")
    source = catalog(tmp_path / "root.xml", [("target.xml", VLNV)])
    source.write_text(source.read_text().replace("components", "designs"))
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert any("category mismatch" in str(call) for call in warning.call_args_list)
    assert registry.get_id(VLNV) is not None


def test_malformed_target_does_not_stop_valid_sibling(tmp_path):
    (tmp_path / "bad.xml").write_text("<broken")
    document(tmp_path / "target.xml")
    source = catalog(tmp_path / "root.xml", [("bad.xml", VLNV), ("target.xml", VLNV)])
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None
    assert any("catalog target" in str(call) for call in warning.call_args_list)


@pytest.mark.parametrize(
    "category,root_name",
    [
        ("catalogs", "catalog"), ("busDefinitions", "busDefinition"),
        ("abstractionDefinitions", "abstractionDefinition"), ("components", "component"),
        ("abstractors", "abstractor"), ("designs", "design"),
        ("designConfigurations", "designConfiguration"), ("generatorChains", "generatorChain"),
        ("typeDefinitions", "typeDefinitions"),
    ],
)
def test_catalog_supported_category_matches(tmp_path, category, root_name):
    target = document(tmp_path / "target.xml")
    target.write_text(
        target.read_text().replace("<component ", f"<{root_name} ").replace("</component>", f"</{root_name}>")
    )
    source = catalog(tmp_path / "root.xml", [("target.xml", VLNV)])
    source.write_text(source.read_text().replace("components", category))
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None
    assert not any("category mismatch" in str(call) for call in warning.call_args_list)


@pytest.mark.parametrize("uri", ["bad%path.xml", "bad%2.xml", "bad%FF.xml", "bad%00.xml"])
def test_invalid_encoded_path_keeps_valid_sibling(tmp_path, uri):
    document(tmp_path / "target.xml")
    source = catalog(tmp_path / "root.xml", [(uri, VLNV), ("target.xml", VLNV)])
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None
    assert any("Invalid catalog URI" in str(call) for call in warning.call_args_list)


def test_older_referenced_version_is_available(tmp_path):
    target = document(tmp_path / "old.xml")
    target.write_text(target.read_text().replace("1685-2022", "1685-2014"))
    source = catalog(tmp_path / "root.xml", [("old.xml", VLNV)])
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is not None
    assert not any("Unsupported catalog target" in str(call) for call in warning.call_args_list)


def test_referenced_incomplete_root_vlnv_is_not_cached(tmp_path):
    target = document(tmp_path / "target.xml")
    target.write_text(target.read_text().replace("<version>1.0</version>", ""))
    source = catalog(tmp_path / "root.xml", [("target.xml", VLNV)])
    with patch.object(loader.logger, "warning") as warning:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(VLNV) is None
    assert str(target) not in loader._load_cache(tmp_path / loader.CACHE_BASENAME)
    assert any("Incomplete target VLNV" in str(call) for call in warning.call_args_list)


def test_vendor_extension_catalog_lookalike_not_followed(tmp_path):
    document(tmp_path / "target.xml")
    source = catalog(tmp_path / "root.xml", [("target.xml", VLNV)])
    root = etree.parse(str(source)).getroot()
    extension = etree.SubElement(root, f"{{{NS}}}vendorExtensions")
    extension.append(root.find(f"{{{NS}}}components"))
    source.write_bytes(etree.tostring(root))
    with patch.object(loader, "XmlDocument", wraps=loader.XmlDocument) as parse:
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert parse.call_count == 1
    assert registry.get_id(VLNV) is None
