"""BASE structured-interface attributes preserve optional booleans and enums."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    BusInterfaceType,
    GroupSelector,
    GroupSelectorMultipleGroupSelectionOperator,
    MonitorInterfaceMode,
    PortStructuredType,
    StructPortTypeDefs,
    SubPortType,
)


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        (
            "getInterfaceModeAttribute",
            BusInterfaceType.Monitor(interface_mode=MonitorInterfaceMode.MIRRORED_TARGET),
            "mirroredTarget",
        ),
        ("getIsIOBooleanAttribute", SubPortType(name="port", is_io=False), False),
        (
            "getMultipleGroupSelectionOperatorAttribute",
            GroupSelector(multiple_group_selection_operator=GroupSelectorMultipleGroupSelectionOperator.AND),
            "and",
        ),
        (
            "getPackedBooleanAttribute",
            PortStructuredType(struct_port_type_defs=StructPortTypeDefs(), packed=False),
            False,
        ),
        ("getPhantomBooleanAttribute", PortStructuredType.Interface(phantom=True), True),
    ],
)
def test_structured_attribute(name, obj, expected):
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) == expected
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == expected
    assert getattr(tgi, name) is getter
    assert XmlDocument.serializer().render(obj) == before
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")


def test_optional_structured_flags():
    assert api.getIsIOBooleanAttribute(get_handle(SubPortType(name="port"))) is None
    assert api.getPhantomBooleanAttribute(get_handle(PortStructuredType.Interface())) is None
    assert (
        api.getPackedBooleanAttribute(get_handle(PortStructuredType(struct_port_type_defs=StructPortTypeDefs())))
        is True
    )
