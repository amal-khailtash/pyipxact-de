"""Memory map category TGI functions (IEEE 1685-2022).

Implements the full BASE (F.7.57) and EXTENDED (F.7.58) API surface for the
Memory map category. ONLY the functions specified in those sections are
exported (no more, no less). Functions provide read (get) and mutation
operations across memory maps, banks, addressBlocks, subspaceMaps, memoryRemaps
and associated aliasing / definition references. Missing optional elements
return None (or empty lists) per TGI semantics. Invalid handles raise
``TgiError`` with ``TgiFaultCode.INVALID_ID``; bad arguments raise with
``TgiFaultCode.INVALID_ARGUMENT``.
"""

# ruff: noqa: I001

from collections.abc import Iterable
from typing import Any

from org.accellera.ipxact.v1685_2022 import (
    AddressBlockRef,
    Dim,
    BankRef,
    MemoryRemapRef,
    FieldType,
    Array,
    Index,
    Indices,
    AccessPolicies,
    AddressBlockType,
    AddressBlockDefinitions,
    BaseAddress,
    Parameters,
    RegisterFile,
    UnsignedPositiveLongintExpression,
    UnsignedPositiveIntExpression,
    UsageType,
    Volatile,
    ComponentType,
    ModeRef,
    SignedLongintExpression,
    SubspaceRefType,
    AddressBlock,
    AddressBankType,
    AddressBankDefinitionType,
    BankedDefinitionBankType,
    BankDefinitions,
    LocalBankedBankType,
    BankedBankType,
    BankedBlockType,
    BankedSubspaceType,
    AddressUnitBits,
    Bank,
    LocalAddressBankType,
    LocalMemoryMapType,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapType,
    SharedType,
    SubspaceMap,
    AddressSpaces,
)

from .address_space import _register_owned_child, _remove_owned
from .access_policy import _mode_ref_priority
from .component import _list_attr, _register_graph
from .bus_interface import _named_target
from ._expressions import _integer, _xml_text
from ._model import _walk_model, _reference_list
from .port_map import _child, _name
from ._reference_choices import _reference_choice, _set_reference_choice
from ._reference_paths import _append_reference_path, _remove_reference_path, _set_named_reference
from ._attribute_references import _reference_name, resolve_attribute_reference
from .register_file import _child_ids, _numeric, _expression
from .register import (
    _type_definition_external,
    _type_definition_target,
    _type_definition_reference_names,
    _register_reference,
    _register_alias,
    _remove_register_reference_index,
    _add_register_reference_index,
)
from .type_definitions import (
    getTypeDefinitionsAddressBlockDefinitionIDs,
    getTypeDefinitionsMemoryMapDefinitionIDs,
    getTypeDefinitionsBankDefinitionIDs,
    getTypeDefinitionsMemoryRemapDefinitionIDs,
)

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    "setAddressBlockDefinitionRef",
    "addAddressBlockRefIndex",
    "setAddressBlockAddressBlockDefinitionRef",
    "setAddressBlockArray",
    "setAddressBlockBaseAddress",
    "setAddressBlockRange",
    "setAddressBlockWidth",
    "removeAddressBlockArray",
    "removeAddressBlockRefIndex",
    "removeAddressBlockTypeIdentifier",
    "removeAddressBlockUsage",
    "removeAddressBlockVolatility",
    "setAddressBlockTypeIdentifier",
    "setAddressBlockUsage",
    "setAddressBlockVolatility",
    "getAliasOfAddressBlockRefByName",
    "getAliasOfAddressBlockRefID",
    "getAliasOfBankRefByNames",
    "getAliasOfBankRefIDs",
    "getAliasOfMemoryMapRefByName",
    "getAliasOfMemoryMapRefID",
    "getAliasOfMemoryRemapRefByID",
    "getAliasOfMemoryRemapRefByName",
    "getAliasOfMemoryRemapRefID",
    "getBankBankDefinitionRefByExternalTypeDefID",
    "getBankBankDefinitionRefByID",
    "getBankBankDefinitionRefByName",
    "getBankBankDefinitionRefID",
    "getMemoryRemapRemapDefinitionRefByExternalTypeDefID",
    "getMemoryRemapRemapDefinitionRefByID",
    "getMemoryRemapRemapDefinitionRefByName",
    "getMemoryRemapRemapDefinitionRefID",
    "getBankAddressBlockIDs",
    "getBankBankIDs",
    "getBankBaseAddress",
    "getBankBaseAddressExpression",
    "getBankBaseAddressID",
    "getBankBlockAndSubspaceElementIDs",
    "getBankSubspaceMapIDs",
    "getBankUsage",
    "getBankVolatility",
    # BASE (F.7.57.x) – ordering matches spec numbering groups
    # AddressBlock getters (1–21) - subset implemented (schema coverage pending)
    "getAddressBlockAddressBlockDefinitionRefByExternalTypeDefID",
    "getAddressBlockAddressBlockDefinitionRefByID",
    "getAddressBlockAddressBlockDefinitionRefByName",
    "getAddressBlockAddressBlockDefinitionRefID",
    "getAddressBlockAccessPolicyIDs",
    "getAddressBlockArrayID",
    "getAddressBlockRefIndexIDs",
    "getAddressBlockRegisterFileIDs",
    "getAddressBlockRegisterIDs",
    "getAddressBlockTypeIdentifier",
    "getAddressBlockUsage",
    "getAddressBlockVolatility",
    "getAddressBlockBaseAddress",
    "getAddressBlockBaseAddressExpression",
    "getAddressBlockBaseAddressID",
    "getAddressBlockRange",
    "getAddressBlockRangeExpression",
    "getAddressBlockRangeID",
    "getAddressBlockWidth",
    "getAddressBlockWidthExpression",
    "getAddressBlockWidthID",
    "getMemoryMapAddressBlockIDs",  # 44 (spec numbering within section)
    "getMemoryMapAddressUnitBits",
    "getMemoryMapAddressUnitBitsExpression",
    "getMemoryMapAddressUnitBitsID",
    "getMemoryMapBankIDs",  # 48
    "getMemoryMapElementIDs",
    "getMemoryMapElementType",
    "getMemoryMapMemoryMapDefinitionRefByExternalTypeDefID",
    "getMemoryMapMemoryMapDefinitionRefByID",
    "getMemoryMapMemoryMapDefinitionRefByName",
    "getMemoryMapMemoryMapDefinitionRefID",
    "getMemoryMapMemoryRemapIDs",
    "getMemoryMapRemapIDs",
    # (Minimal name/displayName/description/shared retained for convenience if spec maps earlier numbers)
    "getMemoryMapSubspaceMapIDs",
    "getMemoryRemapAddressBlockIDs",
    "getMemoryRemapBankIDs",
    "getMemoryRemapElementIDs",
    "getMemoryRemapSubspaceMapIDs",
    "getMemoryRemapModeRefByID",
    "getMemoryRemapModeRefByNames",
    "getMemoryRemapModeRefIDs",
    "getSubspaceMapBaseAddress",
    "getSubspaceMapBaseAddressExpression",
    "getSubspaceMapBaseAddressID",
    "getSubspaceMapSegmentRefByName",
    "getMemoryMapShared",  # reuse previous, spec 68 setter counterpart
    # EXTENDED (F.7.58) - subset focusing on core structural adds/removes + key setters
    "addMemoryMapAddressBlock",
    "addMemoryMapBank",
    "addMemoryMapMemoryRemap",
    "addMemoryMapSubspaceMap",
    "addMemoryRemapModeRef",
    "removeMemoryMapMemoryRemap",
    "removeMemoryMapShared",
    "removeMemoryMapSubspaceMap",
    "removeMemoryRemapModeRef",
    "setMemoryMapMemoryMapDefinitionRef",
    "setMemoryMapShared",
    "setMemoryRemapRemapDefinitionRef",
    "setSubSpaceMapBaseAddress",
    "removeBankUsage",
    "removeBankVolatility",
    "setBankBankDefinitionRef",
    "setBankBaseAddress",
    "setBankUsage",
    "setBankVolatility",
    "addAliasOfBankRef",
    "removeAliasOfAddressBlockRef",
    "removeAliasOfAddressSpaceRef",
    "removeAliasOfBankRef",
    "removeAliasOfMemoryMapRef",
    "setAliasOfAddressBlockRef",
    "setAliasOfAddressSpaceRef",
    "setAliasOfMemoryMapRef",
    "setAliasOfMemoryRemapRef",
]


# ---------------------------------------------------------------------------
# Internal helpers (non-spec)
# ---------------------------------------------------------------------------


def _resolve_memory_map(memoryMapID: str) -> MemoryMapType | None:
    if not isinstance(memoryMapID, str):
        return None
    obj = resolve_handle(memoryMapID)
    return obj if isinstance(obj, MemoryMapType) else None


def _require_memory_map(memoryMapID: str) -> MemoryMapType:
    mm = _resolve_memory_map(memoryMapID)
    if mm is None:
        raise TgiError("Invalid memoryMap handle", TgiFaultCode.INVALID_ID)
    return mm


def _ids(items: Iterable[Any]) -> list[str]:  # helper for list of handles
    return [get_handle(i) for i in items]


# ---------------------------------------------------------------------------
# BASE (F.7.57)
# ---------------------------------------------------------------------------


def _memory_map_choice(memory_map: MemoryMapType) -> list | tuple:
    """Validate stored inline/reference branches without normalizing their containers."""
    values = memory_map.choice
    allowed = (AddressBlock, Bank, SubspaceMap, MemoryRemap, AddressUnitBits, SharedType)
    if not isinstance(values, (list, tuple)):
        raise TgiError("Invalid memoryMap choice", TgiFaultCode.INVALID_ID)
    references = [item for item in values if isinstance(item, MemoryMapType.MemoryMapDefinitionRef)]
    if references:
        if len(values) != 1:
            raise TgiError("Conflicting memoryMap definition and inline content", TgiFaultCode.INVALID_ID)
        return values
    if any(not isinstance(item, allowed) for item in values):
        raise TgiError("Invalid memoryMap choice child", TgiFaultCode.INVALID_ID)
    for scalar in (AddressUnitBits, SharedType):
        if sum(isinstance(item, scalar) for item in values) > 1:
            raise TgiError("Duplicate memoryMap scalar child", TgiFaultCode.INVALID_ID)
    return values


def _memory_map_elements(memory_map: MemoryMapType | LocalMemoryMapType) -> list[str]:
    """Return ordered direct block/bank/subspace handles from the actual schema container."""
    if isinstance(memory_map, MemoryMapType):
        values = _memory_map_choice(memory_map)
        children = [item for item in values if isinstance(item, (AddressBlock, Bank, SubspaceMap))]
        return _child_ids(memory_map, children, ("choice",))
    values = memory_map.address_block_or_bank
    if not isinstance(values, (list, tuple)) or any(
        not isinstance(item, (AddressBlock, LocalAddressBankType)) for item in values
    ):
        raise TgiError("Invalid localMemoryMap children", TgiFaultCode.INVALID_ID)
    return _child_ids(memory_map, values, ("address_block_or_bank",))


def _require_map_or_local(handle: str) -> MemoryMapType | LocalMemoryMapType:
    if not isinstance(handle, str):
        raise TgiError("Invalid memoryMap or localMemoryMap handle", TgiFaultCode.INVALID_ID)
    owner = resolve_handle(handle)
    if not isinstance(owner, (MemoryMapType, LocalMemoryMapType)):
        raise TgiError("Invalid memoryMap or localMemoryMap handle", TgiFaultCode.INVALID_ID)
    return owner


