"""CPU TGI edits retain schema types, ownership and XML ordering."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import component as component_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import cpu as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, Design, DesignConfiguration
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.executable_image import ExecutableImage

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_NS = {"i": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"}


@pytest.fixture(autouse=True)
def top_level_registry_only(monkeypatch):
    registry.clear()
    register = registry.register

    def register_document(element, *args, **kwargs):
        assert isinstance(element, (Component, Design, DesignConfiguration))
        return register(element, *args, **kwargs)

    monkeypatch.setattr(registry, "register", register_document)
    yield
    registry.clear()


def _root():
    return Component(vendor="v", library="l", name="component", version="1")


def _with_cpu():
    root = _root()
    component_api.addComponentMemoryMap(get_handle(root), "map")
    cpu_id = component_api.addComponentCpu(get_handle(root), "processor", "map", "4096", "32")
    return root, cpu_id


def _valid(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert parsed == root
    return xml


def test_component_factory_cpu_round_trips_schema_order_and_expression_types():
    root, cpu_id = _with_cpu()
    cpu = resolve_handle(cpu_id)

    region_id = api.addCpuRegion(cpu_id, "boot", "64", "1024")
    image_id = api.addCpuExecutableImage(cpu_id, "firmware", "fw_image")

    assert api.getCpuRegionIDs(cpu_id) == [region_id]
    assert api.getCpuExecutableImageIDs(cpu_id) == [image_id]
    assert isinstance(resolve_handle(region_id), ComponentType.Cpus.Cpu.Regions.Region)
    assert isinstance(resolve_handle(image_id), ExecutableImage)
    xml = _valid(root)
    document = etree.fromstring(xml.encode())
    assert document.xpath("count(i:cpus/i:cpu/i:regions/i:region)", namespaces=_NS) == 1
    assert document.xpath("string(i:cpus/i:cpu/i:executableImage/@imageId)", namespaces=_NS) == "fw_image"
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_cpu = parsed.cpus.cpu[0]
    assert type(parsed_cpu.range).__name__ == "UnsignedPositiveLongintExpression"
    assert type(parsed_cpu.width).__name__ == "UnsignedPositiveIntExpression"
    assert parsed_cpu.regions.region[0].address_offset.value == "64"
    assert parsed_cpu.executable_image[0].image_id == "fw_image"
    assert cpu.name == "processor"


def test_component_cpu_factory_rejects_invalid_xml_names_and_references_atomically():
    root = _root()
    component_api.addComponentMemoryMap(get_handle(root), "map")
    before = _valid(root)
    for name, memory_map_ref in (("bad name", "map"), ("cpu", "bad reference"), ("", "map")):
        with pytest.raises(TgiError):
            component_api.addComponentCpu(get_handle(root), name, memory_map_ref, "16", "8")
        assert _valid(root) == before


def test_cpu_expression_setters_preserve_wrapper_identity_metadata_and_evaluate_sv_constants():
    root, cpu_id = _with_cpu()
    cpu = resolve_handle(cpu_id)
    range_wrapper = cpu.range
    width_wrapper = cpu.width
    range_wrapper.other_attributes = {"{urn:test}marker": "range"}
    width_wrapper.other_attributes = {"{urn:test}marker": "width"}
    range_id = api.getCpuRangeID(cpu_id)
    width_id = api.getCpuWidthID(cpu_id)

    api.setCpuRange(cpu_id, "64'hFFFF_FFFF_FFFF_FFFF")
    api.setCpuWidth(cpu_id, "32'hFFFF_FFFF")
    assert api.getCpuRange(cpu_id) == (1 << 64) - 1
    assert api.getCpuWidth(cpu_id) == (1 << 32) - 1
    assert cpu.range is range_wrapper
    assert cpu.width is width_wrapper
    assert range_wrapper.other_attributes["{urn:test}marker"] == "range"
    assert width_wrapper.other_attributes["{urn:test}marker"] == "width"
    assert api.getCpuRangeID(cpu_id) == range_id
    assert api.getCpuWidthID(cpu_id) == width_id

    api.setCpuRange(cpu_id, "PARAMETERIZED_RANGE")
    assert api.getCpuRangeExpression(cpu_id) == "PARAMETERIZED_RANGE"
    with pytest.raises(TgiError):
        api.getCpuRange(cpu_id)
    _valid(root)


def test_memory_map_reference_setter_validates_names_and_cannot_clear_with_none():
    root, cpu_id = _with_cpu()
    component_api.addComponentMemoryMap(get_handle(root), "other_map")
    before = _valid(root)
    for invalid in ("bad reference", "", None):
        with pytest.raises(TgiError):
            api.setCpuMemoryMapRef(cpu_id, invalid)
        assert _valid(root) == before

    api.setCpuMemoryMapRef(cpu_id, "other_map")
    assert api.getCpuMemoryMapRef(cpu_id) == "other_map"


def test_cpu_numeric_limits_are_checked_without_partial_mutation():
    root, cpu_id = _with_cpu()
    assert api.getCpuAddressUnitBits(cpu_id) == 8
    assert api.getCpuAddressUnitBitsExpression(cpu_id) is None
    assert api.getCpuAddressUnitBitsID(cpu_id) is None
    api.setCpuRange(cpu_id, "64'hFFFF_FFFF_FFFF_FFFF")
    api.setCpuWidth(cpu_id, "32'hFFFF_FFFF")
    api.setCpuAddressUnitBits(cpu_id, "64'hFFFF_FFFF_FFFF_FFFF")
    assert api.getCpuRange(cpu_id) == (1 << 64) - 1
    assert api.getCpuWidth(cpu_id) == (1 << 32) - 1
    assert api.getCpuAddressUnitBits(cpu_id) == (1 << 64) - 1
    before = _valid(root)

    for setter, invalid in (
        (api.setCpuRange, "0"),
        (api.setCpuRange, "64'h1_0000_0000_0000_0000"),
        (api.setCpuRange, "-1"),
        (api.setCpuWidth, "0"),
        (api.setCpuWidth, "32'h1_0000_0000"),
        (api.setCpuWidth, "-1"),
        (api.setCpuAddressUnitBits, "0"),
        (api.setCpuAddressUnitBits, "64'h1_0000_0000_0000_0000"),
        (api.setCpuAddressUnitBits, "-1"),
    ):
        with pytest.raises(TgiError):
            setter(cpu_id, invalid)
        assert _valid(root) == before


def test_address_unit_bits_has_explicit_removal_and_invalidates_its_handle():
    root, cpu_id = _with_cpu()
    cpu = resolve_handle(cpu_id)
    assert api.getCpuAddressUnitBitsID(cpu_id) is None
    api.setCpuAddressUnitBits(cpu_id, "8")
    wrapper = cpu.address_unit_bits
    wrapper.other_attributes = {"{urn:test}marker": "aub"}
    wrapper_id = api.getCpuAddressUnitBitsID(cpu_id)
    api.setCpuAddressUnitBits(cpu_id, "16")
    assert cpu.address_unit_bits is wrapper
    assert wrapper.other_attributes["{urn:test}marker"] == "aub"
    assert api.getCpuAddressUnitBitsID(cpu_id) == wrapper_id
    with pytest.raises(TgiError):
        api.setCpuAddressUnitBits(cpu_id, None)
    assert api.removeCpuAddressUnitBits(cpu_id)
    assert cpu.address_unit_bits is None
    assert resolve_handle(wrapper_id) is None
    assert not api.removeCpuAddressUnitBits(cpu_id)
    _valid(root)


def test_region_and_image_additions_reject_duplicates_and_bad_names_atomically():
    root, cpu_id = _with_cpu()
    first_region = api.addCpuRegion(cpu_id, "boot", "0", "256")
    first_image = api.addCpuExecutableImage(cpu_id, "firmware", "fw_image")
    before = _valid(root)

    for action in (
        lambda: api.addCpuRegion(cpu_id, "boot", "256", "256"),
        lambda: api.addCpuRegion(cpu_id, "bad name", "0", "1"),
        lambda: api.addCpuRegion(cpu_id, "bad-offset", "", "1"),
        lambda: api.addCpuExecutableImage(cpu_id, "firmware", "another_id"),
        lambda: api.addCpuExecutableImage(cpu_id, "another_name", "fw_image"),
        lambda: api.addCpuExecutableImage(cpu_id, "bad name", "another_id"),
    ):
        with pytest.raises(TgiError):
            action()
        assert _valid(root) == before

    assert resolve_handle(first_region) is not None
    assert resolve_handle(first_image) is not None

    other_cpu_id = component_api.addComponentCpu(get_handle(root), "second_cpu", "map", "512", "32")
    before_global_duplicates = _valid(root)
    with pytest.raises(TgiError):
        api.addCpuExecutableImage(other_cpu_id, "firmware", "third_id")
    with pytest.raises(TgiError):
        api.addCpuExecutableImage(other_cpu_id, "other_firmware", "fw_image")
    assert _valid(root) == before_global_duplicates


def test_symbolic_region_expressions_and_setters_keep_schema_wrappers():
    root, cpu_id = _with_cpu()
    region_id = api.addCpuRegion(cpu_id, "window", "BASE_ADDRESS + 'h40", "WINDOW_SIZE")
    region = resolve_handle(region_id)
    offset_wrapper = region.address_offset
    range_wrapper = region.range
    offset_wrapper.other_attributes = {"{urn:test}marker": "offset"}
    range_wrapper.other_attributes = {"{urn:test}marker": "range"}
    offset_id = api.getCpuRegionAddressOffsetID(region_id)
    range_id = api.getCpuRegionRangeID(region_id)

    with pytest.raises(TgiError):
        api.getCpuRegionAddressOffset(region_id)
    with pytest.raises(TgiError):
        api.getCpuRegionRange(region_id)
    api.setRegionAddressOffset(region_id, "32'h80")
    api.setRegionRange(region_id, "64")
    assert api.getCpuRegionAddressOffset(region_id) == 128
    assert api.getCpuRegionRange(region_id) == 64
    api.setRegionAddressOffset(region_id, "BASE_ADDRESS + 'h80")
    api.setRegionRange(region_id, "2 * WINDOW_SIZE")
    assert region.address_offset is offset_wrapper
    assert region.range is range_wrapper
    assert offset_wrapper.other_attributes["{urn:test}marker"] == "offset"
    assert range_wrapper.other_attributes["{urn:test}marker"] == "range"
    assert api.getCpuRegionAddressOffsetID(region_id) == offset_id
    assert api.getCpuRegionRangeID(region_id) == range_id
    assert api.getCpuRegionAddressOffsetExpression(region_id) == "BASE_ADDRESS + 'h80"
    assert api.getCpuRegionRangeExpression(region_id) == "2 * WINDOW_SIZE"
    with pytest.raises(TgiError):
        api.setRegionAddressOffset(region_id, None)
    with pytest.raises(TgiError):
        api.setRegionRange(region_id, None)
    _valid(root)


def test_tuple_backed_collections_are_normalized_before_appending():
    root, cpu_id = _with_cpu()
    cpu = resolve_handle(cpu_id)
    first_region = api.addCpuRegion(cpu_id, "first", "0", "32")
    cpu.regions.region = tuple(cpu.regions.region)
    second_region = api.addCpuRegion(cpu_id, "second", "32", "32")
    assert isinstance(cpu.regions.region, list)
    assert api.getCpuRegionIDs(cpu_id) == [first_region, second_region]

    first_image = api.addCpuExecutableImage(cpu_id, "first_image", "image_one")
    cpu.executable_image = tuple(cpu.executable_image)
    second_image = api.addCpuExecutableImage(cpu_id, "second_image", "image_two")
    assert isinstance(cpu.executable_image, list)
    assert api.getCpuExecutableImageIDs(cpu_id) == [first_image, second_image]
    other_cpu_id = component_api.addComponentCpu(get_handle(root), "other_cpu", "map", "512", "32")
    other_region_id = api.addCpuRegion(other_cpu_id, "first", "0", "32")
    assert api.getCpuRegionIDs(other_cpu_id) == [other_region_id]
    _valid(root)


def test_region_removal_uses_parsed_owner_prunes_container_and_invalidates_descendants():
    root, cpu_id = _with_cpu()
    region_id = api.addCpuRegion(cpu_id, "only_region", "0", "32")
    image_handle = api.addCpuExecutableImage(cpu_id, "only_image", "image_one")
    xml = _valid(root)
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, ["v", "l", "component", "1"])
    parsed_cpu = parsed.cpus.cpu[0]
    parsed_cpu_id = get_handle(parsed_cpu)

    parsed_region_id = api.getCpuRegionIDs(parsed_cpu_id)[0]
    parsed_region = resolve_handle(parsed_region_id)
    offset_id = api.getCpuRegionAddressOffsetID(parsed_region_id)
    range_id = api.getCpuRegionRangeID(parsed_region_id)
    assert api.removeCpuRegion(parsed_region_id)
    assert parsed_cpu.regions is None
    for handle in (parsed_region_id, offset_id, range_id):
        assert resolve_handle(handle) is None

    parsed_image_id = api.getCpuExecutableImageIDs(parsed_cpu_id)[0]
    parsed_image = resolve_handle(parsed_image_id)
    assert api.removeCpuExecutableImage(parsed_image_id)
    assert parsed_cpu.executable_image == []
    assert resolve_handle(parsed_image_id) is None
    _valid(parsed)
    assert resolve_handle(region_id) is not None
    assert resolve_handle(image_handle) is not None
    assert parsed_region is not None and parsed_image is not None


def test_parsed_cpu_removal_recovers_registered_component_owner_and_invalidates_tree():
    root, cpu_id = _with_cpu()
    api.addCpuRegion(cpu_id, "region", "16", "64")
    api.addCpuExecutableImage(cpu_id, "image", "firmware")
    xml = _valid(root)
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, ["v", "l", "component", "1"])
    cpu = parsed.cpus.cpu[0]
    parsed_cpu_id = get_handle(cpu)
    region_id = api.getCpuRegionIDs(parsed_cpu_id)[0]
    offset_id = api.getCpuRegionAddressOffsetID(region_id)
    range_id = api.getCpuRegionRangeID(region_id)
    image_id = api.getCpuExecutableImageIDs(parsed_cpu_id)[0]
    range_cpu_id = api.getCpuRangeID(parsed_cpu_id)
    width_cpu_id = api.getCpuWidthID(parsed_cpu_id)

    assert api.removeComponentCpu(parsed_cpu_id)
    assert parsed.cpus is None
    for handle in (parsed_cpu_id, region_id, offset_id, range_id, image_id, range_cpu_id, width_cpu_id):
        assert resolve_handle(handle) is None
    _valid(parsed)
