"""CPU and transport BASE child traversal restores parsed ownership."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import cpu, generator
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentType,
    ExecutableImage,
    Generator,
    GeneratorType,
    IpxactUri,
    TransportMethodType,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)


@pytest.mark.parametrize("parsed", [False, True])
def test_cpu_children(parsed):
    c = ComponentType.Cpus.Cpu(
        name="cpu",
        memory_map_ref="memory",
        range=UnsignedPositiveLongintExpression(value="1024"),
        width=UnsignedPositiveIntExpression(value="32"),
        executable_image=[ExecutableImage(name="image", image_id="image")],
        regions=ComponentType.Cpus.Cpu.Regions(
            region=[
                ComponentType.Cpus.Cpu.Regions.Region(
                    name="region",
                    address_offset=UnsignedLongintExpression(value="0"),
                    range=UnsignedPositiveLongintExpression(value="256"),
                )
            ]
        ),
    )
    root = Component(vendor="v", library="l", name="c", version="1", cpus=ComponentType.Cpus(cpu=[c]))
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
        c = root.cpus.cpu[0]
    handle = get_handle(c)
    assert cpu.getCpuMemoryMapRefByName(handle) == "memory"
    images = cpu.getCpuExecutableImageIDs(handle)
    regions = cpu.getCpuRegionIDs(handle)
    assert resolve_handle(images[0]).image_id == "image"
    assert resolve_handle(regions[0]).name == "region"
    for h in [images[0], regions[0]]:
        assert detach_child_by_handle(h)
    assert cpu.getCpuExecutableImageIDs(handle) == []
    assert cpu.getCpuRegionIDs(handle) == []


@pytest.mark.parametrize("parsed", [False, True])
def test_transport_children(parsed):
    g = Generator(
        name="gen",
        generator_exe=IpxactUri(value="gen"),
        transport_methods=GeneratorType.TransportMethods(
            transport_method=GeneratorType.TransportMethods.TransportMethod(value=TransportMethodType.FILE)
        ),
    )
    if parsed:
        g = XmlDocument.parser().from_string(XmlDocument.serializer().render(g), Generator)
    handle = get_handle(g)
    tm = generator.getGeneratorTransportMethodsID(handle)
    method = generator.getTransportMethodsTransportMethodID(tm)
    assert resolve_handle(method).value is TransportMethodType.FILE
    assert generator.getGeneratorTransportMethodsID(handle) == tm
    assert detach_child_by_handle(tm)
    assert resolve_handle(method) is None
    assert generator.getGeneratorTransportMethodsID(handle) is None


def test_wrong_handles():
    for f in [
        cpu.getCpuExecutableImageIDs,
        cpu.getCpuMemoryMapRefByName,
        cpu.getCpuRegionIDs,
        generator.getGeneratorTransportMethodsID,
        generator.getTransportMethodsTransportMethodID,
    ]:
        with pytest.raises(TgiError):
            f("missing-base-owner")
