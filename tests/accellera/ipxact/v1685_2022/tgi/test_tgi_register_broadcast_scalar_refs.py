"""Broadcast scalar source, choice, wrapper and address-block target getters."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import register
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressBlockRef,
    AddressBlockType,
    AddressUnitBits,
    AlternateRegisterRef,
    BaseAddress,
    Component,
    FieldDefinitions,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    MemoryRemapRef,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)

OWNERS = [
    FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
    FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
]
KINDS = ["AddressBlock", "AddressSpace", "AlternateRegister", "MemoryMap"]
SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("kind", KINDS)
def test_signatures_exports_and_invalid_handles(kind):
    for suffix in ("ByName", "ID"):
        name = f"getBroadcastTo{kind}Ref{suffix}"
        operation = getattr(api, name)
        assert name in register.__all__ and list(inspect.signature(operation).parameters) == ["broadcastToID"]
        for invalid in (None, [], {}, "missing", get_handle(FieldRef(field_ref="wrong"))):
            with pytest.raises(TgiError) as error:
                operation(invalid)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("owner_type", OWNERS)
@pytest.mark.parametrize("kind", KINDS)
def test_optional_sources_and_owned_wrappers_preserve_names_and_containers(owner_type, kind):
    broadcast = owner_type(field_ref=FieldRef(field_ref="target"))
    owner_id = get_handle(broadcast)
    names = getattr(api, f"getBroadcastTo{kind}RefByName")
    ids = getattr(api, f"getBroadcastTo{kind}RefID")
    assert names(owner_id) is None and ids(owner_id) is None
    if kind == "AddressBlock":
        child = AddressBlockRef(address_block_ref=" \tδ_block\n", indices=Indices(index=[Index(value="1")]))
        broadcast.address_block_ref = child
        original = None
    elif kind == "AlternateRegister":
        child = AlternateRegisterRef(alternate_register_ref=" \tδ_alternate\n")
        broadcast.alternate_register_ref = child
        original = None
    else:
        child_type = owner_type.AddressSpaceRef if kind == "AddressSpace" else owner_type.MemoryMapRef
        attribute = "address_space_ref" if kind == "AddressSpace" else "memory_map_ref"
        child = child_type(**{attribute: " \tδ_choice\n"})
        original = (child,)
        broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref = original
    child_id = get_handle(child)
    assert names(owner_id).startswith("δ_")
    if kind == "AddressBlock":
        # Annex/WSDL .13 returns an addressBlock target, so a detached source has none.
        with pytest.raises(TgiError) as error:
            ids(owner_id)
        assert error.value.fault_code == TgiFaultCode.NOT_FOUND
        assert get_parent_info(get_handle(child.indices.index[0])).parent_handle == get_handle(child.indices)
    else:
        assert ids(owner_id) == child_id and resolve_handle(child_id) is child
    assert get_parent_info(child_id).parent_handle == owner_id
    if original is not None:
        assert broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref is original
        assert getattr(child, attribute) == " \tδ_choice\n"
    else:
        attribute = "address_block_ref" if kind == "AddressBlock" else "alternate_register_ref"
    setattr(child, attribute, "bad Name")
    for operation in (names, ids):
        with pytest.raises(TgiError) as error:
            operation(owner_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("owner_type", OWNERS)
@pytest.mark.parametrize("bad", ["wrong", "duplicate", "mixed", "reverse", "remap_only", "foreign"])
def test_reference_choice_rejects_invalid_branches_atomically(owner_type, bad):
    owner = owner_type(field_ref=FieldRef(field_ref="target"))
    address = owner_type.AddressSpaceRef(address_space_ref="space")
    memory_map = owner_type.MemoryMapRef(memory_map_ref="map")
    remap = MemoryRemapRef(memory_remap_ref="remap")
    foreign_type = OWNERS[1] if owner_type is OWNERS[0] else OWNERS[0]
    choices = {
        "wrong": "wrong",
        "duplicate": (memory_map, memory_map),
        "mixed": (address, memory_map),
        "reverse": (remap, memory_map),
        "remap_only": (remap,),
        "foreign": (foreign_type.MemoryMapRef(memory_map_ref="map"),),
    }
    original = choices[bad]
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = original
    for kind in ("AddressSpace", "MemoryMap"):
        for suffix in ("ByName", "ID"):
            with pytest.raises(TgiError) as error:
                getattr(api, f"getBroadcastTo{kind}Ref{suffix}")(get_handle(owner))
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
            assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is original


@pytest.mark.parametrize("owner_type", OWNERS)
def test_memory_map_remap_choice_and_opposite_branch_absence(owner_type):
    child = owner_type.MemoryMapRef(memory_map_ref="map")
    remap = MemoryRemapRef(memory_remap_ref="remap")
    owner = owner_type(
        field_ref=FieldRef(field_ref="target"), address_space_ref_or_memory_map_ref_or_memory_remap_ref=(child, remap)
    )
    original = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    assert api.getBroadcastToMemoryMapRefID(get_handle(owner)) == get_handle(child)
    assert api.getBroadcastToMemoryMapRefByName(get_handle(owner)) == "map"
    assert api.getBroadcastToAddressSpaceRefID(get_handle(owner)) is None
    assert api.getBroadcastToAddressSpaceRefByName(get_handle(owner)) is None
    assert get_parent_info(get_handle(remap)).parent_handle == get_handle(owner)
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is original


@pytest.mark.parametrize("owner_type", OWNERS)
def test_wrong_direct_reference_models_fault(owner_type):
    owner = owner_type(
        field_ref=FieldRef(field_ref="target"),
        address_block_ref=AlternateRegisterRef(alternate_register_ref="wrong"),
        alternate_register_ref=AddressBlockRef(address_block_ref="wrong"),
    )
    for kind in ("AddressBlock", "AlternateRegister"):
        with pytest.raises(TgiError) as error:
            getattr(api, f"getBroadcastTo{kind}RefID")(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def component():
    broadcast = OWNERS[0](
        field_ref=FieldRef(field_ref="target"),
        address_block_ref=AddressBlockRef(address_block_ref="registers"),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref="alternate"),
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=[OWNERS[0].MemoryMapRef(memory_map_ref="map")],
    )
    policy = FieldType.FieldAccessPolicies.FieldAccessPolicy(
        broadcasts=FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts(broadcast_to=[broadcast])
    )
    source = FieldType(
        name="source",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), FieldType.FieldAccessPolicies(field_access_policy=[policy])],
    )
    register_node = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), source],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="16"),
            UnsignedPositiveIntExpression(value="8"),
            UsageType.REGISTER,
            register_node,
        ],
    )
    root = Component(
        vendor="acme",
        library="test",
        name="broadcasts",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )
    return root, broadcast, block


def test_target_address_block_id_schema_round_trip_and_normalized_source():
    root, _broadcast, _block = component()
    xml = XmlDocument.serializer().render(root)
    SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    block = parsed.memory_maps.memory_map[0].choice[0]
    broadcast = block.choice[3].choice[1].choice[1].field_access_policy[0].broadcasts.broadcast_to[0]
    owner_id = get_handle(broadcast)
    broadcast.address_block_ref.address_block_ref = " \tregisters\n"
    broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0].memory_map_ref = " \tmap\n"
    assert api.getBroadcastToAddressBlockRefByName(owner_id) == "registers"
    assert api.getBroadcastToAddressBlockRefID(owner_id) == get_handle(block)
    assert api.getBroadcastToAddressBlockRefID(owner_id) != get_handle(broadcast.address_block_ref)
    assert api.getBroadcastToMemoryMapRefByName(owner_id) == "map"
    assert api.getBroadcastToAlternateRegisterRefByName(owner_id) == "alternate"
    assert api.getBroadcastToAddressSpaceRefID(owner_id) is None
    assert broadcast.address_block_ref.address_block_ref == " \tregisters\n"


@pytest.mark.parametrize(
    "failure,fault", [("missing", TgiFaultCode.NOT_FOUND), ("duplicate", TgiFaultCode.INVALID_ARGUMENT)]
)
def test_address_block_target_missing_and_ambiguity_faults(failure, fault):
    root, broadcast, block = component()
    if failure == "missing":
        broadcast.address_block_ref.address_block_ref = "missing"
    else:
        duplicate = AddressBlock(name="registers", base_address=BaseAddress(value="16"), choice=[])
        root.memory_maps.memory_map[0].choice.append(duplicate)
        source_register = block.choice.pop(3)
        source_block = AddressBlock(
            name="source_block",
            base_address=BaseAddress(value="32"),
            choice=[
                UnsignedPositiveLongintExpression(value="16"),
                UnsignedPositiveIntExpression(value="8"),
                UsageType.REGISTER,
                source_register,
            ],
        )
        root.memory_maps.memory_map[0].choice.append(source_block)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    with pytest.raises(TgiError) as error:
        api.getBroadcastToAddressBlockRefID(get_handle(broadcast))
    assert error.value.fault_code == fault


def test_address_block_target_rejects_malformed_qualifier_and_choice():
    root, broadcast, _block = component()
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0].memory_map_ref = "bad Name"
    with pytest.raises(TgiError) as error:
        api.getBroadcastToAddressBlockRefID(get_handle(broadcast))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref = (
        OWNERS[0].MemoryMapRef(memory_map_ref="map"),
        OWNERS[0].AddressSpaceRef(address_space_ref="space"),
    )
    with pytest.raises(TgiError) as error:
        api.getBroadcastToAddressBlockRefID(get_handle(broadcast))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
