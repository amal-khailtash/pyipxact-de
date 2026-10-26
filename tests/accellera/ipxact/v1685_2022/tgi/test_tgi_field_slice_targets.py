"""Field-slice ByID getters resolve typed targets within local hierarchy."""

import inspect
from collections.abc import Callable, Iterator, Sequence
from typing import TypedDict, cast

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import slice_ as api
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
    AddressBankType,
    AddressBlock,
    AddressBlockRef,
    AddressBlockType,
    AddressSpaces,
    AlternateRegisterRef,
    AlternateRegisters,
    Bank,
    BankAlignmentType,
    BankedBlockType,
    BankRef,
    BaseAddress,
    Component,
    ComponentPortDirectionType,
    ComponentType,
    FieldMap,
    FieldMaps,
    FieldRef,
    FieldType,
    LocalMemoryMapType,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapRef,
    Model,
    ModeRef,
    Port,
    PortWireType,
    RegisterFile,
    RegisterFileRef,
    RegisterRef,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_Mode = ComponentType.Modes.Mode
_ModeFieldSlice = _Mode.FieldSlice
_MapFieldSlice = FieldMap.FieldSlice
_FieldSlice = _ModeFieldSlice | _MapFieldSlice
_FieldSliceType = type[_ModeFieldSlice] | type[_MapFieldSlice]
_FieldAddressSpaceRef = _ModeFieldSlice.AddressSpaceRef | _MapFieldSlice.AddressSpaceRef
_FieldMemoryMapRef = _ModeFieldSlice.MemoryMapRef | _MapFieldSlice.MemoryMapRef
_FieldChoiceRef = _FieldAddressSpaceRef | _FieldMemoryMapRef | MemoryRemapRef
_Register = AddressBlockType.Register | RegisterFile.Register | BankedBlockType.Register
_KINDS: tuple[_FieldSliceType, ...] = (_ModeFieldSlice, _MapFieldSlice)
_KIND_IDS = ("mode", "field-map")
_TARGETS: tuple[tuple[str, str, str, str], ...] = (
    ("AddressBlockRef", "address_block_ref", "addressBlockRef", "address-block"),
    ("AddressSpaceRef", "address_space_ref", "addressSpaceRef", "address-space"),
    ("AlternateRegisterRef", "alternate_register_ref", "alternateRegisterRef", "alternate-register"),
    ("MemoryMapRef", "memory_map_ref", "memoryMapRef", "memory-map"),
    ("MemoryRemapRef", "memory_remap_ref", "memoryRemapRef", "memory-remap"),
    ("RegisterRef", "register_ref", "registerRef", "register"),
)
_TARGET_IDS = tuple(target[3] for target in _TARGETS)


class _MapTargets(TypedDict):
    block: AddressBlock
    direct_register: _Register
    outer_file: RegisterFile
    inner_file: RegisterFile
    file_register: _Register
    outer_bank: Bank
    inner_bank: AddressBankType.Bank
    bank_register: _Register
    banked_block: BankedBlockType
    remap_block: AddressBlock
    remap_register: _Register
    remap: MemoryRemap


class _ResolvedMapTargets(_MapTargets):
    memory_map: MemoryMapType


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field(name: str = "enable") -> FieldType:
    return FieldType(
        name=name,
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="1")],
    )


def _alternate_registers(name: str = "debug") -> AlternateRegisters:
    return AlternateRegisters(
        alternate_register=[
            AlternateRegisters.AlternateRegister(
                name=name,
                mode_ref=[ModeRef(value="active", priority=0)],
                field_value=[_field()],
            )
        ]
    )


def _register(register_type: type[_Register], name: str = "control") -> _Register:
    return register_type(
        name=name,
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32"), _field()],
        alternate_registers=_alternate_registers(),
    )


