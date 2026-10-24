"""Choice TGI contracts work on schema-parsed IP-XACT documents."""

import pytest
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import choice as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from org.accellera.ipxact.v1685_2022 import BusDefinition, Choices

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


def _parsed_bus_definition() -> BusDefinition:
    source = BusDefinition(
        vendor="acme",
        library="bus",
        name="choice-test",
        version="1",
        direct_connection=True,
        is_addressable=False,
        choices=Choices(
            choice=[
                Choices.Choice(
                    name="mode",
                    enumeration=[
                        Choices.Choice.Enumeration(value="0", text="Disabled"),
                        Choices.Choice.Enumeration(value="1 + 2", help="Computed selection"),
                    ],
                )
            ]
        ),
    )
    xml = XmlSerializer().render(source)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    return XmlParser().from_string(xml, BusDefinition)


def _assert_schema_valid(root: BusDefinition) -> str:
    xml = XmlSerializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    return xml


def test_choice_value_contracts_and_schema_valid_edits_on_parsed_document():
    root = _parsed_bus_definition()
    choice = root.choices.choice[0]
    choice_id = get_handle(choice)

    enumeration_ids = tgi.getChoiceEnumerationIDs(choice_id)
    assert [tgi.getEnumerationValue(handle) for handle in enumeration_ids] == ["0", "1 + 2"]
    assert [tgi.getEnumerationValueExpression(handle) for handle in enumeration_ids] == ["0", "1 + 2"]
    assert tgi.getEnumerationValue(enumeration_ids[1]) == "1 + 2"

    assert tgi.setEnumerationValue(enumeration_ids[1], "MODE + 1") is True
    added_id = tgi.addChoiceEnumeration(choice_id, "4")
    assert tgi.getEnumerationValue(added_id) == "4"
    assert [item.value for item in choice.enumeration] == ["0", "MODE + 1", "4"]

    xml = _assert_schema_valid(root)
    reparsed = XmlParser().from_string(xml, BusDefinition)
    assert [item.value for item in reparsed.choices.choice[0].enumeration] == ["0", "MODE + 1", "4"]


def test_parsed_enumeration_removal_drops_ownership_and_invalidates_handle():
    root = _parsed_bus_definition()
    choice_id = get_handle(root.choices.choice[0])
    first_id, second_id = api.getChoiceEnumerationIDs(choice_id)

    assert api.removeChoiceEnumeration(first_id) is True
    assert resolve_handle(first_id) is None
    assert resolve_handle(second_id) is not None
    assert api.getChoiceEnumerationIDs(choice_id) == [second_id]
    assert [item.value for item in root.choices.choice[0].enumeration] == ["1 + 2"]
    _assert_schema_valid(root)

    with pytest.raises(TgiError) as error:
        api.setEnumerationValue(first_id, "stale")
    assert error.value.fault_code == "INVALID_ID"


@pytest.mark.parametrize("bad_value", [None, 1, object()])
def test_invalid_values_leave_choice_unchanged(bad_value):
    root = _parsed_bus_definition()
    choice = root.choices.choice[0]
    choice_id = get_handle(choice)
    enum_id = api.getChoiceEnumerationIDs(choice_id)[0]
    before = [item.value for item in choice.enumeration]

    with pytest.raises(TgiError) as add_error:
        api.addChoiceEnumeration(choice_id, bad_value)
    assert add_error.value.fault_code == "INVALID_ARGUMENT"
    assert [item.value for item in choice.enumeration] == before

    with pytest.raises(TgiError) as set_error:
        api.setEnumerationValue(enum_id, bad_value)
    assert set_error.value.fault_code == "INVALID_ARGUMENT"
    assert [item.value for item in choice.enumeration] == before
    _assert_schema_valid(root)


def test_choice_functions_reject_handles_of_the_wrong_schema_type():
    choice = Choices.Choice(name="standalone", enumeration=[Choices.Choice.Enumeration(value="1")])
    choice_id = get_handle(choice)
    enum_id = api.getChoiceEnumerationIDs(choice_id)[0]

    for operation, handle in (
        (api.getChoiceEnumerationIDs, enum_id),
        (api.addChoiceEnumeration, enum_id),
        (api.getEnumerationValue, choice_id),
        (api.getEnumerationValueExpression, choice_id),
        (api.removeChoiceEnumeration, choice_id),
        (api.setEnumerationValue, choice_id),
    ):
        args = (handle, "2") if operation in (api.addChoiceEnumeration, api.setEnumerationValue) else (handle,)
        with pytest.raises(TgiError) as error:
            operation(*args)
        assert error.value.fault_code == "INVALID_ID"
