"""Bus-definition expression edits preserve XML metadata and owned handles."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import BusDefinition, Choices, Component, UnsignedIntExpression


def _bus():
    return BusDefinition(vendor="v", library="l", name="bus", version="1", direct_connection=True, is_addressable=False)


def _valid(bus):
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    xml = XmlDocument.serializer().render(bus)
    schema.assertValid(etree.fromstring(xml.encode()))
    return xml


@pytest.mark.parametrize("suffix,attribute", [("Initiators", "max_initiators"), ("Targets", "max_targets")])
def test_unsigned_limits_and_expression_identity(suffix, attribute):
    bus = _bus()
    expression = UnsignedIntExpression(value="0", other_attributes={"{urn:test}label": "limit"}, minimum=0)
    setattr(bus, attribute, expression)
    handle = get_handle(bus)
    getter = getattr(api, f"getBusDefinitionMax{suffix}")
    source = getattr(api, f"getBusDefinitionMax{suffix}Expression")
    child_id = getattr(api, f"getBusDefinitionMax{suffix}ID")
    setter = getattr(api, f"setBusDefinitionMax{suffix}")
    original_id = child_id(handle)
    setter(handle, "32'hFFFFFFFF")
    assert getter(handle) == (1 << 32) - 1
    assert source(handle) == "32'hFFFFFFFF"
    assert child_id(handle) == original_id
    assert getattr(bus, attribute) is expression
    assert expression.other_attributes == {"{urn:test}label": "limit"}
    before = _valid(bus)
    for invalid in [str(1 << 32), "-1", "", True]:
        with pytest.raises(TgiError):
            setter(handle, invalid)
        assert _valid(bus) == before
    expression.maximum = 0
    with pytest.raises(TgiError):
        setter(handle, "1")
    setter(handle, "0")
    assert getter(handle) == 0
    assert expression.maximum == 0
    remover = getattr(api, f"removeBusDefinitionMax{suffix}")
    assert remover(handle)
    assert resolve_handle(original_id) is None
    assert getter(handle) is None
    _valid(bus)


def test_parsed_choice_ownership_and_subtree_invalidation():
    bus = _bus()
    api.addBusDefinitionChoice(get_handle(bus), "width", ["8", "16"])
    parsed = XmlDocument.parser().from_string(_valid(bus), BusDefinition)
    choice_id = api.getBusDefinitionChoiceIDs(get_handle(parsed))[0]
    choice = resolve_handle(choice_id)
    enumeration_id = get_handle(choice.enumeration[0])
    assert api.removeBusDefinitionChoice(choice_id)
    assert resolve_handle(choice_id) is None
    assert resolve_handle(enumeration_id) is None
    assert parsed.choices is None
    _valid(parsed)


def test_bus_choice_removal_does_not_detach_another_owner_category():
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import register_parent

    root = Component(vendor="v", library="l", name="component", version="1", choices=Choices())
    choice = Choices.Choice(name="width", enumeration=[Choices.Choice.Enumeration(value="8")])
    root.choices.choice.append(choice)
    register_parent(choice, root, ("choices", "choice"), "list")
    choice_id = get_handle(choice)
    try:
        result = api.removeBusDefinitionChoice(choice_id)
    except TgiError:
        result = False
    assert result is False
    assert resolve_handle(choice_id) is root.choices.choice[0]
