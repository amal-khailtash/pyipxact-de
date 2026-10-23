"""BASE access/build boolean flags retain true/false values in generated XML."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockType,
    BaseAddress,
    FileSetType,
    GeneratorChain,
    Payload,
    PortAccessHandle,
    PortSlicesType,
)


@pytest.mark.parametrize(
    "name,kind,field,kwargs",
    [
        ("getForceBooleanAttribute", PortAccessHandle, "force", {"slices": PortSlicesType()}),
        ("getMandatoryBooleanAttribute", Payload.Extension, "mandatory", {"value": "extension"}),
        (
            "getMisalignmentAllowedBooleanAttribute",
            AddressBlockType,
            "misalignment_allowed",
            {"name": "block", "base_address": BaseAddress(value="0")},
        ),
        ("getReplicateBooleanAttribute", FileSetType.Function, "replicate", {"file_ref": "source"}),
        ("getUniqueBooleanAttribute", GeneratorChain.GeneratorChainSelector, "unique", {}),
    ],
)
@pytest.mark.parametrize("value", [False, True])
def test_access_boolean(name, kind, field, kwargs, value):
    obj = kind(**kwargs, **{field: value})
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) is value
    parsed = XmlDocument.parser().from_string(before, kind)
    assert getter(get_handle(parsed)) is value
    assert XmlDocument.serializer().render(obj) == before
    assert getattr(tgi, name) is getter
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")
