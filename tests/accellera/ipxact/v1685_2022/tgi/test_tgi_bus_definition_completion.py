"""Focused standard-contract coverage for Bus Definition TGI operations."""


import inspect

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import BusDefinition, UnsignedIntExpression

BASE = {
    "getBusDefinitionBroadcast": "F.7.17.1",
    "getBusDefinitionChoiceIDs": "F.7.17.2",
    "getBusDefinitionDirectConnection": "F.7.17.3",
    "getBusDefinitionExtendsRefByVLNV": "F.7.17.4",
    "getBusDefinitionIsAddressable": "F.7.17.5",
    "getBusDefinitionMaxInitiators": "F.7.17.6",
    "getBusDefinitionMaxInitiatorsExpression": "F.7.17.7",
    "getBusDefinitionMaxInitiatorsID": "F.7.17.8",
    "getBusDefinitionMaxTargets": "F.7.17.9",
    "getBusDefinitionMaxTargetsExpression": "F.7.17.10",
    "getBusDefinitionMaxTargetsID": "F.7.17.11",
    "getBusDefinitionSystemGroupNameIDs": "F.7.17.12",
}

EXTENDED = {
    "addBusDefinitionChoice": "F.7.18.1",
    "addBusDefinitionSystemGroupName": "F.7.18.2",
    "removeBusDefinitionBroadcast": "F.7.18.3",
    "removeBusDefinitionChoice": "F.7.18.4",
    "removeBusDefinitionExtends": "F.7.18.5",
    "removeBusDefinitionMaxInitiators": "F.7.18.6",
    "removeBusDefinitionMaxTargets": "F.7.18.7",
    "setBusDefinitionBroadcast": "F.7.18.8",
    "setBusDefinitionDirectConnection": "F.7.18.9",
    "setBusDefinitionExtends": "F.7.18.10",
    "setBusDefinitionIsAddressable": "F.7.18.11",
    "setBusDefinitionMaxInitiators": "F.7.18.12",
    "setBusDefinitionMaxTargets": "F.7.18.13",
}


def bus() -> BusDefinition:
    return BusDefinition(
        vendor="acme", library="bus", name="test", version="1", direct_connection=True, is_addressable=False
    )


def valid_xml(value: BusDefinition) -> str:
    xml = XmlDocument.serializer().render(value)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    schema.assertValid(etree.fromstring(xml.encode()))
    return xml


def test_all_numbered_operations_are_exported_with_exact_sections() -> None:
    assert len(BASE) + len(EXTENDED) == 25
    assert set(BASE | EXTENDED) <= set(api.__all__)
    for name, section in (BASE | EXTENDED).items():
        function = getattr(api, name)
        assert section in inspect.getdoc(function)
        assert section in "\n".join(inspect.getsource(function).splitlines()[:5])

    # This published compatibility operation is cross-listed in F.7.20.15.
    assert "removeBusDefinitionSystemGroupName" in api.__all__
    assert "F.7.20.15" in inspect.getdoc(api.removeBusDefinitionSystemGroupName)


def test_expression_getters_evaluate_sv_preserve_source_and_handle() -> None:
    item = bus()
    item.max_initiators = UnsignedIntExpression(value="008", other_attributes={"{urn:test}x": "y"})
    handle = get_handle(item)
    expression_id = api.getBusDefinitionMaxInitiatorsID(handle)
    assert expression_id == api.getBusDefinitionMaxInitiatorsID(handle)
    assert resolve_handle(expression_id) is item.max_initiators
    assert api.getBusDefinitionMaxInitiators(handle) == 8
    assert api.getBusDefinitionMaxInitiatorsExpression(handle) == "008"

    api.setBusDefinitionMaxInitiators(busDefID=handle, valueExpression="32'hFFFFFFFF")
    assert api.getBusDefinitionMaxInitiators(handle) == (1 << 32) - 1
    assert api.getBusDefinitionMaxInitiatorsExpression(handle) == "32'hFFFFFFFF"
    assert api.getBusDefinitionMaxInitiatorsID(handle) == expression_id
    assert item.max_initiators.other_attributes == {"{urn:test}x": "y"}
    api.setBusDefinitionMaxInitiators(handle, "MAX_INITIATORS")
    assert api.getBusDefinitionMaxInitiators(handle) is None
    assert api.getBusDefinitionMaxInitiatorsExpression(handle) == "MAX_INITIATORS"


@pytest.mark.parametrize("suffix,attribute", [("Initiators", "max_initiators"), ("Targets", "max_targets")])
def test_unsigned_setters_are_bounded_atomic_and_removal_invalidates_handle(suffix: str, attribute: str) -> None:
    item = bus()
    expression = UnsignedIntExpression(value="0", minimum=0, maximum=100, other_attributes={"{urn:test}label": "limit"})
    setattr(item, attribute, expression)
    handle = get_handle(item)
    setter = getattr(api, f"setBusDefinitionMax{suffix}")
    getter = getattr(api, f"getBusDefinitionMax{suffix}")
    child_getter = getattr(api, f"getBusDefinitionMax{suffix}ID")
    remover = getattr(api, f"removeBusDefinitionMax{suffix}")
    child_id = child_getter(handle)
    setter(busDefID=handle, valueExpression=100)
    assert getter(handle) == 100
    xml_before = valid_xml(item)

    for invalid in [-1, 101, 1 << 32, True, "", "-1"]:
        with pytest.raises(TgiError):
            setter(handle, invalid)
        assert valid_xml(item) == xml_before
        assert getattr(item, attribute) is expression

    assert expression.other_attributes == {"{urn:test}label": "limit"}
    assert expression.minimum == 0 and expression.maximum == 100
    assert remover(busDefID=handle)
    assert resolve_handle(child_id) is None
    assert getter(handle) is None
    assert not remover(busDefID=handle)
    valid_xml(item)


