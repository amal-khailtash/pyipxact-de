"""Direct coverage for all IEEE 1685-2022 F.7.11/F.7.12 address-space calls."""


from uuid import uuid4

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import address_space as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressSpaces,
    AddressUnitBits,
    Component,
    ComponentType,
    ExecutableImage,
    FieldRef,
    FieldType,
    LocalMemoryMapType,
    StringExpression,
    UnsignedBitExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.bank_alignment_type import BankAlignmentType
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.generator_ref import GeneratorRef
from org.accellera.ipxact.v1685_2022.linker_command_file import LinkerCommandFile
from org.accellera.ipxact.v1685_2022.local_address_bank_type import LocalAddressBankType


def _block(name: str = "block") -> AddressBlock:
    return AddressBlock(
        name=name,
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="64"), UnsignedPositiveIntExpression(value="32")],
    )


def _models():
    segment = AddressSpaces.AddressSpace.Segments.Segment(
        name="segment",
        address_offset=UnsignedLongintExpression(value="0016"),
        range=UnsignedPositiveLongintExpression(value="${SEGMENT_SIZE}"),
    )
    bank = LocalAddressBankType(
        name="bank",
        base_address=BaseAddress(value="0"),
        bank_alignment=BankAlignmentType.SERIAL,
    )
    local_map = LocalMemoryMapType(name="local", address_block_or_bank=[_block(), bank])
    address_space = AddressSpaces.AddressSpace(
        name="space",
        range=UnsignedPositiveLongintExpression(value="4*1024"),
        width=UnsignedPositiveIntExpression(value="8*4"),
        segments=AddressSpaces.AddressSpace.Segments(segment=[segment]),
        address_unit_bits=AddressUnitBits(value="1+7"),
        local_memory_map=local_map,
    )
    alias = FieldType.AliasOf(
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=[
            FieldType.AliasOf.AddressSpaceRef(address_space_ref="space")
        ],
        field_ref=FieldRef(field_ref="target"),
    )
    linker_file = LinkerCommandFile(
        name=StringExpression(value="link.ld"),
        command_line_switch=StringExpression(value="-T"),
        enable=UnsignedBitExpression(value="1"),
        generator_ref=[GeneratorRef(value="linker")],
    )
    image = ExecutableImage(
        name="image",
        image_id="image-id",
        file_set_ref_group=ExecutableImage.FileSetRefGroup(file_set_ref=[]),
        language_tools=ExecutableImage.LanguageTools(linker_flags_or_linker_command_file=[linker_file]),
    )
    region = ComponentType.Cpus.Cpu.Regions.Region(
        name="region",
        address_offset=UnsignedLongintExpression(value="0x20"),
        range=UnsignedPositiveLongintExpression(value="0016"),
    )
    cpu = ComponentType.Cpus.Cpu(
        name="cpu",
        range=UnsignedPositiveLongintExpression(value="4096"),
        width=UnsignedPositiveIntExpression(value="32"),
        memory_map_ref="memory",
        regions=ComponentType.Cpus.Cpu.Regions(region=[region]),
        executable_image=[image],
    )
    component = Component(
        vendor="example.org",
        library="test",
        name="address-space-test",
        version="1.0",
        address_spaces=AddressSpaces(address_space=[address_space]),
        cpus=ComponentType.Cpus(cpu=[cpu]),
    )
    return component, address_space, local_map, segment, bank, region, alias, image, linker_file


@pytest.fixture
def model_tree():
    component, *objects = _models()
    component = XmlDocument.parser().from_string(XmlDocument.serializer().render(component), Component)
    address_space = component.address_spaces.address_space[0]
    local_map = address_space.local_memory_map
    segment = address_space.segments.segment[0]
    cpu = component.cpus.cpu[0]
    region = cpu.regions.region[0]
    image = cpu.executable_image[0]
    linker_file = image.language_tools.linker_flags_or_linker_command_file[0]
    bank = next(child for child in local_map.address_block_or_bank if isinstance(child, LocalAddressBankType))
    _component, _space, _map, _segment, _bank, _region, alias, _image, _linker_file = _models()
    objects = [address_space, local_map, segment, bank, region, alias, image, linker_file]
    vlnv = ("test", "address-space", str(uuid4()), "1")
    registry.register(component, vlnv, element_type="Component")
    try:
        yield component, *objects
    finally:
        registry.unregister(vlnv)


