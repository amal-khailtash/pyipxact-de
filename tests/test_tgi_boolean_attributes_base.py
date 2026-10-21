"""BASE boolean attributes read generated XML metadata without changing XML."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ComponentPortDirectionType,
    File,
    Initiative,
    PortTransactionalType,
    PortWireType,
    Wire,
)


@pytest.mark.parametrize(
    "name,kind,field,kwargs",
    [
        ("getAllBitsBooleanAttribute", Wire.OnInitiator.Width, "all_bits", {"value": "8"}),
        (
            "getAllLogicalDirectionsAllowedBooleanAttribute",
            PortWireType,
            "all_logical_directions_allowed",
            {"direction": ComponentPortDirectionType.IN},
        ),
        (
            "getAllLogicalInitiativesAllowedBooleanAttribute",
            PortTransactionalType,
            "all_logical_initiatives_allowed",
            {"initiative": Initiative(value="requires")},
        ),
        ("getAppendBooleanAttribute", File.BuildCommand.Flags, "append", {"value": "-O2"}),
        ("getDefaultBooleanAttribute", File.LogicalName, "default", {"value": "logical"}),
    ],
)
@pytest.mark.parametrize("value", [False, True])
def test_boolean_attribute(name, kind, field, kwargs, value):
    obj = kind(**kwargs, **{field: value})
    before = XmlDocument.serializer().render(obj)
    getter = getattr(api, name)
    assert getter(get_handle(obj)) is value
    parsed = XmlDocument.parser().from_string(before, kind)
    assert getter(get_handle(parsed)) is value
    assert XmlDocument.serializer().render(obj) == before
    assert getattr(tgi, name) is getter
    assert list(inspect.signature(getter).parameters) == ["elementID"]
    assert "Section: F.7.43." in getter.__doc__
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")