def test_defaults_extends_wrapper_identity_and_strict_capability_setters() -> None:
    item = bus()
    handle = get_handle(item)
    assert api.getBusDefinitionBroadcast(handle) is False
    assert api.getBusDefinitionDirectConnection(handle) is True
    assert api.getBusDefinitionIsAddressable(handle) is False
    assert api.getBusDefinitionMaxInitiators(handle) is None
    assert api.getBusDefinitionMaxTargets(handle) is None
    assert api.getBusDefinitionMaxInitiatorsID(handle) is None
    assert api.getBusDefinitionMaxTargetsID(handle) is None
    assert api.getBusDefinitionExtendsRefByVLNV(handle) is None

    api.setBusDefinitionExtends(handle, ["acme", "bus", "base", "1"])
    reference = item.extends
    reference.id = "extends-id"
    api.setBusDefinitionExtends(busDefID=handle, busDefVLNV=("other", "bus", "base", "2"))
    assert item.extends is reference
    assert item.extends.id == "extends-id"
    assert api.getBusDefinitionExtendsRefByVLNV(handle) == "other:bus:base:2"

    for setter, field in [
        (api.setBusDefinitionBroadcast, "broadcast"),
        (api.setBusDefinitionDirectConnection, "direct_connection"),
        (api.setBusDefinitionIsAddressable, "is_addressable"),
    ]:
        for bad in [0, 1, "true", "false", None]:
            before = getattr(item, field)
            with pytest.raises(TgiError):
                setter(handle, bad)
            assert getattr(item, field) is before
        setter(busDefID=handle, value=False)
    assert api.getBusDefinitionDirectConnection(handle) is False
    assert api.getBusDefinitionIsAddressable(handle) is False
    assert valid_xml(item)

    with pytest.raises(TgiError):
        api.setBusDefinitionExtends(handle, ["incomplete"])
    assert item.extends is reference


def test_group_and_choice_parsed_ownership_identity_and_subtree_removal() -> None:
    item = bus()
    handle = get_handle(item)
    group_ids = [api.addBusDefinitionSystemGroupName(handle, name) for name in ("control", "data")]
    api.addBusDefinitionChoice(handle, "width", ["8", "16"])
    parsed = XmlDocument.parser().from_string(valid_xml(item), BusDefinition)
    parsed_id = get_handle(parsed)
    parsed_groups = api.getBusDefinitionSystemGroupNameIDs(parsed_id)
    parsed_choices = api.getBusDefinitionChoiceIDs(parsed_id)
    group = resolve_handle(parsed_groups[0])
    choice = resolve_handle(parsed_choices[0])
    enumeration_id = get_handle(choice.enumeration[0])

    assert parsed_groups != group_ids
    assert api.getBusDefinitionSystemGroupNameValue(parsed_groups[0]) == "control"
    assert api.removeBusDefinitionSystemGroupName(parsed_groups[0])
    assert resolve_handle(parsed_groups[0]) is None
    assert api.getBusDefinitionSystemGroupNameIDs(parsed_id) == parsed_groups[1:]
    assert group.value == "control"

    assert api.removeBusDefinitionChoice(parsed_choices[0])
    assert resolve_handle(parsed_choices[0]) is None
    assert resolve_handle(enumeration_id) is None
    assert parsed.choices is None
    assert valid_xml(parsed)
    assert choice.name == "width"


def test_optional_and_required_removal_contracts() -> None:
    item = bus()
    handle = get_handle(item)
    assert api.removeBusDefinitionBroadcast(busDefID=handle) is False
    api.setBusDefinitionBroadcast(handle, True)
    assert api.removeBusDefinitionBroadcast(busDefID=handle) is True
    assert api.getBusDefinitionBroadcast(handle) is False
    for remover in (api.removeBusDefinitionDirectConnection, api.removeBusDefinitionIsAddressable):
        with pytest.raises(TgiError):
            remover(handle)
    assert item.direct_connection is True
    assert item.is_addressable is False
    assert valid_xml(item)


def test_remaining_standard_calls_use_their_annex_argument_contracts() -> None:
    item = bus()
    handle = get_handle(item)
    api.setBusDefinitionDirectConnection(busDefID=handle, value=True)
    api.setBusDefinitionIsAddressable(busDefID=handle, value=True)
    api.setBusDefinitionMaxTargets(busDefID=handle, valueExpression="6 + 2")
    assert api.getBusDefinitionMaxTargetsExpression(handle) == "6 + 2"
    assert api.getBusDefinitionMaxTargets(handle) == 8
    assert api.removeBusDefinitionMaxInitiators(busDefID=handle) is False
    assert api.removeBusDefinitionMaxTargets(busDefID=handle) is True
    assert valid_xml(item)
