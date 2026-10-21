"""CPU BASE source expressions preserve lexical values and ownership."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import cpu as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressUnitBits,
    Component,
    ComponentType,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)


@pytest.mark.parametrize("name", ["Range", "Width", "AddressUnitBits"])
@pytest.mark.parametrize("parsed", [False, True])
def test_cpu_source_and_handle(name, parsed):
    child = ComponentType.Cpus.Cpu(
        name="cpu",
        range=UnsignedPositiveLongintExpression(value="${RANGE}"),
        width=UnsignedPositiveIntExpression(value="32"),
        address_unit_bits=AddressUnitBits(value="8"),
        memory_map_ref="memory",
    )
    root = Component(vendor="v", library="l", name="c", version="1", cpus=ComponentType.Cpus(cpu=[child]))
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
        child = root.cpus.cpu[0]
    handle = get_handle(child)
    getter = getattr(api, f"getCpu{name}Expression")
    ids = getattr(api, f"getCpu{name}ID")
    expected = {"Range": "${RANGE}", "Width": "32", "AddressUnitBits": "8"}[name]
    before = XmlDocument.serializer().render(root)
    assert getter(handle) == expected
    child_id = ids(handle)
    assert ids(handle) == child_id
    assert resolve_handle(child_id).value == expected
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(child_id)
    assert resolve_handle(child_id) is None
    assert getter(handle) is None
    assert ids(handle) is None
    for op in (getter, ids):
        with pytest.raises(TgiError):
            op("missing-cpu")
