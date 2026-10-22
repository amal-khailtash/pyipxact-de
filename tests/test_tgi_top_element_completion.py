"""Registered-root enumeration and editing metadata match Annex F."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AbstractionDefinition,
    Abstractor,
    BusDefinition,
    Catalog,
    Component,
    Design,
    DesignConfiguration,
    GeneratorChain,
    TypeDefinitions,
)


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("getter,model", [
    (api.getAbstractionDefIDs, AbstractionDefinition), (api.getAbstractorIDs, Abstractor),
    (api.getBusDefIDs, BusDefinition), (api.getCatalogIDs, Catalog),
    (api.getComponentIDs, Component), (api.getDesignConfigurationIDs, DesignConfiguration),
    (api.getDesignIDs, Design), (api.getGeneratorChainIDs, GeneratorChain),
    (api.getTypeDefinitionsIDs, TypeDefinitions),
])
def test_registry_enumeration_is_typed_ordered_and_excludes_unregistered(getter, model):
    assert getter() == []
    kwargs = {}
    if model is AbstractionDefinition:
        kwargs = {"bus_type": None, "ports": AbstractionDefinition.Ports()}
    elif model is Abstractor:
        kwargs = {"abstractor_mode": None, "bus_type": None, "abstractor_interfaces": Abstractor.AbstractorInterfaces()}
    elif model is BusDefinition:
        kwargs = {"direct_connection": False, "is_addressable": False}
    first = model(**kwargs,vendor="v", library="l", name="first", version="1")
    second = model(**kwargs,vendor="v", library="l", name="second", version="1")
    unregistered = model(**kwargs,vendor="v", library="l", name="unregistered", version="1")
    get_handle(unregistered)
    registry.register(first, ("v", "l", "first", "1"))
    registry.register(Component(vendor="v", library="l", name="other", version="1"), ("v", "l", "other", "1"))
    registry.register(second, ("v", "l", "second", "1"))
    expected = [get_handle(first), get_handle(second)]
    if model is Component:
        expected.insert(1, api.getID(("v", "l", "other", "1")))
    assert getter() == expected
    registry.unregister(("v", "l", "first", "1"))
    assert get_handle(first) not in getter()


def test_paths_are_registry_metadata_and_dereference_links(tmp_path):
    root_id = api.createComponent(("v", "l", "c", "1"))
    root = tgi.resolve_handle(root_id)
    original_xml = XmlDocument.serializer().render(root)
    assert api.getXMLPath(root_id) is None
    target = tmp_path / "component.xml"
    target.write_text(original_xml)
    link = tmp_path / "link.xml"
    link.symlink_to(target)
    assert api.setXMLPath(root_id, str(link))
    assert api.getXMLPath(root_id, False) == str(link)
    assert api.getXMLPath(root_id, True) == str(target.resolve())
    assert registry.get_file_name(root_id) == str(link)
    assert XmlDocument.serializer().render(root) == original_xml
    assert api.edit(root_id)
    assert api.getID(("v", "l", "c", "1")) == root_id
    assert api.getVLNV(root_id) == ("v", "l", "c", "1")
    registry.unregister(("v", "l", "c", "1"))
    assert api.getXMLPath(root_id) is None
    assert api.getVLNV(root_id) is None
    assert not api.edit(root_id)


def test_registered_location_and_invalid_edits_are_atomic():
    root = Component(vendor="v", library="l", name="c", version="1")
    registry.register(root, ("v", "l", "c", "1"), file_name="original.xml")
    handle = get_handle(root)
    assert api.getXMLPath(handle) == "original.xml"
    for value in [None, "", "  ", 4]:
        with pytest.raises(TgiError):
            api.setXMLPath(handle, value)
    assert api.getXMLPath(handle) == "original.xml"
    with pytest.raises(TgiError):
        api.setXMLPath("missing", "new.xml")
    with pytest.raises(TgiError):
        api.getXMLPath(handle, "yes")
    assert not api.edit("missing")


def test_package_exports():
    for name in api.__all__:
        assert name in tgi.__all__
        assert callable(getattr(tgi, name))