def _memory_map(name: str) -> tuple[MemoryMapType, _MapTargets]:
    direct_register = _register(AddressBlockType.Register)
    file_register = _register(RegisterFile.Register)
    inner_file = RegisterFile(
        name="inner_files", address_offset=UnsignedLongintExpression(value="0"), choice=[file_register]
    )
    outer_file = RegisterFile(
        name="outer_files", address_offset=UnsignedLongintExpression(value="0"), choice=[inner_file]
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            direct_register,
            outer_file,
        ],
    )

    bank_register = _register(BankedBlockType.Register)
    banked_block = BankedBlockType(
        name="banked_registers",
        range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
        register_or_register_file=[bank_register],
    )
    inner_bank = AddressBankType.Bank(
        name="inner_bank",
        bank_alignment=BankAlignmentType.PARALLEL,
        choice=[banked_block],
    )
    outer_bank = Bank(
        name="outer_bank",
        base_address=BaseAddress(value="0"),
        bank_alignment=BankAlignmentType.PARALLEL,
        choice=[inner_bank],
    )
    remap_register = _register(AddressBlockType.Register)
    remap_block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            remap_register,
        ],
    )
    remap = MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)], choice=[remap_block])
    memory_map = MemoryMapType(name=name, choice=[block, outer_bank, remap])
    return memory_map, {
        "block": block,
        "direct_register": direct_register,
        "outer_file": outer_file,
        "inner_file": inner_file,
        "file_register": file_register,
        "outer_bank": outer_bank,
        "inner_bank": inner_bank,
        "bank_register": bank_register,
        "banked_block": banked_block,
        "remap_block": remap_block,
        "remap_register": remap_register,
        "remap": remap,
    }


def _field_slice(
    kind: _FieldSliceType,
    *,
    target: str,
    choice: str = "map_b",
    address_space_ref: str | None = None,
    block_ref: str | None = "registers",
    register_file_refs: Sequence[str] = (),
    bank_refs: Sequence[str] = (),
    alternate_ref: str | None = None,
    remap_ref: str | None = None,
) -> _FieldSlice:
    if address_space_ref is not None:
        selected: list[_FieldChoiceRef] = [kind.AddressSpaceRef(address_space_ref=address_space_ref)]
    else:
        selected = [kind.MemoryMapRef(memory_map_ref=choice)]
        if remap_ref is not None:
            selected.append(MemoryRemapRef(memory_remap_ref=remap_ref))
    kwargs = {
        "address_space_ref_or_memory_map_ref_or_memory_remap_ref": selected,
        "address_block_ref": None if block_ref is None else AddressBlockRef(address_block_ref=block_ref),
        "register_file_ref": [RegisterFileRef(register_file_ref=name) for name in register_file_refs],
        "register_ref": RegisterRef(register_ref="control"),
        "alternate_register_ref": (
            None if alternate_ref is None else AlternateRegisterRef(alternate_register_ref=alternate_ref)
        ),
        "field_ref": FieldRef(field_ref="enable"),
        "bank_ref": [BankRef(bank_ref=name) for name in bank_refs],
    }
    if kind is _ModeFieldSlice:
        return _ModeFieldSlice(name=f"source_{target}", **kwargs)
    return _MapFieldSlice(**kwargs)


def _local_address_space() -> tuple[AddressSpaces.AddressSpace, AddressBlock, _Register]:
    register = _register(AddressBlockType.Register)
    block = AddressBlock(
        name="local_registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            register,
        ],
    )
    address_space = AddressSpaces.AddressSpace(
        name="local_space",
        range=UnsignedPositiveLongintExpression(value="4096"),
        width=UnsignedPositiveIntExpression(value="32"),
        local_memory_map=LocalMemoryMapType(name="local_map", address_block_or_bank=[block]),
    )
    return address_space, block, register


def _component(
    kind: _FieldSliceType,
    item: _FieldSlice,
    *,
    maps: Sequence[MemoryMapType] = (),
    address_spaces: Sequence[AddressSpaces.AddressSpace] = (),
    name: str = "source",
) -> Component:
    port = Port(
        name="data_i",
        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
    )
    if kind is _ModeFieldSlice:
        modes = ComponentType.Modes(mode=[_Mode(name="active", field_slice=[cast(_ModeFieldSlice, item)])])
    else:
        modes = ComponentType.Modes(mode=[_Mode(name="active")])
        port.field_maps = FieldMaps(field_map=[FieldMap(field_slice=cast(_MapFieldSlice, item))])
    return Component(
        vendor="acme",
        library="targets",
        name=name,
        version="1.0",
        modes=modes,
        address_spaces=AddressSpaces(address_space=address_spaces) if address_spaces else None,
        memory_maps=MemoryMaps(memory_map=maps) if maps else None,
        model=Model(ports=Model.Ports(port=[port])),
    )