def test_all_address_space_base_calls(model_tree):
    component, address_space, local_map, segment, _bank, region, alias, _image, _linker_file = model_tree
    address_space_id = get_handle(address_space)
    segment_id = get_handle(segment)
    region_id = get_handle(region)
    alias_id = get_handle(alias)

    assert api.getAddressSpaceAddressUnitBits(address_space_id) == 8
    assert api.getAddressSpaceAddressUnitBitsExpression(address_space_id) == "1+7"
    address_unit_bits_id = api.getAddressSpaceAddressUnitBitsID(address_space_id)
    assert resolve_handle(address_unit_bits_id).value == "1+7"
    assert api.getAddressSpaceLocalMemoryMapID(address_space_id) == get_handle(local_map)
    assert api.getAddressSpaceRange(address_space_id) == 4096
    assert api.getAddressSpaceRangeExpression(address_space_id) == "4*1024"
    range_id = api.getAddressSpaceRangeID(address_space_id)
    assert resolve_handle(range_id).value == "4*1024"
    assert api.getAddressSpaceSegmentIDs(address_space_id) == [segment_id]
    assert api.getAddressSpaceWidth(address_space_id) == 32
    assert api.getAddressSpaceWidthExpression(address_space_id) == "8*4"
    width_id = api.getAddressSpaceWidthID(address_space_id)
    assert resolve_handle(width_id).value == "8*4"
    assert api.getAliasOfAddressSpaceRefByName(alias_id) == "space"
    alias_ref_id = api.getAliasOfAddressSpaceRefID(alias_id)
    assert resolve_handle(alias_ref_id).address_space_ref == "space"
    assert api.getLocalMemoryMapAddressBlockIDs(address_space_id) == [
        get_handle(local_map.address_block_or_bank[0])
    ]
    assert api.getLocalMemoryMapBankIDs(address_space_id) == [get_handle(local_map.address_block_or_bank[1])]

    assert api.getRegionAddressOffset(region_id) == 32
    assert api.getRegionAddressOffsetExpression(region_id) == "0x20"
    region_offset_id = api.getRegionAddressOffsetID(region_id)
    assert resolve_handle(region_offset_id).value == "0x20"
    assert api.getRegionRange(region_id) == 16
    assert api.getRegionRangeExpression(region_id) == "0016"
    region_range_id = api.getRegionRangeID(region_id)
    assert resolve_handle(region_range_id).value == "0016"
    assert api.getSegmentAddressOffset(segment_id) == 16
    assert api.getSegmentAddressOffsetExpression(segment_id) == "0016"
    segment_offset_id = api.getSegmentAddressOffsetID(segment_id)
    assert resolve_handle(segment_offset_id).value == "0016"
    assert api.getSegmentRange(segment_id) is None
    assert api.getSegmentRangeExpression(segment_id) == "${SEGMENT_SIZE}"
    segment_range_id = api.getSegmentRangeID(segment_id)
    assert resolve_handle(segment_range_id).value == "${SEGMENT_SIZE}"

    with pytest.raises(TgiError):
        api.getAddressSpaceRange("not-a-handle")
    with pytest.raises(TgiError):
        api.getAliasOfAddressSpaceRefByName(address_space_id)
    assert component.address_spaces.address_space[0] is address_space


