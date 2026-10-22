"""Catalog edits preserve generated reference wrappers and category ownership."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import catalog as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Catalog


@pytest.fixture(autouse=True)
def top_level_registry_only(monkeypatch):
    """Catalog records and their wrappers must never enter the VLNV registry."""
    registry.clear()
    register = registry.register

    def register_catalog(element, *args, **kwargs):
        assert isinstance(element, Catalog)
        return register(element, *args, **kwargs)

    monkeypatch.setattr(registry, "register", register_catalog)
    yield
    registry.clear()


def _root():
    return Catalog(vendor="v", library="l", name="catalog", version="1")


def _valid(root):
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    xml = XmlDocument.serializer().render(root)
    schema.assertValid(etree.fromstring(xml.encode()))
    return xml


def test_catalog_reference_edits_preserve_wrappers_and_validate_before_mutation():
    root = _root()
    entry_id = api.addCatalogComponentsIpxactFile(get_handle(root), ["v", "l", "component", "1"], "component.xml")
    entry = resolve_handle(entry_id)
    name_id, reference_id = get_handle(entry.name), get_handle(entry.vlnv)
    entry.vlnv.id = "reference"
    api.setIpxactFileName(entry_id, "${CATALOG_ROOT}/component.xml")
    api.setIpxactFileVlnv(entry_id, ["v", "l", "component", "2"])
    assert get_handle(entry.name) == name_id
    assert get_handle(entry.vlnv) == reference_id
    assert entry.vlnv.id == "reference"
    assert api.getIpxactFileName(entry_id) == "${CATALOG_ROOT}/component.xml"
    before = _valid(root)
    with pytest.raises(TgiError):
        api.setIpxactFileVlnv(entry_id, ["incomplete"])
    assert _valid(root) == before
    assert api.removeCatalogComponentsIpxactFile(entry_id)
    assert root.components is None
    for handle in [entry_id, name_id, reference_id]:
        assert resolve_handle(handle) is None
    _valid(root)


def test_parsed_catalog_entry_removal_checks_its_category():
    root = _root()
    api.addCatalogComponentsIpxactFile(get_handle(root), ["v", "l", "component", "1"], "component.xml")
    parsed = XmlDocument.parser().from_string(_valid(root), Catalog)
    entry_id = api.getCatalogComponentsIpxactFileIDs(get_handle(parsed))[0]
    try:
        removed = api.removeCatalogDesignsIpxactFile(entry_id)
    except TgiError:
        removed = False
    assert removed is False
    assert resolve_handle(entry_id) is parsed.components.ipxact_file[0]
    assert api.removeCatalogComponentsIpxactFile(entry_id)
    assert resolve_handle(entry_id) is None
    _valid(parsed)


def test_catalog_unique_names_and_vlnvs_are_checked_across_categories():
    root = _root()
    handle = get_handle(root)
    api.addCatalogComponentsIpxactFile(handle, ["v", "l", "component", "1"], "component.xml")
    second = api.addCatalogDesignsIpxactFile(handle, ["v", "l", "design", "1"], "design.xml")
    before = _valid(root)
    for vlnv, name in [
        (["v", "l", "component", "1"], "other.xml"),
        (["v", "l", "other", "1"], "component.xml"),
    ]:
        with pytest.raises(TgiError):
            api.addCatalogBusDefinitionsIpxactFile(handle, vlnv, name)
        assert _valid(root) == before
    with pytest.raises(TgiError):
        api.setIpxactFileName(second, "component.xml")
    with pytest.raises(TgiError):
        api.setIpxactFileVlnv(second, ["v", "l", "component", "1"])
    assert _valid(root) == before