def _registered_case(
    kind: _FieldSliceType,
    target: str,
    *,
    choice: str = "map_b",
    address_space_ref: str | None = None,
    register_file_refs: Sequence[str] = (),
    bank_refs: Sequence[str] = (),
    alternate_ref: str | None = None,
    remap_ref: str | None = None,
    block_ref: str | None = "registers",
    duplicate: bool = False,
    source_name: str | None = None,
) -> tuple[Component, _FieldSlice, object]:
    map_a, _ = _memory_map("map_a")
    map_b, targets_b = _memory_map("map_b")
    maps: list[MemoryMapType] = [map_a, map_b]
    expected_targets = {
        "AddressBlockRef": targets_b["block"],
        "MemoryMapRef": map_b,
        "MemoryRemapRef": targets_b["remap"],
        "RegisterRef": targets_b["direct_register"],
        "RegisterFileRef": targets_b["inner_file"],
        "AlternateRegisterRef": targets_b["file_register"].alternate_registers.alternate_register[0],
        "BankRegisterRef": targets_b["bank_register"],
    }
    if duplicate:
        if target == "MemoryMapRef":
            maps.append(_memory_map("map_b")[0])
        elif target == "MemoryRemapRef":
            map_b.choice.append(MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)]))
        elif target == "AddressBlockRef":
            if block_ref == "banked_registers":
                targets_b["inner_bank"].choice.append(
                    BankedBlockType(
                        name="banked_registers",
                        range=UnsignedPositiveLongintExpression(value="256"),
                        width=UnsignedPositiveIntExpression(value="32"),
                        register_or_register_file=[_register(BankedBlockType.Register)],
                    )
                )
            else:
                block_b = AddressBlock(
                    name="registers",
                    base_address=BaseAddress(value="0"),
                    choice=[
                        UnsignedPositiveLongintExpression(value="256"),
                        UnsignedPositiveIntExpression(value="32"),
                        _register(AddressBlockType.Register),
                    ],
                )
                map_b.choice.append(block_b)
        elif target == "AlternateRegisterRef":
            target_reg = targets_b["file_register"]
            target_reg.alternate_registers.alternate_register.append(
                AlternateRegisters.AlternateRegister(
                    name="debug",
                    mode_ref=[ModeRef(value="active", priority=0)],
                    field_value=[_field()],
                )
            )
        elif target == "RegisterRef":
            target_reg = targets_b["direct_register"]
            duplicate_register = _register(AddressBlockType.Register)
            targets_b["block"].choice.append(duplicate_register)
        elif target == "RegisterFileRef":
            targets_b["block"].choice.append(
                RegisterFile(
                    name="inner_files",
                    address_offset=UnsignedLongintExpression(value="0"),
                    choice=[_register(RegisterFile.Register)],
                )
            )
        elif target == "AddressSpaceRef":
            pass
    local_space, _local_block, _local_register = _local_address_space()
    spaces = [local_space]
    if target == "AddressSpaceRef" and address_space_ref is None:
        address_space_ref = "local_space"
    if address_space_ref == "local_space":
        block_ref = "local_registers"
    if target == "AddressBlockRef" and block_ref == "banked_registers":
        expected_targets["AddressBlockRef"] = targets_b["banked_block"]
    item = _field_slice(
        kind,
        target=target,
        choice=choice,
        address_space_ref=address_space_ref,
        block_ref=block_ref,
        register_file_refs=register_file_refs,
        bank_refs=bank_refs,
        alternate_ref=alternate_ref,
        remap_ref=remap_ref,
    )
    root = _component(kind, item, maps=maps, address_spaces=spaces, name=source_name or f"source_{target}")
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    expected = (
        spaces[0]
        if target == "AddressSpaceRef" and address_space_ref == "local_space"
        else None
        if target == "AddressSpaceRef"
        else expected_targets[target]
    )
    return root, item, expected


