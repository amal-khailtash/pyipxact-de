"""Removals of inline children owned by IEEE 1685-2022 memoryRemaps."""

from inspect import signature

import pytest
from lxml import etree
from xsdata.formats.dataclass.models.generics import AnyElement

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map as memory_map_api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AccessPolicies,
    AccessType,
    AddressBlock,
    AddressSpaces,
    AddressUnitBits,
    Bank,
    BankAlignmentType,
    BankedBankType,
    BankedBlockType,
    BankedSubspaceType,
    BaseAddress,
    BusInterface,
    BusInterfaces,
    BusInterfaceType,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    LocalMemoryMapType,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapType,
    ModeRef,
    SharedType,
    SignedLongintExpression,
    SubspaceMap,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
    VendorExtensions,
    Volatile,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_REMOVERS = (
    ("removeMemoryRemapBank", "bankID", Bank),
    ("removeMemoryRemapMapAddressBlock", "addressBlockID", AddressBlock),
    ("removeMemoryRemapSubspaceMap", "subspaceMapID", SubspaceMap),
)


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def block(name: str) -> AddressBlock:
    return AddressBlock(
        name=name,
        base_address=BaseAddress(value="0"),
        choice=(UnsignedPositiveLongintExpression(value="32"), UnsignedPositiveIntExpression(value="32")),
    )


