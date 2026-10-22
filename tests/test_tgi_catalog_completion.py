"""Catalog BASE and EXTENDED functions follow the 1685-2022 TGI contract."""

from uuid import uuid4

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import catalog as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Catalog

_CATEGORIES = [
    (
        "AbstractionDef",
        "abstraction_definitions",
        api.getCatalogAbstractionDefIpxactFileIDs,
        api.addCatalogAbstractionDefIpxactFile,
        api.removeCatalogAbstractionDefIpxactFile,
    ),
    (
        "Abstractors",
        "abstractors",
        api.getCatalogAbstractorsIpxactFileIDs,
        api.addCatalogAbstractorsIpxactFile,
        api.removeCatalogAbstractorsIpxactFile,
    ),
    (
        "BusDefinitions",
        "bus_definitions",
        api.getCatalogBusDefinitionsIpxactFileIDs,
        api.addCatalogBusDefinitionsIpxactFile,
        api.removeCatalogBusDefinitionsIpxactFile,
    ),
    (
        "Catalogs",
        "catalogs",
        api.getCatalogCatalogsIpxactFileIDs,
        api.addCatalogCatalogsIpxactFile,
        api.removeCatalogCatalogsIpxactFile,
    ),
    (
        "Components",
        "components",
        api.getCatalogComponentsIpxactFileIDs,
        api.addCatalogComponentsIpxactFile,
        api.removeCatalogComponentsIpxactFile,
    ),
    (
        "DesignConfigurations",
        "design_configurations",
        api.getCatalogDesignConfigurationsIpxactFileIDs,
        api.addCatalogDesignConfigurationsIpxactFile,
        api.removeCatalogDesignConfigurationsIpxactFile,
    ),
    (
        "Designs",
        "designs",
        api.getCatalogDesignsIpxactFileIDs,
        api.addCatalogDesignsIpxactFile,
        api.removeCatalogDesignsIpxactFile,
    ),
    (
        "GeneratorChains",
        "generator_chains",
        api.getCatalogGeneratorChainsIpxactFileIDs,
        api.addCatalogGeneratorChainsIpxactFile,
        api.removeCatalogGeneratorChainsIpxactFile,
    ),
    (
        "TypeDefinitions",
        "type_definitions",
        api.getCatalogTypeDefinitionsIpxactFileIDs,
        api.addCatalogTypeDefinitionsIpxactFile,
        api.removeCatalogTypeDefinitionsIpxactFile,
    ),
]


def _catalog() -> Catalog:
    return Catalog(vendor="v", library="l", name="catalog", version="1")


def _assert_schema_valid(catalog: Catalog) -> None:
    xml = XmlDocument.serializer().render(catalog)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    schema.assertValid(etree.fromstring(xml.encode()))


def test_all_catalog_operations_are_exported_and_each_category_round_trips():
    assert len(api.__all__) == 31
    assert all(callable(getattr(api, name)) for name in api.__all__)

    catalog = _catalog()
    catalog_id = get_handle(catalog)
    entries = []
    for index, (kind, field, getter, add, remove) in enumerate(_CATEGORIES):
        vlnv = ["vendor", "library", kind, str(index)]
        file_name = f"{kind}.xml"
        assert getter(catalog_id) == []
        entry_id = add(catalog_id, vlnv, file_name)
        entries.append((kind, field, getter, remove, entry_id, vlnv, file_name))
        assert getter(catalog_id) == [entry_id]
        assert api.getIpxactFileName(entry_id) == file_name
        assert api.getIpxactFileVlnvRefByVLNV(entry_id) == tuple(vlnv)

    _assert_schema_valid(catalog)
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(catalog), Catalog)
    for _, _, getter, _, _, _, _ in entries:
        assert len(getter(get_handle(parsed))) == 1

    for _kind, field, _, remove, entry_id, _, _ in entries:
        assert remove(entry_id)
        assert getattr(catalog, field) is None
        with pytest.raises(TgiError):
            api.getIpxactFileName(entry_id)
    _assert_schema_valid(catalog)


