"""Choice enumeration operations preserve schema values and parent ownership."""

import pytest
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022.tgi import choice as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from org.accellera.ipxact.v1685_2022 import BusDefinition, Choices


def persisted(choice):
    bus = BusDefinition(vendor="acme", library="bus", name="test", version="1",
                        direct_connection=True, is_addressable=False, choices=Choices(choice=[choice]))
    xml = XmlSerializer().render(bus)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    schema.assertValid(etree.fromstring(xml.encode()))
    return XmlParser().from_string(xml, BusDefinition).choices.choice[0]


def test_add_set_expression_and_remove():
    choice = Choices.Choice(name="width")
    handle = get_handle(choice)
    first = api.addChoiceEnumeration(choiceID=handle, name="8")
    second = api.addChoiceEnumeration(choiceID=handle, name="16")
    assert api.getChoiceEnumerationIDs(handle) == [first, second]
    assert [e.value for e in persisted(choice).enumeration] == ["8", "16"]
    assert api.setEnumerationValue(choiceEnumerationID=first, value="WIDTH + 1") is True
    assert api.getEnumerationValueExpression(choiceEnumerationID=first) == "WIDTH + 1"
    assert persisted(choice).enumeration[0].value == "WIDTH + 1"
    assert api.removeChoiceEnumeration(choiceEnumerationID=second) is True
    assert resolve_handle(second) is None
    assert api.getChoiceEnumerationIDs(handle) == [first]
    assert len(persisted(choice).enumeration) == 1


def test_traversal_registers_loaded_enumeration_ownership():
    choice = persisted(Choices.Choice(name="mode", enumeration=[
        Choices.Choice.Enumeration(value="0"), Choices.Choice.Enumeration(value="1")]))
    first, second = api.getChoiceEnumerationIDs(get_handle(choice))
    assert api.removeChoiceEnumeration(first)
    assert resolve_handle(first) is None
    assert api.getChoiceEnumerationIDs(get_handle(choice)) == [second]
    assert persisted(choice).enumeration[0].value == "1"


@pytest.mark.parametrize("operation,args", [
    (api.getChoiceEnumerationIDs, ()),
    (api.getEnumerationValueExpression, ()),
    (api.addChoiceEnumeration, ("1",)),
    (api.removeChoiceEnumeration, ()),
    (api.setEnumerationValue, ("1",)),
])
def test_invalid_handles(operation, args):
    for handle in ["missing", get_handle(object())]:
        with pytest.raises(TgiError) as error:
            operation(handle, *args)
        assert error.value.fault_code == "INVALID_ID"