def bank(name: str) -> Bank:
    nested_block = BankedBlockType(
        name=f"{name}-block",
        range=UnsignedPositiveLongintExpression(value="8"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    return Bank(
        name=name,
        base_address=BaseAddress(value="0"),
        bank_alignment=BankAlignmentType.SERIAL,
        choice=(nested_block,),
    )


def subspace(name: str) -> SubspaceMap:
    return SubspaceMap(name=name, base_address=SignedLongintExpression(value="-4"), initiator_ref="bus")


def component_with_map(memory_map: MemoryMapType) -> Component:
    return Component(
        vendor="test",
        library="memory",
        name="remap_removal",
        version="1",
        memory_maps=MemoryMaps(memory_map=[memory_map]),
        bus_interfaces=BusInterfaces(
            bus_interface=[
                BusInterface(
                    name="bus",
                    bus_type=ConfigurableLibraryRefType(vendor="test", library="bus", name="bus", version="1"),
                    choice=BusInterfaceType.Initiator(),
                )
            ]
        ),
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")]),
    )


def assert_invalid_id(operation, handle) -> None:
    with pytest.raises(TgiError) as error:
        operation(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def assert_schema_valid(root: Component) -> None:
    xml = XmlDocument.serializer().render(root)
    parsed = etree.fromstring(xml.encode())
    assert SCHEMA.validate(parsed), SCHEMA.error_log
    reparsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(reparsed)


def test_exact_exports_signatures_and_invalid_handles() -> None:
    expected = {
        "removeMemoryRemapBank": ["bankID"],
        "removeMemoryRemapMapAddressBlock": ["addressBlockID"],
        "removeMemoryRemapSubspaceMap": ["subspaceMapID"],
    }
    for name, parameters in expected.items():
        operation = getattr(api, name)
        assert name in memory_map_api.__all__ and name in api.__all__
        assert list(signature(operation).parameters) == parameters
        for invalid in ("unknown-remap-child", None, [], {}, 7):
            assert_invalid_id(operation, invalid)


@pytest.mark.parametrize("name,parameter,model_type", _REMOVERS)
def test_direct_registered_parent_link_removes_each_inline_child_without_a_root(name, parameter, model_type) -> None:
    operation = getattr(api, name)
    child = {
        AddressBlock: lambda: block("removed-block"),
        Bank: lambda: bank("removed-bank"),
        SubspaceMap: lambda: subspace("removed-subspace"),
    }[model_type]()
    sibling = block("sibling")
    mode_ref = ModeRef(value="active", priority=0)
    remap = MemoryRemap(name="window", mode_ref=(mode_ref,), choice=(child, sibling), id="remap-id")
    remap_id = get_handle(remap)
    child_id = get_handle(child)
    sibling_id = get_handle(sibling)
    mode_ref_id = get_handle(mode_ref)
    register_parent(child, remap, ("choice",), "list")

    assert operation(**{parameter: child_id}) is True

    assert remap.choice == [sibling]
    assert resolve_handle(remap_id) is remap
    assert resolve_handle(child_id) is None
    assert resolve_handle(sibling_id) is sibling
    assert resolve_handle(mode_ref_id) is mode_ref
    assert remap.name == "window" and remap.id == "remap-id" and remap.mode_ref == (mode_ref,)
    assert_invalid_id(operation, child_id)


@pytest.mark.parametrize("name,parameter,model_type", _REMOVERS)
def test_parsed_registered_root_removal_normalizes_only_choice_and_preserves_remap_metadata(
    name, parameter, model_type
) -> None:
    operation = getattr(api, name)
    removed = {
        AddressBlock: lambda: block("removed-block"),
        Bank: lambda: bank("removed-bank"),
        SubspaceMap: lambda: subspace("removed-subspace"),
    }[model_type]()
    survivor = {
        AddressBlock: lambda: bank("survivor-bank"),
        Bank: lambda: block("survivor-block"),
        SubspaceMap: lambda: block("survivor-block"),
    }[model_type]()
    mode_refs = (ModeRef(value="active", priority=0),)
    extensions = VendorExtensions(any_element=[AnyElement(qname="{urn:test}remap", text="metadata")])
    remap = MemoryRemap(
        name="window", mode_ref=mode_refs, choice=(removed, survivor), vendor_extensions=extensions, id="remap-id"
    )
    root = component_with_map(MemoryMapType(name="map", choice=(remap, AddressUnitBits(value="8"), SharedType.NO)))
    source = XmlDocument.serializer().render(root)
    assert SCHEMA.validate(etree.fromstring(source.encode())), SCHEMA.error_log
    root = XmlDocument.parser().from_string(source, Component)
    registry.register(root, ("test", "memory", root.name, "1"))
    remap = root.memory_maps.memory_map[0].choice[0]
    remap.choice = tuple(remap.choice)
    removed = next(item for item in remap.choice if isinstance(item, model_type))
    survivor = next(item for item in remap.choice if item is not removed)
    original_mode_refs = remap.mode_ref
    remap_id, child_id = get_handle(remap), get_handle(removed)
    survivor_id, mode_ref_id = get_handle(survivor), get_handle(remap.mode_ref[0])
    extension_id = get_handle(remap.vendor_extensions)

    assert operation(**{parameter: child_id}) is True

    assert isinstance(remap.choice, list) and remap.choice == [survivor]
    assert resolve_handle(child_id) is None
    assert resolve_handle(remap_id) is remap and resolve_handle(survivor_id) is survivor
    assert resolve_handle(mode_ref_id) is remap.mode_ref[0]
    assert resolve_handle(extension_id) is remap.vendor_extensions
    assert remap.mode_ref is original_mode_refs
    assert remap.name == "window" and remap.id == "remap-id"
    assert_schema_valid(root)


@pytest.mark.parametrize("name,parameter,model_type", _REMOVERS)
def test_removing_last_child_keeps_optional_group_and_mode_references(name, parameter, model_type) -> None:
    operation = getattr(api, name)
    child = {
        AddressBlock: lambda: block("only-block"),
        Bank: lambda: bank("only-bank"),
        SubspaceMap: lambda: subspace("only-subspace"),
    }[model_type]()
    reference = ModeRef(value="active", priority=0)
    remap = MemoryRemap(name="window", mode_ref=[reference], choice=(child,))
    root = component_with_map(MemoryMapType(name="map", choice=[remap]))
    root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
    registry.register(root, ("test", "memory", root.name, "1"))
    remap = root.memory_maps.memory_map[0].choice[0]
    child = remap.choice[0]
    child_id = get_handle(child)
    mode_ref_id = get_handle(remap.mode_ref[0])

    assert operation(child_id) is True

    assert remap.choice == []
    assert resolve_handle(child_id) is None
    assert resolve_handle(mode_ref_id) is remap.mode_ref[0]
    assert remap.mode_ref[0].value == "active"
    assert_schema_valid(root)


@pytest.mark.parametrize("name,parameter,model_type", _REMOVERS)
def test_removed_bank_block_and_subspace_invalidate_owned_graph_but_keep_shared_scalars(
    name, parameter, model_type
) -> None:
    operation = getattr(api, name)
    shared_scalars = (UsageType.MEMORY, SharedType.NO)
    if model_type is Bank:
        policy = AccessPolicies.AccessPolicy(access=AccessType.READ_WRITE)
        policies = AccessPolicies(access_policy=[policy])
        nested_block = BankedBlockType(
            name="banked-block",
            range=UnsignedPositiveLongintExpression(value="8"),
            width=UnsignedPositiveIntExpression(value="32"),
        )
        seed = BaseAddress(value="12")
        volatile = Volatile(value=True)
        child = Bank(
            name="outer-bank",
            base_address=seed,
            bank_alignment=BankAlignmentType.SERIAL,
            choice=(nested_block, policies, UsageType.MEMORY, volatile),
        )
        descendants = (seed, nested_block, nested_block.range, nested_block.width, policies, policy, volatile)
    elif model_type is AddressBlock:
        child = block("address-block")
        descendants = (child.base_address, *child.choice)
    else:
        child = subspace("subspace")
        descendants = (child.base_address,)
    sibling = block("sibling")
    remap = MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)], choice=[child, sibling])
    child_id = get_handle(child)
    sibling_id = get_handle(sibling)
    descendant_ids = [get_handle(item) for item in descendants]
    scalar_ids = [get_handle(item) for item in shared_scalars]
    register_parent(child, remap, ("choice",), "list")

    assert operation(child_id) is True

    assert resolve_handle(child_id) is None
    assert all(resolve_handle(handle) is None for handle in descendant_ids)
    assert all(resolve_handle(handle) is value for handle, value in zip(scalar_ids, shared_scalars, strict=True))
    assert resolve_handle(sibling_id) is sibling