def test_catalog_setters_preserve_nested_reference_identity_and_validate_before_edit():
    catalog = _catalog()
    entry_id = api.addCatalogComponentsIpxactFile(get_handle(catalog), ["v", "l", "component", "1"], "component.xml")
    entry = resolve_handle(entry_id)
    name_id = get_handle(entry.name)
    vlnv_id = get_handle(entry.vlnv)
    assert get_parent_info(name_id).parent_handle == entry_id
    assert get_parent_info(name_id).path == ("name",)
    assert get_parent_info(vlnv_id).parent_handle == entry_id
    assert get_parent_info(vlnv_id).path == ("vlnv",)
    entry.vlnv.id = "vlnv-id"

    assert api.setIpxactFileName(entry_id, "${ROOT}/renamed.xml")
    assert api.setIpxactFileVlnv(entry_id, ["v", "l", "component", "2"])
    assert get_handle(entry.name) == name_id
    assert get_handle(entry.vlnv) == vlnv_id
    assert entry.vlnv.id == "vlnv-id"
    assert api.getIpxactFileName(entry_id) == "${ROOT}/renamed.xml"
    assert api.getIpxactFileVlnvRefByVLNV(entry_id) == ("v", "l", "component", "2")

    before = XmlDocument.serializer().render(catalog)
    for invalid in (["short"], ["v", "l", "n", object()], "v:l:n:1", None):
        with pytest.raises(TgiError):
            api.setIpxactFileVlnv(entry_id, invalid)
        assert XmlDocument.serializer().render(catalog) == before
    with pytest.raises(TgiError):
        api.setIpxactFileName(entry_id, None)
    assert XmlDocument.serializer().render(catalog) == before


def test_remove_rejects_wrong_category_and_removes_only_requested_entry():
    catalog = _catalog()
    catalog_id = get_handle(catalog)
    first = api.addCatalogComponentsIpxactFile(catalog_id, ["v", "l", "c1", "1"], "c1.xml")
    second = api.addCatalogComponentsIpxactFile(catalog_id, ["v", "l", "c2", "1"], "c2.xml")

    assert api.removeCatalogDesignsIpxactFile(first) is False
    assert api.getCatalogComponentsIpxactFileIDs(catalog_id) == [first, second]
    assert api.removeCatalogComponentsIpxactFile(first)
    assert api.getCatalogComponentsIpxactFileIDs(catalog_id) == [second]
    assert resolve_handle(second) is not None
    container_id = get_handle(catalog.components)
    assert api.removeCatalogComponentsIpxactFile(second)
    assert catalog.components is None
    assert resolve_handle(container_id) is None
    _assert_schema_valid(catalog)


def test_registered_parsed_catalog_owner_is_discovered_for_handle_only_setters():
    original = _catalog()
    original_id = get_handle(original)
    api.addCatalogComponentsIpxactFile(original_id, ["v", "l", "first", "1"], "first.xml")
    api.addCatalogDesignsIpxactFile(original_id, ["v", "l", "second", "1"], "second.xml")
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(original), Catalog)
    assert parsed.components is not None
    assert parsed.designs is not None

    catalog_vlnv = ("v", "l", f"registered-{uuid4()}", "1")
    registry.register(parsed, catalog_vlnv)
    try:
        # Obtain an ID directly from the parsed nested model, without first
        # enumerating that category through a TGI getter.
        entry_id = get_handle(parsed.designs.ipxact_file[0])
        before = XmlDocument.serializer().render(parsed)
        with pytest.raises(TgiError):
            api.setIpxactFileName(entry_id, "first.xml")
        with pytest.raises(TgiError):
            api.setIpxactFileVlnv(entry_id, ["v", "l", "first", "1"])
        assert XmlDocument.serializer().render(parsed) == before
    finally:
        registry.unregister(catalog_vlnv)


def test_catalog_add_rejects_malformed_inputs_without_mutation():
    catalog = _catalog()
    catalog_id = get_handle(catalog)
    for invalid in (["short"], ["v", "l", "n", 1], "v:l:n:1", None):
        with pytest.raises(TgiError):
            api.addCatalogComponentsIpxactFile(catalog_id, invalid, "component.xml")
        assert catalog.components is None
    with pytest.raises(TgiError):
        api.addCatalogComponentsIpxactFile("missing-catalog", ["v", "l", "n", "1"], "n.xml")
    assert catalog.components is None
