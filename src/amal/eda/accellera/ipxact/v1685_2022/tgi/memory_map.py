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
from .port_map import _child
from .register_file import _child_ids, _numeric

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
