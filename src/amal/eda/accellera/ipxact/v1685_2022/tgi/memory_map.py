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

from .address_space import _register_owned_child
from .bus_interface import _named_target
from ._expressions import _integer
from .port_map import _child, _name
from .register_file import _child_ids, _numeric
from .register import _type_definition_target, _type_definition_reference_names
from .type_definitions import getTypeDefinitionsAddressBlockDefinitionIDs

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.57.x) – ordering matches spec numbering groups
    # AddressBlock getters (1–21) - subset implemented (schema coverage pending)
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
    "removeMemoryMapMemoryRemap",
    "removeMemoryMapSubspaceMap",
    "setMemoryMapMemoryMapDefinitionRef",
    "setMemoryMapShared",
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
    if isinstance(element, (AddressBankType, BankedBankType, LocalAddressBankType)):
        return "bank"
    if isinstance(element, (SubspaceMap, BankedSubspaceType)):
        return "subSpaceMap"
    raise TgiError("Invalid memory-map element handle", TgiFaultCode.INVALID_ID)


def getMemoryMapMemoryMapDefinitionRefByExternalTypeDefID(
    memoryMapID: str,
) -> str | None:
    """Return the referenced memoryMapDefinition name.

    Section: F.7.57.51. Returns None if absent.
    """
    mm = _resolve_memory_map(memoryMapID)
    if mm is None or mm.memory_map_definition_ref is None:
        return None
    return getattr(mm.memory_map_definition_ref, "value", None)


def getMemoryMapMemoryMapDefinitionRefByID(memoryMapID: str) -> str | None:
    """Return memoryMapDefinition name via element handle.

    Section: F.7.57.52.
    """
    return getMemoryMapMemoryMapDefinitionRefByExternalTypeDefID(memoryMapID)


def getMemoryMapMemoryMapDefinitionRefByName(memoryMapID: str) -> str | None:
    """Return memoryMapDefinition name by its name lookup.

    Section: F.7.57.53.
    """
    return getMemoryMapMemoryMapDefinitionRefByExternalTypeDefID(memoryMapID)


def getMemoryMapMemoryMapDefinitionRefID(memoryMapID: str) -> str | None:
    """Return handle of ``memoryMapDefinitionRef`` element.

    Section: F.7.57.54.
    """
    mm = _resolve_memory_map(memoryMapID)
    if mm is None or mm.memory_map_definition_ref is None:
        return None
    return get_handle(mm.memory_map_definition_ref)


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


def _remap_elements(remap: MemoryRemapType) -> list[str]:
    """Read ordered inline remap children, rejecting conflicting definition branches."""
    values = remap.choice
    if not isinstance(values, (list, tuple)):
        raise TgiError("Invalid memoryRemap choice", TgiFaultCode.INVALID_ID)
    references = [item for item in values if isinstance(item, MemoryRemapType.RemapDefinitionRef)]
    if references:
        if len(values) != 1:
            raise TgiError("Conflicting remap definition and inline content", TgiFaultCode.INVALID_ID)
        return []
    if any(not isinstance(item, (AddressBlock, Bank, SubspaceMap)) for item in values):
        raise TgiError("Invalid memoryRemap choice child", TgiFaultCode.INVALID_ID)
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


def setMemoryMapMemoryMapDefinitionRef(memoryMapID: str, name: str | None) -> bool:
    """Set or clear ``memoryMapDefinitionRef`` (named reference).

    Section: F.7.58.67. Name corresponds to a memoryMapDefinition in typeDefinitions.
    Passing None removes the element.
    """
    mm = _require_memory_map(memoryMapID)
    if name is None:
        mm.memory_map_definition_ref = None  # type: ignore[assignment]
        return True
    mm.memory_map_definition_ref = MemoryMapType.MemoryMapDefinitionRef(value=name, type_definitions="typeDefinitions")  # type: ignore[assignment]
    return True


def setMemoryMapShared(memoryMapID: str, shared: str | None) -> bool:
    """Set or clear ``shared`` attribute value (string form).

    Section: F.7.58.68. Accepts None to remove the element.
    """
    mm = _require_memory_map(memoryMapID)
    if shared is None:
        mm.shared = None  # type: ignore[assignment]
        return True
    from org.accellera.ipxact.v1685_2022.shared_type import SharedType

    mm.shared = SharedType(value=shared)  # type: ignore[arg-type]
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


def _address_block_size_node[T: UnsignedPositiveLongintExpression | UnsignedPositiveIntExpression](
    block: AddressBlockType | BankedBlockType, attribute: str, model_type: type[T]
) -> T:
    if isinstance(block, BankedBlockType):
        node = _child(block, attribute, model_type)
    else:
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
        if refs:
            if len(values) != 1:
                raise TgiError("Conflicting addressBlock definition and inline content", TgiFaultCode.INVALID_ID)
            reference = refs[0]
            register_parent(reference, block, ("choice",), "list")
            name, external = _type_definition_reference_names(reference.value, reference.type_definitions)
            target_id = _type_definition_target(block, name, external, getTypeDefinitionsAddressBlockDefinitionIDs)
            definition = resolve_handle(target_id)
            if not isinstance(definition, AddressBlockDefinitions.AddressBlockDefinition):
                raise TgiError("Invalid addressBlockDefinition target", TgiFaultCode.INVALID_ID)
            node = _child(definition, attribute, model_type)
        else:
            for scalar in (UnsignedPositiveLongintExpression, UnsignedPositiveIntExpression):
                if sum(isinstance(item, scalar) for item in values) > 1:
                    raise TgiError("Duplicate addressBlock size child", TgiFaultCode.INVALID_ID)
            node = next((item for item in values if isinstance(item, model_type)), None)
            if node is not None:
                register_parent(node, block, ("choice",), "list")
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
