"""CPU Annex signatures, references and atomic expression contracts."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import component, cpu
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from org.accellera.ipxact.v1685_2022 import Component


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _component(name="root"):
    root = Component(vendor="v", library="l", name=name, version="1")
    root_id = get_handle(root)
    map_id = component.addComponentMemoryMap(root_id, "map")
    cpu_id = tgi.addComponentCpu(root_id, "cpu", "map", "4096", "32")
    return root, cpu_id, map_id


_BASE = [
    "getCpuAddressUnitBits",
    "getCpuAddressUnitBitsExpression",
    "getCpuAddressUnitBitsID",
    "getCpuExecutableImageIDs",
    "getCpuMemoryMapRefByID",
    "getCpuMemoryMapRefByName",
    "getCpuRange",
    "getCpuRangeExpression",
    "getCpuRangeID",
    "getCpuRegionIDs",
    "getCpuWidth",
    "getCpuWidthExpression",
    "getCpuWidthID",
]
_EXTENDED = [
    ("addCpuExecutableImage", "cpuID,name,imageId"),
    ("addCpuRegion", "cpuID,name,addressOffset,range"),
    ("removeCpuAddressUnitBits", "cpuID"),
    ("removeCpuExecutableImage", "executableImageID"),
    ("removeCpuRegion", "regionID"),
    ("setCpuAddressUnitBits", "cpuID,addressUnitBits"),
    ("setCpuMemoryMapRef", "cpuID,value"),
    ("setCpuRange", "cpuID,range"),
    ("setCpuWidth", "cpuID,width"),
    ("setRegionAddressOffset", "regionID,addressOffset"),
    ("setRegionRange", "regionID,range"),
]


@pytest.mark.parametrize(
    "name,args,section",
    [
        *[(name, "cpuID", f"F.7.21.{i}") for i, name in enumerate(_BASE, 1)],
        *[(name, args, f"F.7.22.{i}") for i, (name, args) in enumerate(_EXTENDED, 1)],
    ],
)
def test_annex_signatures_exports_and_documentation(name, args, section):
    function = getattr(cpu, name)
    assert list(inspect.signature(function).parameters) == args.split(",")
    assert name in cpu.__all__
    assert getattr(tgi, name) is function
    assert "Args:" in function.__doc__ and "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


def test_memory_map_resolution_uses_owner_and_returns_no_foreign_map():
    root, cpu_id, map_id = _component()
    foreign, _, foreign_map = _component("foreign")
    registry.register(root, ["v", "l", "root", "1"])
    registry.register(foreign, ["v", "l", "foreign", "1"])
    assert cpu.getCpuMemoryMapRefByID(cpu_id) == map_id
    assert cpu.getCpuMemoryMapRefByID(cpu_id) != foreign_map
    assert cpu.getCpuMemoryMapRefByName(cpu_id) == "map"
    assert cpu.setCpuMemoryMapRef(cpu_id, "missing")
    assert cpu.getCpuMemoryMapRefByID(cpu_id) is None


@pytest.mark.parametrize("expression", [None, True, 3, "", "1 +", "8'hxx", "1.5", "bad\x00text", "-1"])
@pytest.mark.parametrize("setter,attribute", [(cpu.setCpuRange, "range"), (cpu.setCpuWidth, "width")])
def test_invalid_expressions_do_not_change_wrappers(setter, attribute, expression):
    _, cpu_id, _ = _component()
    wrapper = getattr(resolve_handle(cpu_id), attribute)
    before = wrapper.value
    with pytest.raises(TgiError):
        setter(cpu_id, expression)
    assert getattr(resolve_handle(cpu_id), attribute) is wrapper
    assert wrapper.value == before


def test_loaded_memory_map_duplicate_is_ambiguous():
    root, cpu_id, _ = _component()
    root.memory_maps.memory_map.append(root.memory_maps.memory_map[0])
    with pytest.raises(TgiError):
        cpu.getCpuMemoryMapRefByID(cpu_id)


def test_region_range_getter_rejects_zero_in_loaded_model():
    _, cpu_id, _ = _component()
    region_id = cpu.addCpuRegion(cpu_id, "region", "0", "1")
    resolve_handle(region_id).range.value = "0"
    with pytest.raises(TgiError):
        cpu.getCpuRegionRange(region_id)
    assert cpu.getCpuRegionAddressOffset(region_id) == 0


def test_tuple_collections_support_owned_removal():
    root, cpu_id, _ = _component()
    region_id = cpu.addCpuRegion(cpu_id, "region", "0", "1")
    image_id = cpu.addCpuExecutableImage(cpu_id, "image", "image-id")
    owner = resolve_handle(cpu_id)
    owner.regions.region = tuple(owner.regions.region)
    owner.executable_image = tuple(owner.executable_image)
    assert cpu.removeCpuRegion(region_id)
    assert owner.regions is None
    assert cpu.removeCpuExecutableImage(image_id)
    assert owner.executable_image == []
    root.cpus.cpu = tuple(root.cpus.cpu)
    assert cpu.removeComponentCpu(cpu_id)
    assert root.cpus is None
