"""CPU region BASE values, source expressions and parsed child ownership."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import address_space as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentType,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("field,name", [("address_offset", "AddressOffset"), ("range", "Range")])
@pytest.mark.parametrize("source,expected", [("0016", 16), ("0x20", 32), ("${SIZE}", None)])
def test_region_base(field, name, source, expected, parsed):
    segment = ComponentType.Cpus.Cpu.Regions.Region(
        name="segment", address_offset=UnsignedLongintExpression(value="0"),
        range=UnsignedPositiveLongintExpression(value="64"),
    )
    getattr(segment, field).value = source
    cpu = ComponentType.Cpus.Cpu(
        name="cpu", memory_map_ref="memory", range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
        regions=ComponentType.Cpus.Cpu.Regions(region=[segment]),
    )
    root = Component(
        vendor="v", library="l", name="c", version="1", cpus=ComponentType.Cpus(cpu=[cpu])
    )
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
        segment = root.cpus.cpu[0].regions.region[0]
    handle = get_handle(segment)
    value, expression, child_id = [getattr(api, f"getRegion{name}{suffix}") for suffix in ("", "Expression", "ID")]
    before = XmlDocument.serializer().render(root)
    assert value(handle) == expected
    assert expression(handle) == source
    child = child_id(handle)
    assert child_id(handle) == child
    assert resolve_handle(child) is getattr(segment, field)
    assert getattr(tgi, f"getRegion{name}") is value
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(child)
    assert resolve_handle(child) is None
    for getter in (value, expression, child_id):
        assert getter(handle) is None
        for invalid in ("missing-region", get_handle(root)):
            with pytest.raises(TgiError):
                getter(invalid)
