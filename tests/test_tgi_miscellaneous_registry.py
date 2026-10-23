"""Annex F.7.60 registry and persistence contracts."""

import stat
from pathlib import Path

import pytest
from xsdata.exceptions import SerializerError

from amal.eda.accellera.ipxact.v1685_2022.tgi import _miscellaneous_registry as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import catalog as catalog_api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Catalog


@pytest.fixture(autouse=True)
def _clear_registry():
    registry.clear()
    yield
    registry.clear()


def _catalog(name: str) -> Catalog:
    return Catalog(vendor="vendor", library="library", name=name, version="1.0")


def _write_catalog(path: Path, catalog: Catalog) -> None:
    path.write_text(XmlDocument.serializer().render(catalog), encoding="utf-8")


def _registered_id(vlnv: tuple[str, str, str, str]) -> str:
    handle = registry.get_id(vlnv)
    assert handle is not None
    return handle


def test_register_vlnv_loads_only_top_level_ipxact_documents_and_replace_updates_root(tmp_path):
    path = tmp_path / "catalog.xml"
    original = _catalog("original")
    _write_catalog(path, original)

    assert api.registerVLNV(str(path), False)
    original_id = _registered_id(("vendor", "library", "original", "1.0"))
    assert isinstance(resolve_handle(original_id), Catalog)
    assert registry.get_file_name(original_id) == str(path.resolve())
    assert not api.registerVLNV(str(path), False)

    replacement = _catalog("original")
    replacement.display_name = "new file contents"
    _write_catalog(path, replacement)
    assert api.registerVLNV(str(path), True)
    replacement_id = _registered_id(("vendor", "library", "original", "1.0"))
    assert replacement_id != original_id
    assert registry.get_vlnv(original_id) is None

    nested_path = tmp_path / "nested.xml"
    nested_path.write_text(
        '<ipxact:name xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2022">x</ipxact:name>',
        encoding="utf-8",
    )
    assert not api.registerVLNV(str(nested_path), False)
    assert not api.registerVLNV(str(tmp_path / "missing.xml"), False)


def test_register_vlnv_rejects_wrong_argument_types_before_loading(monkeypatch):
    def fail_if_loaded(*_args, **_kwargs):
        raise AssertionError("invalid arguments must be rejected before loading")

    monkeypatch.setattr(api, "_load_root", fail_if_loaded)
    assert not api.registerVLNV(Path("document.xml"), False)
    assert not api.registerVLNV("document.xml", 1)


def test_catalog_registration_uses_real_files_and_unregisters_referenced_vlnvs(tmp_path):
    child_path = tmp_path / "child.xml"
    child = _catalog("child")
    _write_catalog(child_path, child)

    parent = _catalog("parent")
    catalog_api.addCatalogCatalogsIpxactFile(get_handle(parent), ("vendor", "library", "child", "1.0"), "child.xml")
    parent_path = tmp_path / "parent.xml"
    _write_catalog(parent_path, parent)
    assert api.registerVLNV(str(parent_path), False)
    parent_id = _registered_id(("vendor", "library", "parent", "1.0"))

    assert api.registerCatalogVLNVs(parent_id)
    child_id = _registered_id(("vendor", "library", "child", "1.0"))
    assert isinstance(resolve_handle(child_id), Catalog)
    assert registry.get_file_name(child_id) == str(child_path.resolve())

    child_path.unlink()
    assert api.unregisterCatalogVLNVs(parent_id)
    assert registry.get_id(("vendor", "library", "child", "1.0")) is None
    assert registry.get_id(("vendor", "library", "parent", "1.0")) == parent_id
    assert not api.unregisterCatalogVLNVs("not-a-catalog")


def test_catalog_registration_rejects_mismatched_references_without_partial_registration(tmp_path):
    first_path = tmp_path / "first.xml"
    _write_catalog(first_path, _catalog("first"))
    second_path = tmp_path / "second.xml"
    _write_catalog(second_path, _catalog("actual-second"))

    parent = _catalog("parent")
    catalog_api.addCatalogCatalogsIpxactFile(get_handle(parent), ("vendor", "library", "first", "1.0"), "first.xml")
    catalog_api.addCatalogCatalogsIpxactFile(
        get_handle(parent), ("vendor", "library", "expected-second", "1.0"), "second.xml"
    )
    parent_path = tmp_path / "parent.xml"
    _write_catalog(parent_path, parent)
    assert api.registerVLNV(str(parent_path), False)
    parent_id = _registered_id(("vendor", "library", "parent", "1.0"))

    assert not api.registerCatalogVLNVs(parent_id)
    assert registry.get_id(("vendor", "library", "first", "1.0")) is None


def test_save_validates_and_persists_registered_top_level_models(tmp_path):
    path = tmp_path / "catalog.xml"
    catalog = _catalog("persisted")
    _write_catalog(path, catalog)
    path.chmod(0o640)
    assert api.registerVLNV(str(path), False)
    root_id = _registered_id(("vendor", "library", "persisted", "1.0"))
    root = resolve_handle(root_id)
    assert isinstance(root, Catalog)

    root.display_name = "saved from TGI"
    assert api.save()
    assert stat.S_IMODE(path.stat().st_mode) == 0o640
    restored = XmlDocument.parser().from_string(path.read_text(encoding="utf-8"), Catalog)
    assert restored.display_name == "saved from TGI"


def test_save_returns_false_when_registered_document_is_invalid(tmp_path):
    path = tmp_path / "catalog.xml"
    catalog = _catalog("invalid")
    _write_catalog(path, catalog)
    assert api.registerVLNV(str(path), False)
    root = resolve_handle(_registered_id(("vendor", "library", "invalid", "1.0")))
    assert isinstance(root, Catalog)

    root.vendor = ""
    before = path.read_text(encoding="utf-8")
    assert not api.save()
    assert path.read_text(encoding="utf-8") == before


def test_save_returns_false_when_xsdata_cannot_serialize_a_registered_document(tmp_path, monkeypatch):
    path = tmp_path / "catalog.xml"
    _write_catalog(path, _catalog("serializer-error"))
    assert api.registerVLNV(str(path), False)

    class BrokenSerializer:
        def render(self, _root):
            raise SerializerError("cannot serialize model")

    monkeypatch.setattr(XmlDocument, "serializer", classmethod(lambda _cls: BrokenSerializer()))
    assert not api.save()


def test_unregister_vlnv_uses_annex_four_string_array_shape():
    assert not api.unregisterVLNV(("vendor", "library", "missing", "1.0"))
    assert not api.unregisterVLNV(("too", "few", "values"))