def test_all_address_space_extended_calls_and_owned_removal(model_tree):
    component, address_space, local_map, segment, bank, _region, _alias, image, linker_file = model_tree
    address_space_id = get_handle(address_space)
    local_map_id = get_handle(local_map)

    added_segment_id = api.addAddressSpaceSegment(address_space_id, "added", "32+8", "64*2")
    assert resolve_handle(added_segment_id) is not None
    assert api.getSegmentAddressOffset(added_segment_id) == 40
    assert api.getSegmentRange(added_segment_id) == 128
    assert api.removeAddressSpaceSegment(added_segment_id)
    assert resolve_handle(added_segment_id) is None

    file_set_ref_id = api.addExecutableImageFileSetRef(get_handle(image), "software")
    file_set_ref = resolve_handle(file_set_ref_id)
    assert file_set_ref.local_name == "software"
    assert api.removeExecutableImageFileSetRef(file_set_ref_id)
    assert resolve_handle(file_set_ref_id) is None

    block_id = api.addLocalMemoryMapAddressBlock(local_map_id, "added-block", "0x100", "256", "32")
    block = resolve_handle(block_id)
    assert block.base_address.value == "0x100"
    assert [item.value for item in block.choice] == ["256", "32"]
    assert api.removeLocalMemoryMapAddressBlock(block_id)
    assert resolve_handle(block_id) is None
    bank_id = get_handle(bank)
    assert api.removeLocalMemoryMapBank(bank_id)
    assert resolve_handle(bank_id) is None

    unit_bits_id = api.getAddressSpaceAddressUnitBitsID(address_space_id)
    assert api.removeAddressSpaceAddressUnitBits(address_space_id)
    assert resolve_handle(unit_bits_id) is None
    assert not api.removeAddressSpaceAddressUnitBits(address_space_id)

    generator_ref = linker_file.generator_ref[0]
    generator_ref_id = get_handle(generator_ref)
    assert api.removeLinkerCommandFileGenerator(generator_ref_id)
    assert resolve_handle(generator_ref_id) is None

    assert api.setAddressSpaceAddressUnitBits(address_space_id, "2**3")
    aub = address_space.address_unit_bits
    aub_id = get_handle(aub)
    assert type(aub) is AddressUnitBits
    assert api.setAddressSpaceAddressUnitBits(address_space_id, "8")
    assert address_space.address_unit_bits is aub
    assert get_handle(address_space.address_unit_bits) == aub_id
    assert api.getAddressSpaceAddressUnitBits(address_space_id) == 8
    assert api.setAddressSpaceRange(address_space_id, "2**12")
    range_obj = address_space.range
    assert api.getAddressSpaceRange(address_space_id) == 4096
    width_obj = address_space.width
    width_id = get_handle(width_obj)
    assert api.setAddressSpaceWidth(address_space_id, "16*2")
    assert address_space.width is width_obj
    assert get_handle(address_space.width) == width_id
    assert api.getAddressSpaceWidth(address_space_id) == 32

    segment_id = api.addAddressSpaceSegment(address_space_id, "setter-segment", "0", "1")
    offset_obj = resolve_handle(api.getSegmentAddressOffsetID(segment_id))
    range_obj = resolve_handle(api.getSegmentRangeID(segment_id))
    assert api.setSegmentAddressOffset(segment_id, "4*4")
    assert resolve_handle(api.getSegmentAddressOffsetID(segment_id)) is offset_obj
    assert api.getSegmentAddressOffset(segment_id) == 16
    assert api.setSegmentRange(segment_id, "2**8")
    assert resolve_handle(api.getSegmentRangeID(segment_id)) is range_obj
    assert api.getSegmentRange(segment_id) == 256

    with pytest.raises(TgiError):
        api.setAddressSpaceWidth(address_space_id, "0")
    assert address_space.width is width_obj
    with pytest.raises(TgiError):
        api.setSegmentRange(segment_id, True)
    assert resolve_handle(api.getSegmentRangeID(segment_id)) is range_obj
    assert resolve_handle(aub_id) is aub

    old_block_id = api.addLocalMemoryMapAddressBlock(local_map_id, "replace-me", "0", "1", "8")
    map_id = api.getAddressSpaceLocalMemoryMapID(address_space_id)
    assert api.setAddressSpaceLocalMemoryMap(address_space_id, "local2", "default", "0x1000", "0x100", "32")
    assert api.getAddressSpaceLocalMemoryMapID(address_space_id) == map_id
    assert resolve_handle(old_block_id) is None
    assert local_map.name == "local2"
    assert api.getLocalMemoryMapAddressBlockIDs(address_space_id)
    assert len(local_map.address_block_or_bank) == 1
    assert api.removeAddressSpaceLocalMemoryMap(address_space_id)
    assert resolve_handle(map_id) is None
    assert not api.removeAddressSpaceLocalMemoryMap(address_space_id)
    assert api.removeAddressSpaceSegment(segment_id)
    assert resolve_handle(segment_id) is None
    assert component.address_spaces.address_space[0] is address_space
