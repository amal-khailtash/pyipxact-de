"""Bus-definition batch 1: TGI contracts and schema-valid persistence."""

import pytest
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from org.accellera.ipxact.v1685_2022 import BusDefinition


@pytest.fixture
def bus():
    return BusDefinition(vendor="acme", library="bus", name="test", version="1", direct_connection=True,
                         is_addressable=False)


def roundtrip(bus):
    xml = XmlSerializer().render(bus)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    schema.assertValid(etree.fromstring(xml.encode()))
    return XmlParser().from_string(xml, BusDefinition)


def test_extends_reference_and_update(bus):
    handle = get_handle(bus)
    assert api.getBusDefinitionExtendsRefByVLNV(handle) is None
    for vlnv in [("acme", "bus", "base", "1"), ("other", "library", "replacement", "2")]:
        assert api.setBusDefinitionExtends(busDefID=handle, busDefVLNV=vlnv)
        assert api.getBusDefinitionExtendsRefByVLNV(handle) == ":".join(vlnv)
        assert roundtrip(bus).extends.name == vlnv[2]
    previous = bus.extends
    with pytest.raises(TgiError):
        api.setBusDefinitionExtends(handle, ["incomplete"])
    assert bus.extends is previous


def test_choice_enumerations_and_removal(bus):
    handle = get_handle(bus)
    first = api.addBusDefinitionChoice(handle, "width", ["8", "16", "32"])
    second = api.addBusDefinitionChoice(handle, "mode", ["0", "1"])
    assert [e.value for e in roundtrip(bus).choices.choice[0].enumeration] == ["8", "16", "32"]
    assert api.removeBusDefinitionChoice(first)
    assert resolve_handle(first) is None
    assert api.getBusDefinitionChoiceIDs(handle) == [second]
    assert len(roundtrip(bus).choices.choice) == 1
    assert api.removeBusDefinitionChoice(second)
    assert bus.choices is None
    assert roundtrip(bus).choices is None


def test_system_group_name_identity_and_order(bus):
    handle = get_handle(bus)
    first = api.addBusDefinitionSystemGroupName(handle, value="control")
    second = api.addBusDefinitionSystemGroupName(handle, value="data")
    assert api.getBusDefinitionSystemGroupNameIDs(handle) == [first, second]
    assert api.getBusDefinitionSystemGroupNameValue(first) == "control"
    assert [e.value for e in roundtrip(bus).system_group_names.system_group_name] == ["control", "data"]
    assert api.removeBusDefinitionSystemGroupName(first)
    assert resolve_handle(first) is None
    assert api.getBusDefinitionSystemGroupNameIDs(handle) == [second]


@pytest.mark.parametrize("operation,args", [
    (api.getBusDefinitionExtendsRefByVLNV, ()),
    (api.setBusDefinitionExtends, (["v", "l", "n", "1"],)),
    (api.addBusDefinitionChoice, ("choice", ["1"])),
    (api.removeBusDefinitionChoice, ()),
    (api.addBusDefinitionSystemGroupName, ("group",)),
])
def test_invalid_and_wrong_type_handles(operation, args, bus):
    for handle in ["missing", get_handle(bus.description if bus.description is not None else object())]:
        with pytest.raises(TgiError) as error:
            operation(handle, *args)
        assert error.value.fault_code == "INVALID_ID"


@pytest.mark.parametrize("setter,attribute", [
    (api.setBusDefinitionBroadcast, "broadcast"),
    (api.setBusDefinitionDirectConnection, "direct_connection"),
    (api.setBusDefinitionIsAddressable, "is_addressable"),
])
def test_boolean_setters_contract_and_persistence(bus, setter, attribute):
    handle = get_handle(bus)
    for value in [False, True, False]:
        assert setter(busDefID=handle, value=value) is True
        assert getattr(bus, attribute) is value
        assert getattr(roundtrip(bus), attribute) is value
    for value in ["false", "true", 0, 1, None]:
        with pytest.raises(TgiError) as error:
            setter(busDefID=handle, value=value)
        assert error.value.fault_code == "INVALID_ARGUMENT"
        assert getattr(bus, attribute) is False


def test_remove_broadcast_preserves_false_and_other_fields(bus):
    handle = get_handle(bus)
    assert api.removeBusDefinitionBroadcast(busDefID=handle) is False
    for value in [True, False]:
        api.setBusDefinitionBroadcast(busDefID=handle, value=value)
        assert api.removeBusDefinitionBroadcast(busDefID=handle) is True
        assert roundtrip(bus).broadcast is None
        assert bus.direct_connection is True
        assert bus.is_addressable is False
        assert api.removeBusDefinitionBroadcast(busDefID=handle) is False


def test_remove_extends_and_restore(bus):
    handle = get_handle(bus)
    assert api.removeBusDefinitionExtends(busDefID=handle) is False
    api.setBusDefinitionExtends(handle, ["acme", "bus", "base", "1"])
    assert api.removeBusDefinitionExtends(busDefID=handle) is True
    assert roundtrip(bus).extends is None
    assert api.getBusDefinitionExtendsRefByVLNV(handle) is None
    assert api.removeBusDefinitionExtends(busDefID=handle) is False
    api.setBusDefinitionExtends(handle, ["acme", "bus", "new", "2"])
    assert roundtrip(bus).extends.name == "new"


@pytest.mark.parametrize("operation,args", [
    (api.setBusDefinitionBroadcast, (True,)),
    (api.setBusDefinitionDirectConnection, (False,)),
    (api.setBusDefinitionIsAddressable, (True,)),
    (api.removeBusDefinitionBroadcast, ()),
    (api.removeBusDefinitionExtends, ()),
])
def test_batch_two_invalid_handles(operation, args):
    for handle in ["missing", get_handle(object())]:
        with pytest.raises(TgiError) as error:
            operation(handle, *args)
        assert error.value.fault_code == "INVALID_ID"
