"""Standard abstraction and abstractor creation and traversal contracts."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as ad
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstractor, top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import (
    TgiError,
    TgiFaultCode,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition, Abstractor

VLNV = ("vendor", "library", "root", "1")
BUS = ("vendor", "library", "bus", "1")


@pytest.fixture(autouse=True)
def isolated_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("style", ["wire", "transactional"])
def test_abstraction_creation_and_standard_traversal(style):
    handle = top_element.createAbstractionDef(VLNV, BUS, "data", style)
    obj = resolve_handle(handle)
    assert isinstance(obj, AbstractionDefinition)
    assert registry.get_id(VLNV) == handle
    assert ad.getAbstractionDefBusTypeRefByVLNV(handle) == BUS
    ports = ad.getAbstractionDefPortIDs(handle)
    assert len(ports) == 1
    assert ad.getAbstractionDefPortLogicalName(ports[0]) == "data"
    assert ad.getAbstractionDefPortStyle(ports[0]) == style
    assert get_parent_info(ports[0]).parent_handle == handle
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), AbstractionDefinition) == obj
    assert top_element.createAbstractionDef(VLNV, BUS, "other", style) is None
    assert registry.get_id(VLNV) == handle


@pytest.mark.parametrize("mode", ["initiator", "target", "direct", "system"])
def test_abstractor_creation_and_standard_traversal(mode):
    handle = top_element.createAbstractor(VLNV, mode, BUS, "first", "second")
    obj = resolve_handle(handle)
    assert isinstance(obj, Abstractor)
    assert registry.get_id(VLNV) == handle
    assert abstractor.getAbstractorBusTypeRefByVLNV(handle) == BUS
    assert abstractor.getAbstractorAbstractorMode(handle) == (mode, None)
    mode_id = abstractor.getAbstractorAbstractorModeID(handle)
    assert resolve_handle(mode_id) is obj.abstractor_mode
    assert get_parent_info(mode_id).parent_handle == handle
    interfaces = abstractor.getAbstractorAbstractorInterfaceIDs(handle)
    assert [resolve_handle(i).name for i in interfaces] == ["first", "second"]
    assert all(get_parent_info(i).parent_handle == handle for i in interfaces)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj
    assert top_element.createAbstractor(VLNV, mode, BUS, "first", "second") is None
    assert registry.get_id(VLNV) == handle


@pytest.mark.parametrize("args", [
    (VLNV, BUS, "", "wire"), (VLNV, BUS, "data", "packet"),
    (VLNV, ("v", "l", "b"), "data", "wire"),
    (VLNV, ("v", "", "b", "1"), "data", "wire"),
    (("v", "l", "n"), BUS, "data", "wire"),
])
def test_abstraction_invalid_inputs_leave_registry_empty(args):
    with pytest.raises(TgiError) as error:
        top_element.createAbstractionDef(*args)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert registry.get_id(VLNV) is None


@pytest.mark.parametrize("mode,bus,first,second", [
    ("bad", BUS, "first", "second"), (None, BUS, "first", "second"),
    ("direct", BUS, "", "second"), ("direct", BUS, "first", None),
    ("direct", BUS, "same", "same"), ("direct", ("v", "l", "b"), "first", "second"),
])
def test_abstractor_invalid_inputs_leave_registry_empty(mode, bus, first, second):
    with pytest.raises(TgiError) as error:
        top_element.createAbstractor(VLNV, mode, bus, first, second)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert registry.get_id(VLNV) is None


@pytest.mark.parametrize("getter", [
    ad.getAbstractionDefBusTypeRefByVLNV, ad.getAbstractionDefPortIDs,
    ad.getAbstractionDefPortLogicalName, ad.getAbstractionDefPortStyle,
    abstractor.getAbstractorAbstractorInterfaceIDs, abstractor.getAbstractorAbstractorMode,
    abstractor.getAbstractorAbstractorModeID, abstractor.getAbstractorBusTypeRefByVLNV,
])
def test_verified_getters_reject_invalid_handles(getter):
    with pytest.raises(TgiError) as error:
        getter("missing")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