def _memory_map_unit(owner: MemoryMapType | LocalMemoryMapType) -> AddressUnitBits | None:
    """Read the explicit unit node; local maps use their actual containing address space."""
    if isinstance(owner, LocalMemoryMapType):
        address_space = _register_owned_child(owner, AddressSpaces.AddressSpace)
        if address_space is None or address_space.local_memory_map is not owner:
            raise TgiError("localMemoryMap has no containing addressSpace", TgiFaultCode.INVALID_ID)
        return _child(address_space, "address_unit_bits", AddressUnitBits)
    values = _memory_map_choice(owner)
    node = next((item for item in values if isinstance(item, AddressUnitBits)), None)
    if node is not None:
        register_parent(node, owner, ("choice",), "list")
    return node


def getMemoryMapAddressBlockIDs(memoryMapID: str) -> list[str]:
    """Return owned direct addressBlock handles in stored order (F.7.57.44)."""
    owner = _require_memory_map(memoryMapID)
    return [handle for handle in _memory_map_elements(owner) if isinstance(resolve_handle(handle), AddressBlock)]


def getMemoryMapAddressUnitBits(memoryMapOrLocalMemoryMapID: str) -> int | None:
    """Evaluate explicit addressUnitBits or the absent inline default of eight (F.7.57.45).

    Local maps use the containing addressSpace. Definition-reference values require
    definition expansion and remain unavailable when no inline value is stored.
    """
    owner = _require_map_or_local(memoryMapOrLocalMemoryMapID)
    node = _memory_map_unit(owner)
    if node is None:
        if isinstance(owner, MemoryMapType) and any(
            isinstance(item, MemoryMapType.MemoryMapDefinitionRef) for item in owner.choice
        ):
            return None
        return 8
    if not isinstance(node.value, str):
        raise TgiError("Invalid addressUnitBits source", TgiFaultCode.INVALID_ID)
    return _numeric(node, "addressUnitBits", minimum=1, maximum=(1 << 63) - 1)


def getMemoryMapAddressUnitBitsExpression(memoryMapOrLocalMemoryMapID: str) -> str | None:
    """Return explicit address-unit source without creating a default node (F.7.57.46)."""
    node = _memory_map_unit(_require_map_or_local(memoryMapOrLocalMemoryMapID))
    if node is None:
        return None
    if not isinstance(node.value, str):
        raise TgiError("Invalid addressUnitBits source", TgiFaultCode.INVALID_ID)
    return node.value


def getMemoryMapAddressUnitBitsID(memoryMapID: str) -> str | None:
    """Return the explicit owned addressUnitBits handle, or None when absent (F.7.57.47)."""
    node = _memory_map_unit(_require_memory_map(memoryMapID))
    return get_handle(node) if node is not None else None


def getMemoryMapBankIDs(memoryMapID: str) -> list[str]:
    """Return owned direct bank handles in stored order (F.7.57.48)."""
    owner = _require_memory_map(memoryMapID)
    return [handle for handle in _memory_map_elements(owner) if isinstance(resolve_handle(handle), Bank)]


def getMemoryMapElementIDs(memoryMapOrLocalMemoryMapID: str) -> list[str]:
    """Return ordered direct banks, blocks and subspace maps, excluding remaps (F.7.57.49)."""
    return _memory_map_elements(_require_map_or_local(memoryMapOrLocalMemoryMapID))


def getMemoryMapElementType(memoryMapElementID: str) -> str:
    """Return addressBlock, bank or subSpaceMap for a typed element handle (F.7.57.50)."""
    if not isinstance(memoryMapElementID, str):
        raise TgiError("Invalid memory-map element handle", TgiFaultCode.INVALID_ID)
    element = resolve_handle(memoryMapElementID)
    if isinstance(element, (AddressBlock, BankedBlockType)):
        return "addressBlock"
    if isinstance(element, _BANK_TYPES + _BANK_CHILD_TYPES + _LOCAL_BANK_TYPES):
        return "bank"
    if isinstance(element, (SubspaceMap, BankedSubspaceType)):
        return "subSpaceMap"
    raise TgiError("Invalid memory-map element handle", TgiFaultCode.INVALID_ID)


def _memory_map_definition_reference(
    memoryMapID: str,
) -> tuple[MemoryMapType, MemoryMapType.MemoryMapDefinitionRef | None]:
    owner = _require_memory_map(memoryMapID)
    values = _memory_map_choice(owner)
    reference = next((item for item in values if isinstance(item, MemoryMapType.MemoryMapDefinitionRef)), None)
    if reference is not None:
        _type_definition_reference_names(reference.value, reference.type_definitions)
        register_parent(reference, owner, ("choice",), "list")
    return owner, reference


def getMemoryMapMemoryMapDefinitionRefByExternalTypeDefID(memoryMapID: str) -> str | None:
    """Return the named local externalTypeDefinitions declaration handle (F.7.57.51)."""
    owner, reference = _memory_map_definition_reference(memoryMapID)
    if reference is None:
        return None
    _name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return get_handle(_type_definition_external(owner, external))


def getMemoryMapMemoryMapDefinitionRefByID(memoryMapID: str) -> str | None:
    """Resolve the actual memoryMapDefinition in its declared registered library (F.7.57.52)."""
    owner, reference = _memory_map_definition_reference(memoryMapID)
    if reference is None:
        return None
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return _type_definition_target(owner, name, external, getTypeDefinitionsMemoryMapDefinitionIDs)


def getMemoryMapMemoryMapDefinitionRefByName(memoryMapID: str) -> str | None:
    """Return stored normalized definition Name without resolving its target (F.7.57.53)."""
    _owner, reference = _memory_map_definition_reference(memoryMapID)
    return (
        _type_definition_reference_names(reference.value, reference.type_definitions)[0]
        if reference is not None
        else None
    )


def getMemoryMapMemoryMapDefinitionRefID(memoryMapID: str) -> str | None:
    """Return the owned reference wrapper handle, independent of target availability (F.7.57.54)."""
    _owner, reference = _memory_map_definition_reference(memoryMapID)
    return get_handle(reference) if reference is not None else None


def _map_collection_ids[T](owner: MemoryMapType, model_type: type[T]) -> list[str]:
    """Return typed direct children with immediate choice ownership and descendant handles."""
    values = _memory_map_choice(owner)
    return _child_ids(owner, [item for item in values if isinstance(item, model_type)], ("choice",))


def _require_memory_remap(memoryRemapID: str) -> MemoryRemapType:
    if not isinstance(memoryRemapID, str):
        raise TgiError("Invalid memoryRemap handle", TgiFaultCode.INVALID_ID)
    remap = resolve_handle(memoryRemapID)
    if not isinstance(remap, MemoryRemapType):
        raise TgiError("Invalid memoryRemap handle", TgiFaultCode.INVALID_ID)
    return remap


def _remap_choice(remap: MemoryRemapType) -> list | tuple:
    """Validate stored remap branches without resolving external definitions."""
    values = remap.choice
    if not isinstance(values, (list, tuple)):
        raise TgiError("Invalid memoryRemap choice", TgiFaultCode.INVALID_ID)
    references = [item for item in values if isinstance(item, MemoryRemapType.RemapDefinitionRef)]
    if references:
        if len(values) != 1:
            raise TgiError("Conflicting remap definition and inline content", TgiFaultCode.INVALID_ID)
        return values
    if any(not isinstance(item, (AddressBlock, Bank, SubspaceMap)) for item in values):
        raise TgiError("Invalid memoryRemap choice child", TgiFaultCode.INVALID_ID)
    return values


def _remap_elements(remap: MemoryRemapType) -> list[str]:
    """Read ordered inline remap children, rejecting conflicting definition branches."""
    values = _remap_choice(remap)
    if any(isinstance(item, MemoryRemapType.RemapDefinitionRef) for item in values):
        return []
    return _child_ids(remap, values, ("choice",))


def getMemoryMapMemoryRemapIDs(memoryMapID: str) -> list[str]:
    """Return ordered direct memoryRemap handles from a memoryMap (F.7.57.55)."""
    return _map_collection_ids(_require_memory_map(memoryMapID), MemoryRemap)


def getMemoryMapRemapIDs(memoryMapOrLocalMemoryMapID: str) -> list[str]:
    """Return direct remap handles; the local-map schema contains no remaps (F.7.57.56)."""
    owner = _require_map_or_local(memoryMapOrLocalMemoryMapID)
    if isinstance(owner, LocalMemoryMapType):
        _memory_map_elements(owner)
        return []
    return _map_collection_ids(owner, MemoryRemap)


def getMemoryMapShared(memoryMapOrLocalMemoryMapID: str) -> str | None:
    """Return stored shared value or the inline memory-map default undefined (F.7.57.57).

    Local maps have no shared property in the schema. Definition-reference values
    require definition expansion; both return None rather than inventing content.
    """
    owner = _require_map_or_local(memoryMapOrLocalMemoryMapID)
    if isinstance(owner, LocalMemoryMapType):
        _memory_map_elements(owner)
        return None
    values = _memory_map_choice(owner)
    if any(isinstance(item, MemoryMapType.MemoryMapDefinitionRef) for item in values):
        return None
    shared = next((item for item in values if isinstance(item, SharedType)), SharedType.UNDEFINED)
    return shared.value


def getMemoryMapSubspaceMapIDs(memoryMapID: str) -> list[str]:
    """Return ordered direct subspaceMap handles from a memoryMap (F.7.57.58)."""
    return _map_collection_ids(_require_memory_map(memoryMapID), SubspaceMap)


def getMemoryRemapAddressBlockIDs(memoryRemapID: str) -> list[str]:
    """Return ordered direct addressBlock handles from a memoryRemap (F.7.57.59)."""
    return [
        handle
        for handle in _remap_elements(_require_memory_remap(memoryRemapID))
        if isinstance(resolve_handle(handle), AddressBlock)
    ]


def getMemoryRemapBankIDs(memoryRemapID: str) -> list[str]:
    """Return ordered direct bank handles from a memoryRemap (F.7.57.60)."""
    return [
        handle
        for handle in _remap_elements(_require_memory_remap(memoryRemapID))
        if isinstance(resolve_handle(handle), Bank)
    ]


def getMemoryRemapElementIDs(memoryRemapID: str) -> list[str]:
    """Return ordered direct banks, addressBlocks and subspaceMaps from a remap (F.7.57.61)."""
    return _remap_elements(_require_memory_remap(memoryRemapID))


def getMemoryRemapSubspaceMapIDs(memoryRemapID: str) -> list[str]:
    """Return ordered direct subspaceMap handles from a memoryRemap (F.7.57.69)."""
    return [
        handle
        for handle in _remap_elements(_require_memory_remap(memoryRemapID))
        if isinstance(resolve_handle(handle), SubspaceMap)
    ]


# ---------------------------------------------------------------------------
# EXTENDED (F.7.58)
# ---------------------------------------------------------------------------


def addMemoryMapAddressBlock(memoryMapID: str, name: str) -> str:
    """Create a new ``addressBlock`` under a memory map.

    Section: F.7.58.11 (core portion). Only name is required here; additional
    properties can be assigned via dedicated setters (range, width, baseAddress, etc.).
    """
    mm = _require_memory_map(memoryMapID)
    from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType

    ab = AddressBlockType(name=name)
    mm.address_block.append(ab)  # type: ignore[attr-defined]
    register_parent(ab, mm, ("address_block",), "list")
    return get_handle(ab)