def _owner_wrapper(item: _FieldSlice, suffix: str) -> object:
    if suffix == "AddressBlockRef":
        return item.address_block_ref
    if suffix == "AddressSpaceRef":
        return item.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0]
    if suffix == "AlternateRegisterRef":
        return item.alternate_register_ref
    if suffix == "MemoryMapRef":
        return item.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0]
    if suffix == "MemoryRemapRef":
        return item.address_space_ref_or_memory_map_ref_or_memory_remap_ref[1]
    return item.register_ref


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize("suffix,attribute,xml_name,case_id", _TARGETS, ids=_TARGET_IDS)
def test_field_slice_by_id_getters_resolve_typed_targets_in_selected_hierarchy(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_name: str, case_id: str
) -> None:
    options: dict[str, object] = {}
    if suffix == "AddressSpaceRef":
        options.update(address_space_ref="local_space", block_ref="local_registers")
    elif suffix == "AlternateRegisterRef":
        options.update(register_file_refs=("outer_files", "inner_files"), alternate_ref="debug")
    elif suffix == "MemoryRemapRef":
        options.update(remap_ref="window")
    elif suffix == "RegisterRef":
        options.update()
    root, item, expected = _registered_case(kind, suffix, **options)
    owner_id = get_handle(item)
    source_wrapper = _owner_wrapper(item, suffix)
    source_wrapper_id = get_handle(source_wrapper)

    target_id = getattr(api, f"getFieldSlice{suffix}ByID")(owner_id)
    assert target_id == get_handle(expected)
    assert target_id != source_wrapper_id
    assert resolve_handle(target_id) is expected
    info = get_parent_info(source_wrapper_id)
    assert info is not None and info.parent_handle == owner_id
    assert get_handle(root) is not None


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize("suffix,attribute,xml_name,case_id", _TARGETS, ids=_TARGET_IDS)
def test_field_slice_by_id_getters_report_missing_named_targets(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_name: str, case_id: str
) -> None:
    options: dict[str, object] = {"choice": "absent_map"}
    if suffix == "AddressSpaceRef":
        options.update(address_space_ref="absent_space")
    elif suffix == "AlternateRegisterRef":
        options.update(register_file_refs=("absent_files",), alternate_ref="absent_alt")
    elif suffix == "MemoryRemapRef":
        options.update(choice="absent_map", remap_ref="absent_window")
    root, item, _expected = _registered_case(kind, suffix, **options)
    owner_id = get_handle(item)

    with pytest.raises(TgiError) as error:
        getattr(api, f"getFieldSlice{suffix}ByID")(owner_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize("suffix,attribute,xml_name,case_id", _TARGETS, ids=_TARGET_IDS)
def test_field_slice_by_id_getters_report_ambiguous_targets(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_name: str, case_id: str
) -> None:
    options: dict[str, object] = {"duplicate": True}
    if suffix == "AddressSpaceRef":
        options.update(address_space_ref="local_space", block_ref="local_registers")
    elif suffix == "AlternateRegisterRef":
        options.update(register_file_refs=("outer_files", "inner_files"), alternate_ref="debug")
    elif suffix == "MemoryRemapRef":
        options.update(remap_ref="window")
    root, item, _expected = _registered_case(kind, suffix, **options)
    if suffix == "AddressSpaceRef":
        extra, _, _ = _local_address_space()
        root.address_spaces.address_space = [root.address_spaces.address_space[0], extra]
    owner_id = get_handle(item)

    with pytest.raises(TgiError) as error:
        getattr(api, f"getFieldSlice{suffix}ByID")(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_memory_map_and_remap_choice_target_handles_are_scoped_to_containing_document(
    kind: _FieldSliceType,
) -> None:
    root, item, _expected_remap = _registered_case(kind, "MemoryRemapRef", remap_ref="window")
    other_root, _other_item, other_map = _registered_case(
        kind, "MemoryRemapRef", remap_ref="window", source_name="source_MemoryRemapRef_other"
    )
    # The second registered document has equal local map and remap names.
    owner_id = get_handle(item)
    expected_map = _memory_map_target(root, "map_b")["memory_map"]

    map_target_id = api.getFieldSliceMemoryMapRefByID(owner_id)
    remap_target_id = api.getFieldSliceMemoryRemapRefByID(owner_id)
    assert map_target_id == get_handle(expected_map)
    expected_remap = _memory_map_target(root, "map_b")["remap"]
    assert remap_target_id == get_handle(expected_remap)
    assert resolve_handle(map_target_id) is expected_map
    assert resolve_handle(map_target_id) is not other_map
    assert resolve_handle(remap_target_id) is root.memory_maps.memory_map[1].choice[-1]
    assert other_root is not root


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_address_space_choice_resolves_local_memory_map_targets(kind: _FieldSliceType) -> None:
    root, item, expected_space = _registered_case(kind, "AddressSpaceRef", address_space_ref="local_space")
    owner_id = get_handle(item)
    local_block = root.address_spaces.address_space[0].local_memory_map.address_block_or_bank[0]
    local_register = local_block.choice[2]

    assert resolve_handle(api.getFieldSliceAddressSpaceRefByID(owner_id)) is expected_space
    assert resolve_handle(api.getFieldSliceAddressBlockRefByID(owner_id)) is local_block
    assert resolve_handle(api.getFieldSliceRegisterRefByID(owner_id)) is local_register


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize("duplicate", [False, True], ids=("unique", "ambiguous"))
def test_field_slice_address_block_reference_resolves_banked_block_targets(
    kind: _FieldSliceType, duplicate: bool
) -> None:
    root, item, expected = _registered_case(
        kind,
        "AddressBlockRef",
        block_ref="banked_registers",
        bank_refs=("outer_bank", "inner_bank"),
        duplicate=duplicate,
    )
    owner_id = get_handle(item)

    if duplicate:
        with pytest.raises(TgiError) as error:
            api.getFieldSliceAddressBlockRefByID(owner_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    else:
        target_id = api.getFieldSliceAddressBlockRefByID(owner_id)
        assert target_id == get_handle(expected)
        assert resolve_handle(target_id) is expected
        assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize("use_remap", [False, True], ids=("default-map", "selected-remap"))
def test_field_slice_address_block_and_register_targets_follow_remap_choice(
    kind: _FieldSliceType, use_remap: bool
) -> None:
    root, item, _expected = _registered_case(
        kind,
        "RegisterRef",
        remap_ref="window" if use_remap else None,
    )
    owner_id = get_handle(item)
    targets = _memory_map_target(root, "map_b")
    expected_block = targets["remap_block"] if use_remap else targets["block"]
    expected_register = targets["remap_register"] if use_remap else targets["direct_register"]

    block_id = api.getFieldSliceAddressBlockRefByID(owner_id)
    register_id = api.getFieldSliceRegisterRefByID(owner_id)
    assert resolve_handle(block_id) is expected_block
    assert resolve_handle(register_id) is expected_register


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "path_case,path",
    [
        ("ordered", ("outer_files", "inner_files")),
        ("reversed", ("inner_files", "outer_files")),
        ("skipped-level", ("inner_files",)),
    ],
    ids=("ordered", "reversed", "skipped-level"),
)
def test_field_slice_register_file_qualifiers_require_exact_ordered_path(
    kind: _FieldSliceType, path_case: str, path: tuple[str, ...]
) -> None:
    root, item, expected = _registered_case(kind, "RegisterFileRef", register_file_refs=path)
    owner_id = get_handle(item)
    if path_case == "ordered":
        target_id = api.getFieldSliceRegisterRefByID(owner_id)
        assert target_id == get_handle(_memory_map_target(root, "map_b")["file_register"])
        assert resolve_handle(target_id) is _memory_map_target(root, "map_b")["file_register"]
    else:
        with pytest.raises(TgiError) as error:
            api.getFieldSliceRegisterRefByID(owner_id)
        assert error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "path_case,path",
    [
        ("ordered", ("outer_bank", "inner_bank")),
        ("reversed", ("inner_bank", "outer_bank")),
        ("skipped-level", ("inner_bank",)),
    ],
    ids=("ordered", "reversed", "skipped-level"),
)
def test_field_slice_bank_qualifiers_require_exact_ordered_path(
    kind: _FieldSliceType, path_case: str, path: tuple[str, ...]
) -> None:
    root, item, _expected = _registered_case(
        kind,
        "BankRegisterRef",
        block_ref=None,
        bank_refs=path,
    )
    owner_id = get_handle(item)
    if path_case == "ordered":
        target_id = api.getFieldSliceRegisterRefByID(owner_id)
        assert resolve_handle(target_id) is _memory_map_target(root, "map_b")["bank_register"]
    else:
        with pytest.raises(TgiError) as error:
            api.getFieldSliceRegisterRefByID(owner_id)
        assert error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_optional_alternate_and_remap_targets_return_none(kind: _FieldSliceType) -> None:
    root, item, _expected = _registered_case(kind, "RegisterRef")
    owner_id = get_handle(item)
    assert api.getFieldSliceAlternateRegisterRefByID(owner_id) is None
    assert api.getFieldSliceMemoryRemapRefByID(owner_id) is None
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize("suffix,attribute,xml_name,case_id", _TARGETS, ids=_TARGET_IDS)
def test_field_slice_target_getters_reject_invalid_owners_and_malformed_wrappers(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_name: str, case_id: str
) -> None:
    root, item, _expected = _registered_case(kind, suffix)
    getter = getattr(api, f"getFieldSlice{suffix}ByID")
    _assert_fault(getter, "unknown-owner")
    foreign = get_handle(_mode_port_slice())
    _assert_fault(getter, foreign)

    if suffix == "AddressBlockRef":
        item.address_block_ref = object()
    elif suffix == "AddressSpaceRef":
        item.address_space_ref_or_memory_map_ref_or_memory_remap_ref = [object()]
    elif suffix == "AlternateRegisterRef":
        item.alternate_register_ref = object()
    elif suffix in {"MemoryMapRef", "MemoryRemapRef"}:
        item.address_space_ref_or_memory_map_ref_or_memory_remap_ref = [
            kind.AddressSpaceRef(address_space_ref="local_space"),
            object(),
        ]
    else:
        item.register_ref = object()
    _assert_fault(getter, get_handle(item))
    assert resolve_handle(get_handle(root)) is root


def _memory_map_target(root: Component, name: str) -> _ResolvedMapTargets:
    memory_map = next(memory_map for memory_map in root.memory_maps.memory_map if memory_map.name == name)
    block, outer_bank, remap = memory_map.choice
    outer_file = block.choice[3]
    inner_file = outer_file.choice[0]
    file_register = inner_file.choice[0]
    inner_bank = outer_bank.choice[0]
    banked_block = inner_bank.choice[0]
    remap_block = remap.choice[0]
    return {
        "memory_map": memory_map,
        "block": block,
        "outer_file": outer_file,
        "inner_file": inner_file,
        "file_register": file_register,
        "remap_block": remap_block,
        "remap_register": remap_block.choice[2],
        "outer_bank": outer_bank,
        "inner_bank": inner_bank,
        "bank_register": banked_block.register_or_register_file[0],
        "banked_block": banked_block,
        "direct_register": block.choice[2],
        "remap": remap,
    }


def _mode_port_slice() -> _Mode.PortSlice:
    return _Mode.PortSlice(name="port", port_ref=_Mode.PortSlice.PortRef(port_ref="data_i"))


def _assert_fault(operation: Callable[..., object], *args: object) -> None:
    with pytest.raises(TgiError) as error:
        operation(*args)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_parsed_field_slice_register_reference_resolves_target_and_restores_source_ownership(
    kind: _FieldSliceType,
) -> None:
    register = _register(AddressBlockType.Register)
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            register,
        ],
    )
    memory_map = MemoryMapType(name="register_map", choice=[block])
    item = _field_slice(kind, target="RegisterRef", choice="register_map")
    root = _component(kind, item, maps=[memory_map], name="parsed_target_source")
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    if kind is _ModeFieldSlice:
        parsed_item = parsed.modes.mode[0].field_slice[0]
    else:
        parsed_item = parsed.model.ports.port[0].field_maps.field_map[0].field_slice
    owner_id = get_handle(parsed_item)

    target_id = api.getFieldSliceRegisterRefByID(owner_id)
    parsed_register = parsed.memory_maps.memory_map[0].choice[0].choice[2]
    assert target_id == get_handle(parsed_register)
    assert resolve_handle(target_id) is parsed_register
    reference_id = api.getFieldSliceRegisterRefID(owner_id)
    info = get_parent_info(reference_id)
    assert info is not None and info.parent_handle == owner_id and info.path == ("register_ref",)


def test_field_slice_target_getter_exports_and_native_signatures_match_annex_contract() -> None:
    expected: dict[str, tuple[tuple[str, ...], tuple[object, ...], object]] = {
        f"getFieldSlice{suffix}ByID": (("fieldSliceID",), (str,), str | None)
        for suffix, _attribute, _xml_name, _case_id in _TARGETS
    }
    assert set(expected) <= set(api.__all__)
    for name, (parameter_names, parameter_types, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type