@pytest.mark.parametrize("name,parameter,model_type", _REMOVERS)
def test_rejects_foreign_owner_types_wrong_models_and_definition_reference_branches(
    name, parameter, model_type
) -> None:
    operation = getattr(api, name)
    child = {
        AddressBlock: lambda: block("candidate-block"),
        Bank: lambda: bank("candidate-bank"),
        SubspaceMap: lambda: subspace("candidate-subspace"),
    }[model_type]()
    wrong_children = {
        AddressBlock: (
            BankedBlockType(
                name="wrong",
                range=UnsignedPositiveLongintExpression(value="1"),
                width=UnsignedPositiveIntExpression(value="1"),
            ),
        ),
        Bank: (BankedBankType(name="wrong", bank_alignment=BankAlignmentType.SERIAL),),
        SubspaceMap: (BankedSubspaceType(name="wrong", initiator_ref="bus"),),
    }[model_type]
    for wrong in wrong_children:
        assert_invalid_id(operation, get_handle(wrong))

    foreign_owners = (
        MemoryMapType(name="map", choice=[child]),
        LocalMemoryMapType(name="local", address_block_or_bank=[child]),
        bank("foreign-bank"),
        AddressSpaces.AddressSpace(
            name="space",
            range=UnsignedPositiveLongintExpression(value="32"),
            width=UnsignedPositiveIntExpression(value="32"),
        ),
        MemoryRemapType.RemapDefinitionRef(value="external", type_definitions="defs"),
    )
    for foreign_owner in foreign_owners:
        child_id = get_handle(child)
        register_parent(child, foreign_owner, ("choice",), "list")
        assert_invalid_id(operation, child_id)
        assert resolve_handle(child_id) is child

    reference = MemoryRemapType.RemapDefinitionRef(value="undefined", type_definitions="missing")
    remap = MemoryRemap(name="definition-source", choice=(reference,))
    source_child = {
        AddressBlock: lambda: block("not-owned"),
        Bank: lambda: bank("not-owned"),
        SubspaceMap: lambda: subspace("not-owned"),
    }[model_type]()
    register_parent(source_child, remap, ("choice",), "list")
    original_choice = remap.choice
    assert_invalid_id(operation, get_handle(source_child))
    assert remap.choice is original_choice and remap.choice == (reference,)


@pytest.mark.parametrize("name,parameter,model_type", _REMOVERS)
def test_malformed_parent_path_membership_duplicates_and_choices_are_atomic(name, parameter, model_type) -> None:
    operation = getattr(api, name)
    child = {
        AddressBlock: lambda: block("child-block"),
        Bank: lambda: bank("child-bank"),
        SubspaceMap: lambda: subspace("child-subspace"),
    }[model_type]()
    unrelated = block("unrelated")
    remap = MemoryRemap(name="window", choice=(child, unrelated))
    original_choice = remap.choice
    child_id = get_handle(child)

    register_parent(child, remap, ("name",), "list")
    assert_invalid_id(operation, child_id)
    assert remap.choice is original_choice

    register_parent(child, remap, ("choice",), "list")
    remap.choice = (unrelated,)
    original_choice = remap.choice
    assert_invalid_id(operation, child_id)
    assert remap.choice is original_choice

    remap.choice = (child, child)
    original_choice = remap.choice
    assert_invalid_id(operation, child_id)
    assert remap.choice is original_choice

    remap.choice = (child, MemoryRemapType.RemapDefinitionRef(value="definition", type_definitions="defs"))
    original_choice = remap.choice
    assert_invalid_id(operation, child_id)
    assert remap.choice is original_choice

    for malformed in (None, {}, (child, object()), (child, SharedType.NO)):
        remap.choice = malformed
        original_choice = remap.choice
        assert_invalid_id(operation, child_id)
        assert remap.choice is original_choice


@pytest.mark.parametrize("name,parameter,model_type", _REMOVERS)
def test_stale_handle_after_removal_is_rejected(name, parameter, model_type) -> None:
    operation = getattr(api, name)
    child = {
        AddressBlock: lambda: block("removed-block"),
        Bank: lambda: bank("removed-bank"),
        SubspaceMap: lambda: subspace("removed-subspace"),
    }[model_type]()
    remap = MemoryRemap(name="window", choice=[child])
    child_id = get_handle(child)
    register_parent(child, remap, ("choice",), "list")

    assert operation(child_id) is True
    assert_invalid_id(operation, child_id)