def addMemoryMapBank(memoryMapID: str, name: str) -> str:
    """Add a ``bank`` to the memory map.

    Section: F.7.58.12.
    """
    mm = _require_memory_map(memoryMapID)
    from org.accellera.ipxact.v1685_2022.bank import Bank

    bk = Bank(name=name)
    mm.bank.append(bk)  # type: ignore[attr-defined]
    register_parent(bk, mm, ("bank",), "list")
    return get_handle(bk)


def addMemoryMapMemoryRemap(memoryMapID: str, name: str) -> str:
    """Add a ``memoryRemap`` element.

    Section: F.7.58.13.
    """
    mm = _require_memory_map(memoryMapID)
    from org.accellera.ipxact.v1685_2022.memory_remap_type import MemoryRemapType

    remap = MemoryRemapType(name=name)
    mm.memory_remap.append(remap)  # type: ignore[attr-defined]
    register_parent(remap, mm, ("memory_remap",), "list")
    return get_handle(remap)


def addMemoryMapSubspaceMap(memoryMapID: str, name: str, addressOffset: int | None = None) -> str:
    """Add a ``subspaceMap`` to the memory map.

    Section: F.7.58.14. Supports optional base address offset.
    """
    mm = _require_memory_map(memoryMapID)
    from org.accellera.ipxact.v1685_2022.subspace_map import SubspaceMap
    from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression

    sm = SubspaceMap(name=name)
    if addressOffset is not None:
        sm.base_address = UnsignedLongintExpression(value=str(addressOffset))  # type: ignore[arg-type]
    mm.subspace_map.append(sm)  # type: ignore[attr-defined]
    register_parent(sm, mm, ("subspace_map",), "list")
    return get_handle(sm)


def removeMemoryMapMemoryRemap(memoryRemapID: str) -> bool:
    """Remove a ``memoryRemap`` element.

    Section: F.7.58.40.
    """
    obj = resolve_handle(memoryRemapID)
    from org.accellera.ipxact.v1685_2022.memory_remap_type import MemoryRemapType

    if not isinstance(obj, MemoryRemapType):
        raise TgiError("Invalid memoryRemap handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(memoryRemapID)


def removeMemoryMapSubspaceMap(subspaceMapID: str) -> bool:
    """Remove a ``subspaceMap`` element.

    Section: F.7.58.42.
    """
    obj = resolve_handle(subspaceMapID)
    from org.accellera.ipxact.v1685_2022.subspace_map import SubspaceMap

    if not isinstance(obj, SubspaceMap):
        raise TgiError("Invalid subspaceMap handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(subspaceMapID)


def removeMemoryMapShared(memoryMapID: str) -> bool:
    """Remove an explicit ``shared`` value from an inline memory map (F.7.58.41)."""
    memory_map = _require_memory_map(memoryMapID)
    values = _memory_map_choice(memory_map)
    if any(isinstance(item, MemoryMapType.MemoryMapDefinitionRef) for item in values):
        return False
    shared_index = next((index for index, item in enumerate(values) if isinstance(item, SharedType)), None)
    if shared_index is None:
        return False
    if isinstance(values, tuple):
        values = list(values)
        memory_map.choice = values
    del values[shared_index]
    return True


def setMemoryMapMemoryMapDefinitionRef(memoryMapID: str, value: str, typeDefinitions: str) -> bool:
    """Set a named ``memoryMapDefinitionRef`` or replace the complete inline choice (F.7.58.67)."""
    memory_map, reference = _memory_map_definition_reference(memoryMapID)
    try:
        definition_name = _name(value, "Name")
        type_definitions_name = _name(typeDefinitions, "Name")
    except TgiError as error:
        raise TgiError("Invalid memoryMap definition reference Name", TgiFaultCode.INVALID_ARGUMENT) from error

    if reference is not None:
        reference.value = definition_name
        reference.type_definitions = type_definitions_name
        return True

    values = _memory_map_choice(memory_map)
    for child in values:
        if isinstance(child, SharedType):
            continue
        register_parent(child, memory_map, ("choice",), "list")
        _register_graph(child)
    memory_map.choice = list(values)  # type: ignore[assignment]
    for child in values:
        if isinstance(child, SharedType):
            continue
        if not detach_child_by_handle(get_handle(child)):
            raise TgiError("Could not replace memoryMap inline definition", TgiFaultCode.INVALID_ID)

    reference = MemoryMapType.MemoryMapDefinitionRef(value=definition_name, type_definitions=type_definitions_name)
    memory_map.choice = [reference]  # type: ignore[assignment]
    register_parent(reference, memory_map, ("choice",), "list")
    return True


def setMemoryMapShared(memoryMapID: str, shared: str) -> bool:
    """Set the schema sharedness enum on an inline memory map (F.7.58.68)."""
    memory_map = _require_memory_map(memoryMapID)
    if type(shared) is not str:
        raise TgiError("shared must be a string enum value", TgiFaultCode.INVALID_ARGUMENT)
    try:
        shared_value = SharedType(shared)
    except ValueError as error:
        raise TgiError("Invalid memoryMap shared value", TgiFaultCode.INVALID_ARGUMENT) from error

    values = _memory_map_choice(memory_map)
    if any(isinstance(item, MemoryMapType.MemoryMapDefinitionRef) for item in values):
        raise TgiError("shared cannot be set on a memoryMapDefinitionRef", TgiFaultCode.INVALID_ARGUMENT)
    shared_index = next((index for index, item in enumerate(values) if isinstance(item, SharedType)), None)
    if isinstance(values, tuple):
        values = list(values)
        memory_map.choice = values
    if shared_index is not None:
        values[shared_index] = shared_value
        return True

    unit_index = next((index for index, item in enumerate(values) if isinstance(item, AddressUnitBits)), None)
    if unit_index is not None:
        values.insert(unit_index + 1, shared_value)
    else:
        values.append(shared_value)
    return True


def _stored_name(source: str) -> str:
    """Validate and normalize a stored XML Name without modifying the source."""
    try:
        return _name(source, "Name")
    except TgiError as error:
        raise TgiError("Invalid stored reference Name", TgiFaultCode.INVALID_ID) from error


def _remap_mode_refs(remap: MemoryRemapType) -> list | tuple:
    values = remap.mode_ref
    if not isinstance(values, (list, tuple)) or any(not isinstance(item, ModeRef) for item in values):
        raise TgiError("Invalid memoryRemap modeRef collection", TgiFaultCode.INVALID_ID)
    for item in values:
        _stored_name(item.value)
    return values


def getMemoryRemapModeRefIDs(memoryRemapID: str) -> list[str]:
    """Return ordered owned modeRef handles (F.7.57.64)."""
    remap = _require_memory_remap(memoryRemapID)
    return _child_ids(remap, _remap_mode_refs(remap), ("mode_ref",))


def getMemoryRemapModeRefByNames(memoryRemapID: str) -> list[str]:
    """Return ordered referenced mode Names without modifying their sources (F.7.57.63)."""
    remap = _require_memory_remap(memoryRemapID)
    return [_stored_name(item.value) for item in _remap_mode_refs(remap)]


def getMemoryRemapModeRefByID(memoryRemapID: str, modeRef: str) -> str:
    """Resolve an owned modeRef HANDLE to its containing component's mode (F.7.57.62)."""
    remap = _require_memory_remap(memoryRemapID)
    if not isinstance(modeRef, str):
        raise TgiError("Invalid memoryRemap modeRef handle", TgiFaultCode.INVALID_ID)
    reference = resolve_handle(modeRef)
    refs = _remap_mode_refs(remap)
    if not isinstance(reference, ModeRef) or not any(item is reference for item in refs):
        raise TgiError("modeRef does not belong to memoryRemap", TgiFaultCode.INVALID_ID)
    _child_ids(remap, refs, ("mode_ref",))
    target = _named_target(remap, "modes.mode", "name", _stored_name(reference.value))
    if not isinstance(target, ComponentType.Modes.Mode):
        raise TgiError("Invalid referenced component mode", TgiFaultCode.INVALID_ID)
    return get_handle(target)


def _require_subspace(handle: str) -> SubspaceRefType:
    if not isinstance(handle, str):
        raise TgiError("Invalid subspaceMap handle", TgiFaultCode.INVALID_ID)
    subspace = resolve_handle(handle)
    if not isinstance(subspace, SubspaceRefType):
        raise TgiError("Invalid subspaceMap handle", TgiFaultCode.INVALID_ID)
    return subspace


def _subspace_base(handle: str) -> SignedLongintExpression:
    subspace = _require_subspace(handle)
    node = _child(subspace, "base_address", SignedLongintExpression)
    if node is None:
        raise TgiError("Missing required subspace baseAddress", TgiFaultCode.INVALID_ID)
    return node


def getSubspaceMapBaseAddress(subSpaceMapID: str) -> int:
    """Evaluate the signed 64-bit subspace baseAddress and declared bounds (F.7.57.70)."""
    node = _subspace_base(subSpaceMapID)
    if not isinstance(node.value, str):
        raise TgiError("Invalid subspace baseAddress source", TgiFaultCode.INVALID_ID)
    value = _integer(node.value, (1 << 63) - 1, minimum=-(1 << 63))
    assert value is not None
    for bound in (node.minimum, node.maximum):
        if bound is not None and type(bound) is not int:
            raise TgiError("Invalid declared baseAddress bound", TgiFaultCode.INVALID_ID)
    if (node.minimum is not None and value < node.minimum) or (node.maximum is not None and value > node.maximum):
        raise TgiError("baseAddress outside declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def getSubspaceMapBaseAddressExpression(subSpaceMapID: str) -> str:
    """Return original subspace baseAddress source without evaluation (F.7.57.71)."""
    node = _subspace_base(subSpaceMapID)
    if not isinstance(node.value, str):
        raise TgiError("Invalid subspace baseAddress source", TgiFaultCode.INVALID_ID)
    return node.value


def getSubspaceMapBaseAddressID(subspaceMapID: str) -> str:
    """Return the owned required signed baseAddress wrapper handle (F.7.57.72)."""
    return get_handle(_subspace_base(subspaceMapID))


def getSubspaceMapSegmentRefByName(subSpaceID: str) -> str | None:
    """Return optional segmentRef XML Name source on a subspace element (F.7.57.73)."""
    subspace = _require_subspace(subSpaceID)
    return _stored_name(subspace.segment_ref) if subspace.segment_ref is not None else None


def _require_address_block(addressBlockID: str, *, banked: bool = True) -> AddressBlockType | BankedBlockType:
    if not isinstance(addressBlockID, str):
        raise TgiError("Invalid addressBlock handle", TgiFaultCode.INVALID_ID)
    block = resolve_handle(addressBlockID)
    allowed = (AddressBlockType, BankedBlockType) if banked else (AddressBlockType,)
    if not isinstance(block, allowed):
        raise TgiError("Invalid addressBlock handle", TgiFaultCode.INVALID_ID)
    return block


type _BlockContent = AddressBlockType | BankedBlockType | AddressBlockDefinitions.AddressBlockDefinition


def _address_block_choice(block: AddressBlockType) -> list | tuple:
    values = block.choice
    allowed = (
        str,
        UnsignedPositiveLongintExpression,
        UnsignedPositiveIntExpression,
        UsageType,
        Volatile,
        AccessPolicies,
        Parameters,
        AddressBlockType.Register,
        RegisterFile,
        AddressBlockType.AddressBlockDefinitionRef,
    )
    if not isinstance(values, (list, tuple)) or any(not isinstance(item, allowed) for item in values):
        raise TgiError("Invalid addressBlock choice", TgiFaultCode.INVALID_ID)
    refs = [item for item in values if isinstance(item, AddressBlockType.AddressBlockDefinitionRef)]
    if refs and len(values) != 1:
        raise TgiError("Conflicting addressBlock definition and inline content", TgiFaultCode.INVALID_ID)
    for scalar in (
        str,
        UnsignedPositiveLongintExpression,
        UnsignedPositiveIntExpression,
        UsageType,
        Volatile,
        AccessPolicies,
        Parameters,
    ):
        if sum(isinstance(item, scalar) for item in values) > 1:
            raise TgiError("Duplicate addressBlock scalar child", TgiFaultCode.INVALID_ID)
    return values


def _address_block_definition_reference(
    addressBlockID: str,
) -> tuple[AddressBlockType | BankedBlockType, AddressBlockType.AddressBlockDefinitionRef | None]:
    block = _require_address_block(addressBlockID)
    if isinstance(block, BankedBlockType):
        return block, None
    values = _address_block_choice(block)
    reference = next((item for item in values if isinstance(item, AddressBlockType.AddressBlockDefinitionRef)), None)
    if reference is not None:
        _type_definition_reference_names(reference.value, reference.type_definitions)
        register_parent(reference, block, ("choice",), "list")
    return block, reference


def _address_block_content(block: AddressBlockType | BankedBlockType) -> _BlockContent:
    """Validate inline content or resolve the declared external block definition."""
    _block, reference = _address_block_definition_reference(get_handle(block))
    if reference is None:
        return block
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    target_id = _type_definition_target(block, name, external, getTypeDefinitionsAddressBlockDefinitionIDs)
    definition = resolve_handle(target_id)
    if not isinstance(definition, AddressBlockDefinitions.AddressBlockDefinition):
        raise TgiError("Invalid addressBlockDefinition target", TgiFaultCode.INVALID_ID)
    return definition


def _block_scalar[T](content: _BlockContent, attribute: str, model_type: type[T]) -> T | None:
    if not isinstance(content, AddressBlockType):
        if model_type is UsageType:
            node = content.usage
            if node is not None and not isinstance(node, UsageType):
                raise TgiError("Invalid addressBlock usage value", TgiFaultCode.INVALID_ID)
            return node
        return _child(content, attribute, model_type)
    node = next((item for item in content.choice if isinstance(item, model_type)), None)
    if node is not None and model_type is not UsageType:
        register_parent(node, content, ("choice",), "list")
    return node


def _address_block_size_node[T: UnsignedPositiveLongintExpression | UnsignedPositiveIntExpression](
    block: AddressBlockType | BankedBlockType, attribute: str, model_type: type[T]
) -> T:
    node = _block_scalar(_address_block_content(block), attribute, model_type)
    if node is None:
        raise TgiError(f"Missing required addressBlock {attribute}", TgiFaultCode.INVALID_ID)
    return node


def _address_block_base(addressBlockID: str) -> BaseAddress:
    block = _require_address_block(addressBlockID, banked=False)
    node = _child(block, "base_address", BaseAddress)
    if node is None:
        raise TgiError("Missing required addressBlock baseAddress", TgiFaultCode.INVALID_ID)
    return node


def _block_expression_source(
    node: BaseAddress | UnsignedPositiveLongintExpression | UnsignedPositiveIntExpression,
) -> str:
    if not isinstance(node.value, str):
        raise TgiError("Invalid addressBlock expression source", TgiFaultCode.INVALID_ID)
    return node.value


def _block_expression_value(
    node: BaseAddress | UnsignedPositiveLongintExpression | UnsignedPositiveIntExpression,
    label: str,
    minimum: int,
    maximum: int,
) -> int:
    _block_expression_source(node)
    value = _numeric(node, label, minimum, maximum)
    assert value is not None
    return value


def getAddressBlockBaseAddress(addressBlockID: str) -> int:
    """Return evaluated unsigned 64-bit baseAddress (F.7.57.7)."""
    return _block_expression_value(_address_block_base(addressBlockID), "baseAddress", 0, (1 << 64) - 1)


def getAddressBlockBaseAddressExpression(addressBlockID: str) -> str:
    """Return original local baseAddress source (F.7.57.8)."""
    return _block_expression_source(_address_block_base(addressBlockID))


def getAddressBlockBaseAddressID(addressBlockID: str) -> str:
    """Return the owned local baseAddress wrapper handle (F.7.57.9)."""
    return get_handle(_address_block_base(addressBlockID))


def getAddressBlockRange(addressBlockID: str) -> int:
    """Return evaluated positive unsigned 64-bit inline or referenced range (F.7.57.10)."""
    node = _address_block_size_node(_require_address_block(addressBlockID), "range", UnsignedPositiveLongintExpression)
    return _block_expression_value(node, "range", 1, (1 << 64) - 1)


def getAddressBlockRangeExpression(addressBlockID: str) -> str:
    """Return original inline or referenced range source (F.7.57.11)."""
    node = _address_block_size_node(_require_address_block(addressBlockID), "range", UnsignedPositiveLongintExpression)
    return _block_expression_source(node)


def getAddressBlockRangeID(addressBlockID: str) -> str:
    """Return the actual owned inline or definition range wrapper handle (F.7.57.12)."""
    return get_handle(
        _address_block_size_node(_require_address_block(addressBlockID), "range", UnsignedPositiveLongintExpression)
    )


def getAddressBlockWidth(addressBlockID: str) -> int:
    """Return evaluated positive unsigned 32-bit inline or referenced width (F.7.57.19)."""
    node = _address_block_size_node(_require_address_block(addressBlockID), "width", UnsignedPositiveIntExpression)
    return _block_expression_value(node, "width", 1, (1 << 32) - 1)


def getAddressBlockWidthExpression(addressBlockID: str) -> str:
    """Return original inline or referenced width source (F.7.57.20)."""
    node = _address_block_size_node(_require_address_block(addressBlockID), "width", UnsignedPositiveIntExpression)
    return _block_expression_source(node)


def getAddressBlockWidthID(addressBlockID: str) -> str:
    """Return the actual owned inline or definition width wrapper handle (F.7.57.21)."""
    return get_handle(
        _address_block_size_node(_require_address_block(addressBlockID), "width", UnsignedPositiveIntExpression)
    )


def _block_register_ids(content: _BlockContent, *, files: bool = False) -> list[str]:
    """Return typed direct register or register-file handles from the actual content owner."""
    if isinstance(content, AddressBlockType):
        values, path, register_type = content.choice, "choice", AddressBlockType.Register
    else:
        values, path = content.register_or_register_file, "register_or_register_file"
        register_type = (
            BankedBlockType.Register
            if isinstance(content, BankedBlockType)
            else AddressBlockDefinitions.AddressBlockDefinition.Register
        )
        if not isinstance(values, (list, tuple)) or any(
            not isinstance(item, (register_type, RegisterFile)) for item in values
        ):
            raise TgiError("Invalid addressBlock register collection", TgiFaultCode.INVALID_ID)
    model_type = RegisterFile if files else register_type
    return _child_ids(content, [item for item in values if isinstance(item, model_type)], (path,))


def getAddressBlockAccessPolicyIDs(addressBlockID: str) -> list[str]:
    """Return owned accessPolicy children from inline or referenced block content (F.7.57.1)."""
    content = _address_block_content(_require_address_block(addressBlockID))
    holder = _block_scalar(content, "access_policies", AccessPolicies)
    if holder is None:
        return []
    values = holder.access_policy
    if not isinstance(values, (list, tuple)) or any(
        not isinstance(item, AccessPolicies.AccessPolicy) for item in values
    ):
        raise TgiError("Invalid addressBlock accessPolicy collection", TgiFaultCode.INVALID_ID)
    return _child_ids(holder, values, ("access_policy",))


def getAddressBlockArrayID(addressBlockID: str) -> str | None:
    """Return the optional local array wrapper handle (F.7.57.6)."""
    block = _require_address_block(addressBlockID)
    if isinstance(block, BankedBlockType):
        return None
    array = _child(block, "array", Array)
    return get_handle(array) if array is not None else None


def getAddressBlockRefIndexIDs(addressBlockRefID: str) -> list[str]:
    """Return ordered owned Index wrappers without evaluating their expressions (F.7.57.13)."""
    reference = _register_reference(addressBlockRefID, AddressBlockRef)
    indices = _child(reference, "indices", Indices)
    if indices is None:
        return []
    values = indices.index
    if not isinstance(values, (list, tuple)) or any(not isinstance(item, Index) for item in values):
        raise TgiError("Invalid addressBlockRef indices", TgiFaultCode.INVALID_ID)
    return _child_ids(indices, values, ("index",))


def getAddressBlockRegisterFileIDs(addressBlockID: str) -> list[str]:
    """Return ordered direct registerFile children from actual block content (F.7.57.14)."""
    return _block_register_ids(_address_block_content(_require_address_block(addressBlockID)), files=True)


def getAddressBlockRegisterIDs(addressBlockID: str) -> list[str]:
    """Return ordered direct register children from actual block content (F.7.57.15)."""
    return _block_register_ids(_address_block_content(_require_address_block(addressBlockID)))


def getAddressBlockTypeIdentifier(addressBlockID: str) -> str | None:
    """Return optional typeIdentifier Name; banked blocks have no such property (F.7.57.16)."""
    content = _address_block_content(_require_address_block(addressBlockID))
    if isinstance(content, BankedBlockType):
        return None
    value = (
        next((item for item in content.choice if isinstance(item, str)), None)
        if isinstance(content, AddressBlockType)
        else content.type_identifier
    )
    return _stored_name(value) if value is not None else None


def getAddressBlockUsage(addressBlockID: str) -> str:
    """Return explicit usage or its standard register/reserved presumption (F.7.57.17)."""
    content = _address_block_content(_require_address_block(addressBlockID))
    usage = _block_scalar(content, "usage", UsageType)
    if usage is not None:
        return usage.value
    direct = [resolve_handle(handle) for handle in _block_register_ids(content)]
    files = [resolve_handle(handle) for handle in _block_register_ids(content, files=True)]
    if direct or any(isinstance(obj, RegisterFile.Register) for file in files for obj, *_ in _walk_model(file)):
        return UsageType.REGISTER.value
    return UsageType.RESERVED.value


def getAddressBlockVolatility(addressBlockID: str) -> bool | None:
    """Return explicit volatility; absence is unspecified for address blocks (F.7.57.18)."""
    content = _address_block_content(_require_address_block(addressBlockID))
    node = _block_scalar(content, "volatile", Volatile)
    if node is None:
        return None
    if type(node.value) is not bool:
        raise TgiError("Invalid addressBlock volatile value", TgiFaultCode.INVALID_ID)
    return node.value


def getAddressBlockAddressBlockDefinitionRefByExternalTypeDefID(addressBlockID: str) -> str | None:
    """Return the named local externalTypeDefinitions declaration handle (F.7.57.2)."""
    owner, reference = _address_block_definition_reference(addressBlockID)
    if reference is None:
        return None
    _name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return get_handle(_type_definition_external(owner, external))


def getAddressBlockAddressBlockDefinitionRefByID(addressBlockID: str) -> str | None:
    """Resolve the actual addressBlockDefinition in its declared registered library (F.7.57.3)."""
    owner, reference = _address_block_definition_reference(addressBlockID)
    if reference is None:
        return None
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return _type_definition_target(owner, name, external, getTypeDefinitionsAddressBlockDefinitionIDs)


def getAddressBlockAddressBlockDefinitionRefByName(addressBlockID: str) -> str | None:
    """Return stored normalized definition Name without resolving its target (F.7.57.4)."""
    _owner, reference = _address_block_definition_reference(addressBlockID)
    return (
        _type_definition_reference_names(reference.value, reference.type_definitions)[0]
        if reference is not None
        else None
    )


def getAddressBlockAddressBlockDefinitionRefID(addressBlockID: str) -> str | None:
    """Return the owned reference wrapper handle, independent of target availability (F.7.57.5)."""
    _owner, reference = _address_block_definition_reference(addressBlockID)
    return get_handle(reference) if reference is not None else None


type _Bank = (
    AddressBankType
    | BankedBankType
    | AddressBankDefinitionType
    | BankedDefinitionBankType
    | BankedBankType.Bank
    | BankedDefinitionBankType.Bank
    | LocalAddressBankType
    | LocalBankedBankType
)
type _BankReference = (
    AddressBankType.BankDefinitionRef
    | BankedBankType.BankDefinitionRef
    | AddressBankDefinitionType.BankDefinitionRef
    | BankedDefinitionBankType.BankDefinitionRef
)
type _BankContent = _Bank | BankDefinitions.BankDefinition


_BANK_TYPES = (AddressBankType, BankedBankType, AddressBankDefinitionType, BankedDefinitionBankType)
_LOCAL_BANK_TYPES = (LocalAddressBankType, LocalBankedBankType)
_BANK_CHILD_TYPES = (
    AddressBankType.Bank,
    BankedBankType.Bank,
    AddressBankDefinitionType.Bank,
    BankedDefinitionBankType.Bank,
    BankDefinitions.BankDefinition.Bank,
)


def _require_bank(handle: str, *, local: bool = False) -> _Bank:
    bank = resolve_handle(handle) if isinstance(handle, str) else None
    allowed = _BANK_TYPES + _BANK_CHILD_TYPES + (_LOCAL_BANK_TYPES if local else ())
    if not isinstance(bank, allowed):
        raise TgiError("Invalid bank handle", TgiFaultCode.INVALID_ID)
    return bank


def _bank_storage(bank: _BankContent) -> tuple[list | tuple, str, tuple[type, ...], type | None]:
    """Validate the actual bank container and its model-specific choice branches."""
    if isinstance(bank, _LOCAL_BANK_TYPES):
        path, bank_type, ref_type = "address_block_or_bank", LocalBankedBankType, None
        allowed = (BankedBlockType, bank_type)
    elif isinstance(bank, BankDefinitions.BankDefinition):
        path, bank_type, ref_type = "address_block_or_bank", BankDefinitions.BankDefinition.Bank, None
        allowed = (BankedBlockType, bank_type)
    else:
        model = next((model for model in _BANK_TYPES if isinstance(bank, model)), None)
        if model is None:
            raise TgiError("Bank model has no content container", TgiFaultCode.INVALID_ID)
        path, bank_type, ref_type = "choice", model.Bank, model.BankDefinitionRef
        allowed = (ref_type, BankedBlockType, bank_type, UsageType, Volatile, AccessPolicies, Parameters)
        if model in (AddressBankType, BankedBankType):
            allowed += (BankedSubspaceType,)
    try:
        values = getattr(bank, path)
    except AttributeError as error:
        raise TgiError("Bank model has no supported content container", TgiFaultCode.INVALID_ID) from error
    if not isinstance(values, (list, tuple)) or any(not isinstance(item, allowed) for item in values):
        raise TgiError("Invalid bank content", TgiFaultCode.INVALID_ID)
    if ref_type is not None and any(isinstance(item, ref_type) for item in values) and len(values) != 1:
        raise TgiError("Conflicting bank definition and inline content", TgiFaultCode.INVALID_ID)
    for scalar in (UsageType, Volatile, AccessPolicies, Parameters):
        if sum(isinstance(item, scalar) for item in values) > 1:
            raise TgiError("Duplicate bank scalar child", TgiFaultCode.INVALID_ID)
    return values, path, (BankedBlockType, bank_type, BankedSubspaceType), ref_type


def _bank_definition_reference(bankID: str) -> tuple[_Bank, _BankReference | None]:
    bank = _require_bank(bankID)
    values, path, _types, ref_type = _bank_storage(bank)
    reference = next((item for item in values if ref_type is not None and isinstance(item, ref_type)), None)
    if reference is not None:
        _type_definition_reference_names(reference.value, reference.type_definitions)
        register_parent(reference, bank, (path,), "list")
    return bank, reference


def _bank_content(bank: _Bank) -> _BankContent:
    if isinstance(bank, _LOCAL_BANK_TYPES):
        _bank_storage(bank)
        return bank
    _bank, reference = _bank_definition_reference(get_handle(bank))
    if reference is None:
        return bank
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    target = resolve_handle(_type_definition_target(bank, name, external, getTypeDefinitionsBankDefinitionIDs))
    if not isinstance(target, BankDefinitions.BankDefinition):
        raise TgiError("Invalid bankDefinition target", TgiFaultCode.INVALID_ID)
    _bank_storage(target)
    return target


def _remap_definition_reference(
    memoryRemapID: str,
) -> tuple[MemoryRemapType, MemoryRemapType.RemapDefinitionRef | None]:
    remap = _require_memory_remap(memoryRemapID)
    values = _remap_choice(remap)
    reference = next((item for item in values if isinstance(item, MemoryRemapType.RemapDefinitionRef)), None)
    if reference is not None:
        _type_definition_reference_names(reference.value, reference.type_definitions)
        register_parent(reference, remap, ("choice",), "list")
    return remap, reference


def _bank_element_ids(bank: _Bank) -> list[str]:
    content = _bank_content(bank)
    values, path, types, _ref_type = _bank_storage(content)
    return _child_ids(content, [item for item in values if isinstance(item, types)], (path,))


def getBankAddressBlockIDs(bankID: str) -> list[str]:
    """Return owned direct inline or referenced block handles (F.7.57.31)."""
    return [
        handle
        for handle in _bank_element_ids(_require_bank(bankID))
        if isinstance(resolve_handle(handle), BankedBlockType)
    ]


def getBankBankIDs(bankID: str) -> list[str]:
    """Return owned direct nested bank handles in stored order (F.7.57.36)."""
    return [
        handle
        for handle in _bank_element_ids(_require_bank(bankID))
        if isinstance(resolve_handle(handle), _BANK_TYPES + _BANK_CHILD_TYPES)
    ]


def _bank_base(handle: str, *, local: bool) -> BaseAddress:
    bank = _require_bank(handle, local=local)
    if not isinstance(bank, (AddressBankType, AddressBankDefinitionType, LocalAddressBankType)):
        raise TgiError("Bank model has no baseAddress", TgiFaultCode.INVALID_ID)
    node = _child(bank, "base_address", BaseAddress)
    if node is None:
        raise TgiError("Missing required bank baseAddress", TgiFaultCode.INVALID_ID)
    return node


def getBankBaseAddress(bankOrLocalBankID: str) -> int:
    """Evaluate the explicit unsigned 64-bit bank baseAddress (F.7.57.37)."""
    return _block_expression_value(_bank_base(bankOrLocalBankID, local=True), "baseAddress", 0, (1 << 64) - 1)


def getBankBaseAddressExpression(bankOrLocalBankID: str) -> str:
    """Return the original bank baseAddress source (F.7.57.38)."""
    return _block_expression_source(_bank_base(bankOrLocalBankID, local=True))


def getBankBaseAddressID(bankID: str) -> str:
    """Return the owned explicit nonlocal bank baseAddress wrapper (F.7.57.39)."""
    return get_handle(_bank_base(bankID, local=False))


def getBankBlockAndSubspaceElementIDs(bankOrLocalBankID: str) -> list[str]:
    """Return owned direct bank/block/subspace handles in stored order (F.7.57.40)."""
    return _bank_element_ids(_require_bank(bankOrLocalBankID, local=True))


def getBankSubspaceMapIDs(bankID: str) -> list[str]:
    """Return direct banked subspace handles; definitions have none (F.7.57.41)."""
    return [
        handle
        for handle in _bank_element_ids(_require_bank(bankID))
        if isinstance(resolve_handle(handle), BankedSubspaceType)
    ]


def _bank_scalar[T](bank: _Bank, attribute: str, model_type: type[T]) -> T | None:
    content = _bank_content(bank)
    if isinstance(content, _LOCAL_BANK_TYPES + (BankDefinitions.BankDefinition,)):
        if model_type is UsageType:
            value = content.usage
            if value is not None and not isinstance(value, UsageType):
                raise TgiError("Invalid bank usage", TgiFaultCode.INVALID_ID)
            return value
        return _child(content, attribute, model_type)
    values, path, _types, _ref_type = _bank_storage(content)
    node = next((item for item in values if isinstance(item, model_type)), None)
    if node is not None and model_type is not UsageType:
        register_parent(node, content, (path,), "list")
    return node


def getBankUsage(bankOrLocalBankID: str) -> str | None:
    """Return explicit bank usage; absence permits mixed child usage (F.7.57.42)."""
    node = _bank_scalar(_require_bank(bankOrLocalBankID, local=True), "usage", UsageType)
    return node.value if node is not None else None


def getBankVolatility(bankOrLocalBankID: str) -> bool | None:
    """Return explicit bank volatility; absence is unspecified (F.7.57.43)."""
    node = _bank_scalar(_require_bank(bankOrLocalBankID, local=True), "volatile", Volatile)
    if node is None:
        return None
    if type(node.value) is not bool:
        raise TgiError("Invalid bank volatile value", TgiFaultCode.INVALID_ID)
    return node.value


def _bank_edit_metadata(bank: _Bank, attribute: str, model_type: type) -> tuple[Any | None, str, str]:
    """Validate and return an instance-local metadata node and its storage path."""
    values, path, _types, ref_type = _bank_storage(bank)
    if isinstance(bank, _LOCAL_BANK_TYPES):
        value = getattr(bank, attribute, None)
        expected = UsageType if model_type is UsageType else Volatile
        if value is not None and not isinstance(value, expected):
            raise TgiError(f"Invalid bank {attribute}", TgiFaultCode.INVALID_ID)
        return value, attribute, "single"

    # Validate reference Names without resolving the target definition. Metadata
    # belongs to the addressed instance and is absent on a reference branch.
    reference = next((item for item in values if ref_type is not None and isinstance(item, ref_type)), None)
    if reference is not None:
        _type_definition_reference_names(reference.value, reference.type_definitions)
        return None, path, "list"

    # Generated choice storage can be supplied directly by callers. Reject a
    # malformed ordering before editing so the operation remains atomic.
    ranks = (UsageType, Volatile, AccessPolicies, Parameters)
    rank_by_type = {kind: rank + 1 for rank, kind in enumerate(ranks)}
    last_rank = 0
    for item in values:
        rank = next((rank_by_type[kind] for kind in ranks if isinstance(item, kind)), 0)
        if rank < last_rank:
            raise TgiError("Invalid bank metadata order", TgiFaultCode.INVALID_ID)
        last_rank = rank
    current = next((item for item in values if isinstance(item, model_type)), None)
    return current, path, "list"


def _set_bank_metadata(bankID: str, attribute: str, value: str | bool, model_type: type) -> bool:
    bank = _require_bank(bankID, local=True)
    current, path, container = _bank_edit_metadata(bank, attribute, model_type)
    values: list | tuple = []
    content_types: tuple[type, ...] = ()
    if container == "list":
        values, _path, content_types, ref_type = _bank_storage(bank)
        if ref_type is not None and any(isinstance(item, ref_type) for item in values):
            raise TgiError("Cannot set instance metadata on a referenced bank", TgiFaultCode.INVALID_ARGUMENT)

    replacement = UsageType(value) if model_type is UsageType else value
    if model_type is Volatile:
        if current is not None:
            if type(current.value) is not bool:
                raise TgiError("Invalid bank volatile value", TgiFaultCode.INVALID_ID)
            _register_graph(current)
            register_parent(current, bank, (path,), container)
            current.value = replacement
            return True
        replacement = Volatile(value=replacement)
    elif current == replacement:
        return True

    if container == "single":
        setattr(bank, attribute, replacement)
        if model_type is Volatile:
            register_parent(replacement, bank, (attribute,), "single")
        return True

    values = _list_attr(bank, path)
    if current is not None:
        position = next(index for index, item in enumerate(values) if isinstance(item, model_type))
        values[position] = replacement
    else:
        ranks = (UsageType, Volatile, AccessPolicies, Parameters)
        rank = ranks.index(model_type)
        position = len(values)
        for index, item in enumerate(values):
            item_rank = (
                -1
                if isinstance(item, content_types)
                else next((i for i, kind in enumerate(ranks) if isinstance(item, kind)), len(ranks))
            )
            if item_rank > rank:
                position = index
                break
        values.insert(position, replacement)
    if model_type is Volatile:
        register_parent(replacement, bank, (path,), "list")
    return True


def removeBankUsage(bankID: str) -> bool:
    """Remove explicit usage from a bank instance without editing its target (F.7.58.36)."""
    bank = _require_bank(bankID)
    current, path, container = _bank_edit_metadata(bank, "usage", UsageType)
    if container == "list" and _bank_reference_present(bank):
        return False
    if current is None:
        return False
    if container == "single":
        bank.usage = None
    else:
        values = _list_attr(bank, path)
        del values[next(index for index, item in enumerate(values) if isinstance(item, UsageType))]
    return True


def removeBankVolatility(bankID: str) -> bool:
    """Remove explicit volatility and invalidate its wrapper handle (F.7.58.37)."""
    bank = _require_bank(bankID)
    current, path, container = _bank_edit_metadata(bank, "volatile", Volatile)
    if container == "list" and _bank_reference_present(bank):
        return False
    if current is None:
        return False
    if type(current.value) is not bool:
        raise TgiError("Invalid bank volatile value", TgiFaultCode.INVALID_ID)
    if container == "list":
        _list_attr(bank, path)
    _register_graph(current)
    if container == "single":
        register_parent(current, bank, (path,), "single")
    else:
        register_parent(current, bank, (path,), "list")
    if not detach_child_by_handle(get_handle(current)):
        raise TgiError("Could not remove bank volatility", TgiFaultCode.INVALID_ID)
    return True


def _bank_reference_present(bank: _Bank) -> bool:
    values, _path, _types, ref_type = _bank_storage(bank)
    return ref_type is not None and any(isinstance(item, ref_type) for item in values)


def setBankUsage(bankID: str, usage: str) -> bool:
    """Set the exact schema bank usage on an inline bank or localBank (F.7.58.64)."""
    if not isinstance(usage, str):
        raise TgiError("usage must be a schema usage string", TgiFaultCode.INVALID_ARGUMENT)
    try:
        value = UsageType(usage)
    except ValueError as error:
        raise TgiError("Invalid bank usage", TgiFaultCode.INVALID_ARGUMENT) from error
    return _set_bank_metadata(bankID, "usage", value.value, UsageType)


def setBankVolatility(bankOrLocalBankID: str, _volatile: bool) -> bool:
    """Set explicit volatility on an inline bank or localBank (F.7.58.65)."""
    if type(_volatile) is not bool:
        raise TgiError("_volatile must be a boolean", TgiFaultCode.INVALID_ARGUMENT)
    return _set_bank_metadata(bankOrLocalBankID, "volatile", _volatile, Volatile)


def setBankBaseAddress(bankID: str, baseAddress: str) -> bool:
    """Set a nonlocal addressed bank's unsigned 64-bit baseAddress (F.7.58.63)."""
    node = _bank_base(bankID, local=False)
    node.value = _expression(baseAddress, "baseAddress", 0, (1 << 64) - 1, node)
    return True


def setBankBankDefinitionRef(bankID: str, value: str, typeDefinitions: str) -> bool:
    """Replace inline bank content with literal Name values or update its reference (F.7.58.62)."""
    bank, reference = _bank_definition_reference(bankID)
    name, external = _type_definition_reference_names_for_input(value, typeDefinitions)
    values, path, _types, ref_type = _bank_storage(bank)
    if ref_type is None:
        raise TgiError("Bank model has no definition reference", TgiFaultCode.INVALID_ARGUMENT)
    if reference is not None:
        reference.value, reference.type_definitions = name, external
        return True

    values = _list_attr(bank, path)
    children = [item for item in values if not isinstance(item, UsageType)]
    for child in children:
        register_parent(child, bank, (path,), "list")
        _register_graph(child)
    for child in children:
        if not detach_child_by_handle(get_handle(child)):
            raise TgiError("Could not replace bank inline definition", TgiFaultCode.INVALID_ID)
    replacement = ref_type(value=name, type_definitions=external)
    bank.choice = [replacement]
    register_parent(replacement, bank, (path,), "list")
    return True


def _type_definition_reference_names_for_input(value: str, typeDefinitions: str) -> tuple[str, str]:
    """Validate TGI Name arguments, reporting invalid caller input as INVALID_ARGUMENT."""
    try:
        return _name(value, "Name"), _name(typeDefinitions, "Name")
    except TgiError as error:
        raise TgiError("Invalid bank definition reference Name", TgiFaultCode.INVALID_ARGUMENT) from error


def getBankBankDefinitionRefByExternalTypeDefID(bankID: str) -> str | None:
    """Return the named owning-document external declaration handle (F.7.57.32)."""
    owner, reference = _bank_definition_reference(bankID)
    if reference is None:
        return None
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return get_handle(_type_definition_external(owner, external))


def getBankBankDefinitionRefByID(bankID: str) -> str | None:
    """Resolve the actual definition in its declared registered library (F.7.57.33)."""
    owner, reference = _bank_definition_reference(bankID)
    if reference is None:
        return None
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return _type_definition_target(owner, name, external, getTypeDefinitionsBankDefinitionIDs)


def getBankBankDefinitionRefByName(bankID: str) -> str | None:
    """Return the stored normalized definition Name without target resolution (F.7.57.34)."""
    owner, reference = _bank_definition_reference(bankID)
    if reference is None:
        return None
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return name


def getBankBankDefinitionRefID(bankID: str) -> str | None:
    """Return the owned source reference wrapper without target resolution (F.7.57.35)."""
    owner, reference = _bank_definition_reference(bankID)
    if reference is None:
        return None
    return get_handle(reference)


def getMemoryRemapRemapDefinitionRefByExternalTypeDefID(memoryRemapID: str) -> str | None:
    """Return the named owning-document external declaration handle (F.7.57.65)."""
    owner, reference = _remap_definition_reference(memoryRemapID)
    if reference is None:
        return None
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return get_handle(_type_definition_external(owner, external))


def getMemoryRemapRemapDefinitionRefByID(memoryRemapID: str) -> str | None:
    """Resolve the actual definition in its declared registered library (F.7.57.66)."""
    owner, reference = _remap_definition_reference(memoryRemapID)
    if reference is None:
        return None
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return _type_definition_target(owner, name, external, getTypeDefinitionsMemoryRemapDefinitionIDs)


def getMemoryRemapRemapDefinitionRefByName(memoryRemapID: str) -> str | None:
    """Return the stored normalized definition Name without target resolution (F.7.57.67)."""
    owner, reference = _remap_definition_reference(memoryRemapID)
    if reference is None:
        return None
    name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    return name


def getMemoryRemapRemapDefinitionRefID(memoryRemapID: str) -> str | None:
    """Return the owned source reference wrapper without target resolution (F.7.57.68)."""
    owner, reference = _remap_definition_reference(memoryRemapID)
    if reference is None:
        return None
    return get_handle(reference)


def _memory_alias_reference_id(aliasOfID: str, xml_name: str) -> str | None:
    """Return a typed owned memory-path wrapper and validate its source Name."""
    alias = _register_alias(aliasOfID)
    if xml_name == "addressBlockRef":
        reference = _child(alias, "address_block_ref", AddressBlockRef)
    else:
        _address, memory_map, remap = _reference_choice(
            alias, FieldType.AliasOf.AddressSpaceRef, FieldType.AliasOf.MemoryMapRef
        )
        reference = memory_map if xml_name == "memoryMapRef" else remap
    if reference is None:
        return None
    handle = get_handle(reference)
    _reference_name(handle, xml_name)
    return handle


def getAliasOfAddressBlockRefByName(aliasOfID: str) -> str | None:
    """Return the stored normalized addressBlock reference Name (F.7.57.22)."""
    return _reference_name(_memory_alias_reference_id(aliasOfID, "addressBlockRef"), "addressBlockRef")


def getAliasOfAddressBlockRefID(aliasOfID: str) -> str | None:
    """Return the owned addressBlockRef wrapper, independent of target lookup (F.7.57.23)."""
    return _memory_alias_reference_id(aliasOfID, "addressBlockRef")


def getAliasOfBankRefByNames(aliasOfID: str) -> list[str]:
    """Return the ordered normalized bank reference Names (F.7.57.24)."""
    return [_reference_name(handle, "bankRef") for handle in getAliasOfBankRefIDs(aliasOfID)]


def getAliasOfBankRefIDs(aliasOfID: str) -> list[str]:
    """Return ordered owned bankRef wrappers, preserving source tuples (F.7.57.25)."""
    alias = _register_alias(aliasOfID)
    values = _reference_list(alias, "bank_ref", BankRef)
    for reference in values:
        _reference_name(get_handle(reference), "bankRef")
    return _child_ids(alias, values, ("bank_ref",))


def getAliasOfMemoryMapRefByName(aliasOfID: str) -> str | None:
    """Return the stored normalized memoryMap reference Name (F.7.57.26)."""
    return _reference_name(_memory_alias_reference_id(aliasOfID, "memoryMapRef"), "memoryMapRef")


def getAliasOfMemoryMapRefID(aliasOfID: str) -> str | None:
    """Return the owned memoryMapRef source wrapper (F.7.57.27)."""
    return _memory_alias_reference_id(aliasOfID, "memoryMapRef")


def getAliasOfMemoryRemapRefByID(aliasOfID: str) -> str | None:
    """Resolve the actual memoryRemap selected by the alias memory-map path (F.7.57.28)."""
    reference_id = getAliasOfMemoryRemapRefID(aliasOfID)
    if reference_id is None:
        return None
    _reference_name(getAliasOfMemoryMapRefID(aliasOfID), "memoryMapRef")
    getAliasOfBankRefIDs(aliasOfID)
    return resolve_attribute_reference(reference_id, "memoryRemapRef")


def getAliasOfMemoryRemapRefByName(aliasOfID: str) -> str | None:
    """Return the stored normalized memoryRemap reference Name (F.7.57.29)."""
    return _reference_name(getAliasOfMemoryRemapRefID(aliasOfID), "memoryRemapRef")


def getAliasOfMemoryRemapRefID(aliasOfID: str) -> str | None:
    """Return the owned memoryRemapRef source wrapper (F.7.57.30)."""
    return _memory_alias_reference_id(aliasOfID, "memoryRemapRef")


def _address_block_edit_scalar[T: str | UsageType | Volatile](
    block: AddressBlockType | BankedBlockType, attribute: str, model_type: type[T]
) -> T | None:
    """Read instance-local metadata without resolving or editing an external definition."""
    _owner, reference = _address_block_definition_reference(get_handle(block))
    if reference is not None:
        return None
    if model_type is str:
        value = (
            next((item for item in block.choice if isinstance(item, str)), None)
            if isinstance(block, AddressBlockType)
            else None
        )
        if value is not None:
            _stored_name(value)
        return value
    node = _block_scalar(block, attribute, model_type)
    if model_type is Volatile and node is not None and type(node.value) is not bool:
        raise TgiError("Invalid addressBlock volatile value", TgiFaultCode.INVALID_ID)
    return node


def _remove_address_block_scalar(addressBlockID: str, attribute: str, model_type: type) -> bool:
    block = _require_address_block(addressBlockID)
    node = _address_block_edit_scalar(block, attribute, model_type)
    if node is None:
        return False
    if model_type in (str, UsageType):
        if isinstance(block, BankedBlockType):
            setattr(block, attribute, None)
        else:
            values = _list_attr(block, "choice")
            position = next(index for index, item in enumerate(values) if isinstance(item, model_type))
            del values[position]
        return True
    if isinstance(block, AddressBlockType):
        _list_attr(block, "choice")
    _register_graph(node)
    if not detach_child_by_handle(get_handle(node)):
        raise TgiError("Could not remove addressBlock metadata", TgiFaultCode.INVALID_ID)
    return True


def removeAddressBlockArray(addressBlockID: str) -> bool:
    """Remove the instance array and invalidate its descendants (F.7.58.21)."""
    block = _require_address_block(addressBlockID)
    if isinstance(block, BankedBlockType):
        return False
    array = _child(block, "array", Array)
    if array is None:
        return False
    _register_graph(array)
    if not detach_child_by_handle(get_handle(array)):
        raise TgiError("Could not remove addressBlock array", TgiFaultCode.INVALID_ID)
    return True


def removeAddressBlockRefIndex(indexID: str) -> bool:
    """Remove an owned addressBlockRef index, pruning its empty holder (F.7.58.22)."""
    return _remove_register_reference_index(indexID, AddressBlockRef)


def removeAddressBlockTypeIdentifier(addressBlockID: str) -> bool:
    """Remove the instance-local typeIdentifier, if present (F.7.58.25)."""
    return _remove_address_block_scalar(addressBlockID, "type_identifier", str)


def removeAddressBlockUsage(addressBlockID: str) -> bool:
    """Remove explicit instance usage, restoring the standard presumption (F.7.58.26)."""
    return _remove_address_block_scalar(addressBlockID, "usage", UsageType)


def removeAddressBlockVolatility(addressBlockID: str) -> bool:
    """Remove explicit instance volatility and invalidate its wrapper (F.7.58.27)."""
    return _remove_address_block_scalar(addressBlockID, "volatile", Volatile)


def _set_address_block_scalar(
    addressBlockID: str, attribute: str, value: str | UsageType | bool, model_type: type
) -> bool:
    block = _require_address_block(addressBlockID)
    current = _address_block_edit_scalar(block, attribute, model_type)
    if isinstance(block, AddressBlockType) and any(
        isinstance(item, AddressBlockType.AddressBlockDefinitionRef) for item in block.choice
    ):
        raise TgiError("Cannot set inline metadata on a referenced addressBlock", TgiFaultCode.INVALID_ARGUMENT)
    if model_type is str and isinstance(block, BankedBlockType):
        raise TgiError("Banked addressBlock has no typeIdentifier", TgiFaultCode.INVALID_ARGUMENT)
    if current is not None and model_type is Volatile:
        current.value = value
        _register_graph(current)
        return True
    replacement = Volatile(value=value) if model_type is Volatile else value
    if isinstance(block, BankedBlockType):
        setattr(block, attribute, replacement)
        if model_type is Volatile:
            register_parent(replacement, block, (attribute,), "single")
        return True
    if current == replacement:
        return True
    ranks = (
        str,
        UnsignedPositiveLongintExpression,
        UnsignedPositiveIntExpression,
        UsageType,
        Volatile,
        AccessPolicies,
        Parameters,
    )
    rank = ranks.index(model_type)
    values = _list_attr(block, "choice")
    if current is not None:
        position = next(index for index, item in enumerate(values) if isinstance(item, model_type))
        values[position] = replacement
    else:
        position = len(values)
        for index, item in enumerate(values):
            item_rank = next((i for i, model in enumerate(ranks) if isinstance(item, model)), len(ranks))
            if item_rank > rank:
                position = index
                break
        values.insert(position, replacement)
    if model_type is Volatile:
        register_parent(replacement, block, ("choice",), "list")
    return True


def setAddressBlockTypeIdentifier(addressBlockID: str, typeIdentifier: str) -> bool:
    """Set the instance-local typeIdentifier XML Name (F.7.58.54)."""
    value = _name(typeIdentifier, "Name")
    return _set_address_block_scalar(addressBlockID, "type_identifier", value, str)


def setAddressBlockUsage(addressBlockID: str, usage: str) -> bool:
    """Set schema-defined instance usage without re-owning enum primitives (F.7.58.55)."""
    if not isinstance(usage, str):
        raise TgiError("Invalid addressBlock usage", TgiFaultCode.INVALID_ARGUMENT)
    try:
        value = UsageType(usage)
    except ValueError as error:
        raise TgiError("Invalid addressBlock usage", TgiFaultCode.INVALID_ARGUMENT) from error
    return _set_address_block_scalar(addressBlockID, "usage", value, UsageType)


def setAddressBlockVolatility(addressBlockID: str, _volatile: bool) -> bool:
    """Set explicit instance volatility, preserving an existing wrapper (F.7.58.56)."""
    if type(_volatile) is not bool:
        raise TgiError("_volatile must be a boolean", TgiFaultCode.INVALID_ARGUMENT)
    return _set_address_block_scalar(addressBlockID, "volatile", _volatile, Volatile)


def addAddressBlockRefIndex(addressBlockRefID: str, value: str) -> str:
    """Append an owned unsigned 32-bit expression index (F.7.58.2)."""
    reference = _register_reference(addressBlockRefID, AddressBlockRef)
    return _add_register_reference_index(reference, value)


def setAddressBlockAddressBlockDefinitionRef(addressBlockID: str, value: str, typeDefinitions: str) -> bool:
    """Replace inline block content with a reference or update its owned wrapper (F.7.58.49)."""
    block, reference = _address_block_definition_reference(addressBlockID)
    if isinstance(block, BankedBlockType):
        raise TgiError("Banked addressBlock has no definition reference", TgiFaultCode.INVALID_ARGUMENT)
    name, external = _type_definition_reference_names(value, typeDefinitions)
    if reference is not None:
        reference.value, reference.type_definitions = name, external
        return True
    values = _list_attr(block, "choice")
    for child in tuple(values):
        if isinstance(child, (str, UsageType)):
            continue
        register_parent(child, block, ("choice",), "list")
        _register_graph(child)
        if not detach_child_by_handle(get_handle(child)):
            raise TgiError("Could not replace addressBlock inline definition", TgiFaultCode.INVALID_ID)
    reference = AddressBlockType.AddressBlockDefinitionRef(value=name, type_definitions=external)
    block.choice = [reference]
    register_parent(reference, block, ("choice",), "list")
    return True


def setAddressBlockArray(addressBlockID: str, dim: str) -> bool:
    """Create an instance array or update its first dimension, preserving other data (F.7.58.50)."""
    block = _require_address_block(addressBlockID, banked=False)
    array = _child(block, "array", Array)
    values = array.dim if array is not None else []
    if not isinstance(values, (list, tuple)) or any(not isinstance(item, Dim) for item in values):
        raise TgiError("Invalid addressBlock array dimensions", TgiFaultCode.INVALID_ID)
    current = values[0] if values else None
    source = _expression(dim, "dim", 1, (1 << 64) - 1, current)
    if array is None:
        array = Array(dim=[Dim(value=source)])
        block.array = array
        register_parent(array, block, ("array",), "single")
    elif current is None:
        array.dim = [Dim(value=source)]
    else:
        current.value = source
    _child_ids(array, array.dim, ("dim",))
    return True


def setAddressBlockBaseAddress(addressBlockID: str, baseAddress: str) -> bool:
    """Set local unsigned 64-bit baseAddress while preserving its wrapper (F.7.58.51)."""
    node = _address_block_base(addressBlockID)
    node.value = _expression(baseAddress, "baseAddress", 0, (1 << 64) - 1, node)
    return True


def _set_address_block_size(addressBlockID: str, source: str, attribute: str, model_type: type, maximum: int) -> bool:
    block = _require_address_block(addressBlockID)
    _owner, reference = _address_block_definition_reference(addressBlockID)
    if reference is not None:
        raise TgiError("Cannot set inline size on a referenced addressBlock", TgiFaultCode.INVALID_ARGUMENT)
    node = _block_scalar(block, attribute, model_type)
    if node is None:
        raise TgiError("Missing required addressBlock size", TgiFaultCode.INVALID_ID)
    node.value = _expression(source, attribute, 1, maximum, node)
    return True


def setAddressBlockRange(addressBlockID: str, range: str) -> bool:
    """Set instance range within the positive unsigned 64-bit domain (F.7.58.53)."""
    return _set_address_block_size(addressBlockID, range, "range", UnsignedPositiveLongintExpression, (1 << 64) - 1)


def setAddressBlockWidth(addressBlockID: str, width: str) -> bool:
    """Set instance width within the positive unsigned 32-bit domain (F.7.58.57)."""
    return _set_address_block_size(addressBlockID, width, "width", UnsignedPositiveIntExpression, (1 << 32) - 1)


def setAddressBlockDefinitionRef(addressBlockDefinitionRefID: str, value: str) -> bool:
    """Assign a definition handle's Name within the reference's declared library (F.7.58.52)."""
    reference = _register_reference(addressBlockDefinitionRefID, AddressBlockType.AddressBlockDefinitionRef)
    target = resolve_handle(value) if isinstance(value, str) else None
    if not isinstance(target, AddressBlockDefinitions.AddressBlockDefinition):
        raise TgiError("Invalid addressBlockDefinition value handle", TgiFaultCode.INVALID_ID)
    block = _register_owned_child(reference, AddressBlockType)
    if block is None:
        raise TgiError("Reference has no owning addressBlock", TgiFaultCode.INVALID_ID)
    _block, owned_reference = _address_block_definition_reference(get_handle(block))
    if owned_reference is not reference:
        raise TgiError("Reference is not owned by its addressBlock", TgiFaultCode.INVALID_ID)
    _old_name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
    name = _stored_name(target.name)
    target_id = _type_definition_target(block, name, external, getTypeDefinitionsAddressBlockDefinitionIDs)
    if resolve_handle(target_id) is not target:
        raise TgiError("Definition is outside the reference's declared library", TgiFaultCode.INVALID_ARGUMENT)
    reference.value = name
    return True


# ---------------------------------------------------------------------------
# EXTENDED (F.7.58) – memory map AliasOf reference edits
# ---------------------------------------------------------------------------


def addAliasOfBankRef(aliasOfID: str, bankRef: str) -> str:
    """Append a named bankRef to an aliasOf element (F.7.58.5)."""
    alias = _register_alias(aliasOfID)
    return _append_reference_path(alias, bankRef, "bank_ref", BankRef)


def _remove_alias_choice_reference(alias: FieldType.AliasOf, child: Any, label: str) -> bool:
    """Detach a selected addressSpaceRef or memoryMapRef choice branch."""
    values = _list_attr(alias, "address_space_ref_or_memory_map_ref_or_memory_remap_ref")
    if not any(value is child for value in values):
        raise TgiError("Alias reference is not owned by its choice", TgiFaultCode.INVALID_ID)
    return _remove_owned(get_handle(child), type(child), FieldType.AliasOf, label)


def removeAliasOfAddressBlockRef(aliasOfID: str) -> bool:
    """Remove addressBlockRef and its owned index descendants (F.7.58.28)."""
    alias = _register_alias(aliasOfID)
    reference = _child(alias, "address_block_ref", AddressBlockRef)
    if reference is None:
        return False
    return _remove_owned(get_handle(reference), AddressBlockRef, FieldType.AliasOf, "addressBlockRef")


def removeAliasOfAddressSpaceRef(aliasOfID: str) -> bool:
    """Remove addressSpaceRef while leaving unrelated AliasOf references intact (F.7.58.29)."""
    alias = _register_alias(aliasOfID)
    address_space, _memory_map, _remap = _reference_choice(
        alias, FieldType.AliasOf.AddressSpaceRef, FieldType.AliasOf.MemoryMapRef
    )
    if address_space is None:
        return False
    return _remove_alias_choice_reference(alias, address_space, "addressSpaceRef")


def removeAliasOfBankRef(bankrefID: str) -> bool:
    """Remove a bankRef from its owning aliasOf element (F.7.58.30)."""
    reference = resolve_handle(bankrefID) if isinstance(bankrefID, str) else None
    if not isinstance(reference, BankRef):
        raise TgiError("Invalid bankRef handle", TgiFaultCode.INVALID_ID)
    alias = _register_owned_child(reference, FieldType.AliasOf)
    if alias is None:
        raise TgiError("bankRef has no owning aliasOf", TgiFaultCode.INVALID_ID)
    return _remove_reference_path(alias, bankrefID, "bank_ref", BankRef)


def removeAliasOfMemoryMapRef(aliasOfID: str) -> bool:
    """Remove memoryMapRef together with its dependent memoryRemapRef (F.7.58.31)."""
    alias = _register_alias(aliasOfID)
    _address_space, memory_map, remap = _reference_choice(
        alias, FieldType.AliasOf.AddressSpaceRef, FieldType.AliasOf.MemoryMapRef
    )
    if memory_map is None:
        return False
    if remap is not None:
        _remove_alias_choice_reference(alias, remap, "memoryRemapRef")
    return _remove_alias_choice_reference(alias, memory_map, "memoryMapRef")


def setAliasOfAddressBlockRef(aliasOfID: str, addressBlockRef: str) -> bool:
    """Set the normalized addressBlockRef while preserving its wrapper and indices (F.7.58.58)."""
    alias = _register_alias(aliasOfID)
    replacement = AddressBlockRef(address_block_ref=_name(addressBlockRef, "Name"))
    return _set_named_reference(alias, "address_block_ref", replacement)


def setAliasOfAddressSpaceRef(aliasOfID: str, addressSpaceRef: str) -> bool:
    """Set the addressSpaceRef choice branch and invalidate incompatible alternatives (F.7.58.59)."""
    alias = _register_alias(aliasOfID)
    replacement = FieldType.AliasOf.AddressSpaceRef(address_space_ref=_name(addressSpaceRef, "Name"))
    return _set_reference_choice(
        alias,
        replacement,
        "address_space_ref",
        FieldType.AliasOf.AddressSpaceRef,
        FieldType.AliasOf.MemoryMapRef,
    )


def setAliasOfMemoryMapRef(aliasOfID: str, memoryMapRef: str) -> bool:
    """Set memoryMapRef while preserving an existing remap on the map branch (F.7.58.60)."""
    alias = _register_alias(aliasOfID)
    replacement = FieldType.AliasOf.MemoryMapRef(memory_map_ref=_name(memoryMapRef, "Name"))
    return _set_reference_choice(
        alias,
        replacement,
        "memory_map_ref",
        FieldType.AliasOf.AddressSpaceRef,
        FieldType.AliasOf.MemoryMapRef,
    )


def setAliasOfMemoryRemapRef(aliasOfID: str, memoryRemapRef: str) -> bool:
    """Set memoryRemapRef on an existing map branch (F.7.58.61)."""
    alias = _register_alias(aliasOfID)
    replacement = MemoryRemapRef(memory_remap_ref=_name(memoryRemapRef, "Name"))
    return _set_reference_choice(
        alias,
        replacement,
        "memory_remap_ref",
        FieldType.AliasOf.AddressSpaceRef,
        FieldType.AliasOf.MemoryMapRef,
    )


def addMemoryRemapModeRef(memoryRemapID: str, modeRef: str, priority: int) -> str:
    """Append an owned modeRef after checking its remap and map key scopes (F.7.58.17)."""
    remap = _require_memory_remap(memoryRemapID)
    refs = _remap_mode_refs(remap)
    if type(priority) is not int or not 0 <= priority <= (1 << 63) - 1:
        raise TgiError("priority must be a non-negative signed 64-bit integer", TgiFaultCode.INVALID_ARGUMENT)
    try:
        name = _name(modeRef, "Name")
    except TgiError as error:
        raise TgiError("Invalid memoryRemap modeRef Name", TgiFaultCode.INVALID_ARGUMENT) from error

    priorities: set[int] = set()
    names: set[str] = set()
    for reference in refs:
        current_priority = reference.priority
        if type(current_priority) is not int or current_priority < 0 or current_priority in priorities:
            raise TgiError("Invalid memoryRemap modeRef priorities", TgiFaultCode.INVALID_ID)
        priorities.add(current_priority)
        current_name = _stored_name(reference.value)
        if current_name in names:
            raise TgiError("Duplicate memoryRemap modeRef Names", TgiFaultCode.INVALID_ID)
        names.add(current_name)
    if name in names:
        raise TgiError(f"modeRef {name!r} already exists in this memoryRemap", TgiFaultCode.INVALID_ARGUMENT)

    # The TGI helper applies the shared per-element modeRef and priority checks.
    _mode_ref_priority(refs, name, priority)
    if priority in priorities:
        raise TgiError(f"modeRef priority {priority} already exists in this memoryRemap", TgiFaultCode.INVALID_ARGUMENT)

    memory_map = _register_owned_child(remap, MemoryMapType)
    if memory_map is not None:
        map_names = set(names)
        for sibling in _memory_map_choice(memory_map):
            if sibling is remap or not isinstance(sibling, (MemoryRemap, MemoryRemapType)):
                continue
            sibling_refs = _remap_mode_refs(sibling)
            sibling_priorities: set[int] = set()
            for sibling_ref in sibling_refs:
                sibling_priority = sibling_ref.priority
                sibling_name = _stored_name(sibling_ref.value)
                if type(sibling_priority) is not int or sibling_priority < 0 or sibling_priority in sibling_priorities:
                    raise TgiError("Invalid sibling memoryRemap modeRef priorities", TgiFaultCode.INVALID_ID)
                if sibling_name == name:
                    raise TgiError(
                        f"modeRef {sibling_name!r} already exists in this memoryMap",
                        TgiFaultCode.INVALID_ARGUMENT,
                    )
                if sibling_name in map_names:
                    raise TgiError("Duplicate memoryRemap modeRef Names in this memoryMap", TgiFaultCode.INVALID_ID)
                sibling_priorities.add(sibling_priority)
                map_names.add(sibling_name)

    reference = ModeRef(value=name, priority=priority)
    _list_attr(remap, "mode_ref").append(reference)
    register_parent(reference, remap, ("mode_ref",), "list")
    _register_graph(reference)
    return get_handle(reference)


def removeMemoryRemapModeRef(modeRefID: str) -> bool:
    """Remove a modeRef only when its registered owner actually contains it (F.7.58.45)."""
    reference = resolve_handle(modeRefID) if isinstance(modeRefID, str) else None
    if not isinstance(reference, ModeRef):
        raise TgiError("Invalid memoryRemap modeRef handle", TgiFaultCode.INVALID_ID)
    remap = _register_owned_child(reference, MemoryRemapType)
    if remap is None:
        raise TgiError("modeRef has no owning memoryRemap", TgiFaultCode.INVALID_ID)
    refs = _remap_mode_refs(remap)
    if not any(item is reference for item in refs):
        raise TgiError("modeRef is not a member of its memoryRemap", TgiFaultCode.INVALID_ID)
    _list_attr(remap, "mode_ref")
    register_parent(reference, remap, ("mode_ref",), "list")
    return _remove_owned(modeRefID, ModeRef, MemoryRemapType, "memoryRemap modeRef")


def setMemoryRemapRemapDefinitionRef(memoryRemapID: str, value: str, typeDefinitions: str) -> bool:
    """Set the named remap definition branch or replace the inline remap contents (F.7.58.69)."""
    remap, reference = _remap_definition_reference(memoryRemapID)
    definition_name, type_definitions_name = _type_definition_reference_names_for_input(value, typeDefinitions)
    if reference is not None:
        reference.value = definition_name
        reference.type_definitions = type_definitions_name
        return True

    values = _list_attr(remap, "choice")
    children = list(values)
    for child in children:
        register_parent(child, remap, ("choice",), "list")
        _register_graph(child)
    for child in children:
        if not detach_child_by_handle(get_handle(child)):
            raise TgiError("Could not replace memoryRemap inline definition", TgiFaultCode.INVALID_ID)

    reference = MemoryRemapType.RemapDefinitionRef(
        value=definition_name,
        type_definitions=type_definitions_name,
    )
    remap.choice = [reference]
    register_parent(reference, remap, ("choice",), "list")
    return True


def _signed_subspace_expression(source: str, current: SignedLongintExpression) -> str:
    """Validate a signed baseAddress source and its current declared bounds without replacing its wrapper."""
    _xml_text(source)
    if not source.strip():
        raise TgiError("baseAddress must be a non-empty expression", TgiFaultCode.INVALID_ARGUMENT)
    minimum, maximum = current.minimum, current.maximum
    if any(bound is not None and type(bound) is not int for bound in (minimum, maximum)):
        raise TgiError("Invalid declared baseAddress bound", TgiFaultCode.INVALID_ID)
    if minimum is not None and maximum is not None and minimum > maximum:
        raise TgiError("Invalid declared baseAddress bounds", TgiFaultCode.INVALID_ID)
    lower = max(-(1 << 63), minimum) if minimum is not None else -(1 << 63)
    upper = min((1 << 63) - 1, maximum) if maximum is not None else (1 << 63) - 1
    if lower > upper:
        raise TgiError("baseAddress bounds do not intersect the signed 64-bit domain", TgiFaultCode.INVALID_ID)
    value = _integer(source, (1 << 63) - 1, True, minimum=-(1 << 63))
    if value is not None and ((minimum is not None and value < minimum) or (maximum is not None and value > maximum)):
        raise TgiError("baseAddress outside declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    return source


def setSubSpaceMapBaseAddress(subSpaceMapID: str, baseAddress: str) -> bool:
    """Set a required signed 64-bit subspace baseAddress in its existing wrapper (F.7.58.74)."""
    node = _subspace_base(subSpaceMapID)
    source = _signed_subspace_expression(baseAddress, node)
    node.value = source
    return True
