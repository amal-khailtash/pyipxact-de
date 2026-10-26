"""Indirect interface category TGI functions (IEEE 1685-2022).

Implements exactly the BASE (F.7.53) and EXTENDED (F.7.54) indirect
interface functions for manipulating and querying the ``indirectAddressRef``
and ``indirectDataRef`` structures of an :class:`IndirectInterface`.

Error handling: invalid handles raise :class:`TgiError` with
``TgiFaultCode.INVALID_ID``; semantic violations return
``TgiFaultCode.INVALID_ARGUMENT``.
"""
# ruff: noqa: I001

from org.accellera.ipxact.v1685_2022 import (
    IndirectInterface,
    AddressBlockRef,
    FieldRef,
    RegisterRef,
    AlternateRegisterRef,
    MemoryRemapRef,
)
from org.accellera.ipxact.v1685_2022.indirect_address_ref import IndirectAddressRef
from org.accellera.ipxact.v1685_2022.indirect_data_ref import IndirectDataRef
from org.accellera.ipxact.v1685_2022.bank_ref import BankRef
from org.accellera.ipxact.v1685_2022.register_file_ref import RegisterFileRef

from typing import overload

from .port_map import _child_id, _remove_child, _name
from ._reference_choices import _reference_choice, _REFERENCE_CHOICE, _set_reference_choice
from .component import _list_attr
from ._reference_paths import _append_reference_path, _remove_reference_path
from .address_space import _register_owned_child
from ._model import _reference_list, _owned_list_ids
from .component import _register_graph
from ._attribute_references import _reference_name, resolve_attribute_reference

from .core import (
    TgiError,
    TgiFaultCode,
    resolve_handle,
    get_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.53)
    "getIndirectAddressRefAddressBlockRefByName",
    "getIndirectAddressRefAddressBlockRefID",
    "getIndirectAddressRefAddressSpaceRefByName",
    "getIndirectAddressRefAddressSpaceRefID",
    "getIndirectAddressRefAlternateRegisterRefByName",
    "getIndirectAddressRefAlternateRegisterRefID",
    "getIndirectAddressRefBankRefByNames",
    "getIndirectAddressRefBankRefIDs",
    "getIndirectAddressRefFieldRefByName",
    "getIndirectAddressRefFieldRefID",
    "getIndirectAddressRefMemoryMapRefByName",
    "getIndirectAddressRefMemoryMapRefID",
    "getIndirectAddressRefMemoryRemapRefByID",
    "getIndirectAddressRefMemoryRemapRefByName",
    "getIndirectAddressRefMemoryRemapRefID",
    "getIndirectAddressRefRegisterFileRefByNames",
    "getIndirectAddressRefRegisterFileRefIDs",
    "getIndirectAddressRefRegisterRefByName",
    "getIndirectAddressRefRegisterRefID",
    "getIndirectDataRefAddressBlockRefByName",
    "getIndirectDataRefAddressBlockRefID",
    "getIndirectDataRefAddressSpaceRefByName",
    "getIndirectDataRefAddressSpaceRefID",
    "getIndirectDataRefAlternateRegisterRefByName",
    "getIndirectDataRefAlternateRegisterRefID",
    "getIndirectDataRefBankRefByNames",
    "getIndirectDataRefBankRefIDs",
    "getIndirectDataRefFieldRefByName",
    "getIndirectDataRefFieldRefID",
    "getIndirectDataRefMemoryMapRefByName",
    "getIndirectDataRefMemoryMapRefID",
    "getIndirectDataRefMemoryRemapRefByID",
    "getIndirectDataRefMemoryRemapRefByName",
    "getIndirectDataRefMemoryRemapRefID",
    "getIndirectDataRefRegisterFileRefByNames",
    "getIndirectDataRefRegisterFileRefIDs",
    "getIndirectDataRefRegisterRefByName",
    "getIndirectDataRefRegisterRefID",
    "setIndirectAddressRefAddressSpaceRef",
    "setIndirectAddressRefMemoryMapRef",
    "setIndirectAddressRefMemoryRemapRef",
    "setIndirectDataRefAddressSpaceRef",
    "setIndirectDataRefMemoryMapRef",
    "setIndirectDataRefMemoryRemapRef",
    # EXTENDED (F.7.54)
    "addIndirectAddressRefBankRef",
    "addIndirectAddressRefRegisterFileRef",
    "addIndirectDataRefBankRef",
    "addIndirectDataRefRegisterFileRef",
    "addIndirectInterfaceTransparentBridge",
    "removeAliasOfMemoryRemapRef",
    "removeBroadcastToAddressSpaceRef",
    "removeIndirectAddressRefAddressBlockRef",
    "removeIndirectAddressRefAddressSpaceRef",
    "removeIndirectAddressRefAlternateRegisterRef",
    "removeIndirectAddressRefBankRef",
    "removeIndirectAddressRefMemoryMapRef",
    "removeIndirectAddressRefMemoryRemapRef",
    "removeIndirectAddressRefRegisterFileRef",
    "removeIndirectAddressRefRegisterRef",
    "removeIndirectDataRefAddressBlockRef",
    "removeIndirectDataRefAddressSpaceRef",
    "removeIndirectDataRefAlternateRegisterRef",
    "removeIndirectDataRefBankRef",
    "removeIndirectDataRefMemoryMapRef",
    "removeIndirectDataRefMemoryRemapRef",
    "removeIndirectDataRefRegisterFileRef",
    "removeIndirectDataRefRegisterRef",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _resolve(iiID: str) -> IndirectInterface | None:
    obj = resolve_handle(iiID)
    return obj if isinstance(obj, IndirectInterface) else None


def _resolve_address_ref(addressRefID: str) -> IndirectAddressRef | None:
    obj = resolve_handle(addressRefID)
    return obj if isinstance(obj, IndirectAddressRef) else None


def _resolve_data_ref(dataRefID: str) -> IndirectDataRef | None:
    obj = resolve_handle(dataRefID)
    return obj if isinstance(obj, IndirectDataRef) else None


def _get_address_ref(iiID: str) -> IndirectAddressRef:
    ii = _resolve(iiID)
    if ii is None:
        raise TgiError("Invalid indirectInterface handle", TgiFaultCode.INVALID_ID)
    if ii.indirect_address_ref is None:
        raise TgiError("Missing indirectAddressRef", TgiFaultCode.INVALID_ARGUMENT)
    return ii.indirect_address_ref


def _get_data_ref(iiID: str) -> IndirectDataRef:
    ii = _resolve(iiID)
    if ii is None:
        raise TgiError("Invalid indirectInterface handle", TgiFaultCode.INVALID_ID)
    if ii.indirect_data_ref is None:
        raise TgiError("Missing indirectDataRef", TgiFaultCode.INVALID_ARGUMENT)
    return ii.indirect_data_ref


def _indirect_reference[T: IndirectAddressRef | IndirectDataRef](reference_id: str, model_type: type[T]) -> T:
    """Resolve the generated address or data reference owner before child traversal."""
    owner = resolve_handle(reference_id)
    if not isinstance(owner, model_type):
        raise TgiError("Invalid indirect reference handle", TgiFaultCode.INVALID_ID)
    return owner


@overload
def _indirect_reference_name(reference_id: str, xml_name: str) -> str: ...


@overload
def _indirect_reference_name(reference_id: None, xml_name: str) -> None: ...


def _indirect_reference_name(reference_id: str | None, xml_name: str) -> str | None:
    """Read a reference source with shared attribute mapping and XML Name validation."""
    return _reference_name(reference_id, xml_name)


def _indirect_reference_ids[T: BankRef | RegisterFileRef](
    owner: IndirectAddressRef | IndirectDataRef, attribute: str, model_type: type[T]
) -> list[str]:
    """Return an ordered typed reference path with immediate and descendant ownership."""
    children = _reference_list(owner, attribute, model_type)
    for child in children:
        _register_graph(child)
    return _owned_list_ids(owner, children, attribute)


def _remove_indirect_path[T: BankRef | RegisterFileRef](
    reference_id: str,
    owner_type: type[IndirectAddressRef] | type[IndirectDataRef],
    attribute: str,
    model_type: type[T],
) -> bool:
    """Discover and require the specific address/data path owner before removal."""
    child = resolve_handle(reference_id)
    if not isinstance(child, model_type):
        raise TgiError("Invalid indirect path reference handle", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(child, owner_type)
    if not isinstance(owner, owner_type):
        raise TgiError("Reference has no matching indirect path owner", TgiFaultCode.INVALID_ID)
    return _remove_reference_path(owner, reference_id, attribute, model_type)


def _safe_name(obj: object | None, attr: str) -> object | None:  # helper for attribute-holding refs
    if obj is None:
        return None
    return getattr(obj, attr, None)


# ---------------------------------------------------------------------------
# BASE (F.7.53) – IndirectAddressRef getters
# ---------------------------------------------------------------------------


def getIndirectAddressRefAddressBlockRefByName(indirectAddressRefID: str) -> str | None:
    """Return addressBlockRef attribute value.

    Section: F.7.53.1.
    """
    return _indirect_reference_name(getIndirectAddressRefAddressBlockRefID(indirectAddressRefID), "addressBlockRef")


def getIndirectAddressRefAddressBlockRefID(indirectAddressRefID: str) -> str | None:
    """Return handle of addressBlockRef element.

    Section: F.7.53.2.
    """
    return _child_id(
        _indirect_reference(indirectAddressRefID, IndirectAddressRef), "address_block_ref", AddressBlockRef
    )


def getIndirectAddressRefAddressSpaceRefByName(indirectAddressRefID: str) -> str | None:
    """Return addressSpaceRef attribute value.

    Section: F.7.53.3.
    """
    return _indirect_reference_name(getIndirectAddressRefAddressSpaceRefID(indirectAddressRefID), "addressSpaceRef")


def getIndirectAddressRefAddressSpaceRefID(indirectAddressRefID: str) -> str | None:
    """Return handle of addressSpaceRef element.

    Section: F.7.53.4.
    """
    owner = _indirect_reference(indirectAddressRefID, IndirectAddressRef)
    child = _reference_choice(owner, IndirectAddressRef.AddressSpaceRef, IndirectAddressRef.MemoryMapRef)[0]
    return get_handle(child) if child is not None else None


def getIndirectAddressRefAlternateRegisterRefByName(indirectAddressRefID: str) -> str | None:
    """Return alternateRegisterRef attribute value.

    Section: F.7.53.5.
    """
    return _indirect_reference_name(
        getIndirectAddressRefAlternateRegisterRefID(indirectAddressRefID), "alternateRegisterRef"
    )


def getIndirectAddressRefAlternateRegisterRefID(indirectAddressRefID: str) -> str | None:
    """Return handle of alternateRegisterRef element.

    Section: F.7.53.6.
    """
    return _child_id(
        _indirect_reference(indirectAddressRefID, IndirectAddressRef), "alternate_register_ref", AlternateRegisterRef
    )


def getIndirectAddressRefBankRefByNames(indirectAddressRefID: str) -> list[str]:
    """Return list of bankRef attribute values.

    Section: F.7.53.7.
    """
    return [
        _indirect_reference_name(handle, "bankRef") for handle in getIndirectAddressRefBankRefIDs(indirectAddressRefID)
    ]


def getIndirectAddressRefBankRefIDs(indirectAddressRefID: str) -> list[str]:
    """Return handles of bankRef elements.

    Section: F.7.53.8.
    """
    return _indirect_reference_ids(_indirect_reference(indirectAddressRefID, IndirectAddressRef), "bank_ref", BankRef)


def getIndirectAddressRefFieldRefByName(indirectAddressRefID: str) -> str | None:
    """Return fieldRef attribute value.

    Section: F.7.53.9.
    """
    return _indirect_reference_name(getIndirectAddressRefFieldRefID(indirectAddressRefID), "fieldRef")


def getIndirectAddressRefFieldRefID(indirectAddressRefID: str) -> str | None:
    """Return handle of fieldRef element.

    Section: F.7.53.10.
    """
    return _child_id(_indirect_reference(indirectAddressRefID, IndirectAddressRef), "field_ref", FieldRef)


def getIndirectAddressRefMemoryMapRefByName(indirectAddressRefID: str) -> str | None:
    """Return memoryMapRef attribute value.

    Section: F.7.53.11.
    """
    return _indirect_reference_name(getIndirectAddressRefMemoryMapRefID(indirectAddressRefID), "memoryMapRef")


def getIndirectAddressRefMemoryMapRefID(indirectAddressRefID: str) -> str | None:
    """Return handle of memoryMapRef element.

    Section: F.7.53.12.
    """
    owner = _indirect_reference(indirectAddressRefID, IndirectAddressRef)
    child = _reference_choice(owner, IndirectAddressRef.AddressSpaceRef, IndirectAddressRef.MemoryMapRef)[1]
    return get_handle(child) if child is not None else None


def getIndirectAddressRefMemoryRemapRefByID(indirectAddressRefID: str) -> str | None:
    """Return the handle of the referenced memoryRemap element.

    Section: F.7.53.13.
    """
    reference_id = getIndirectAddressRefMemoryRemapRefID(indirectAddressRefID)
    if reference_id is None:
        return None
    getIndirectAddressRefMemoryRemapRefByName(indirectAddressRefID)
    return resolve_attribute_reference(reference_id, "memoryRemapRef")


def getIndirectAddressRefMemoryRemapRefByName(indirectAddressRefID: str) -> str | None:
    """Return the memoryRemapRef attribute value.

    Section: F.7.53.14.
    """
    return _indirect_reference_name(getIndirectAddressRefMemoryRemapRefID(indirectAddressRefID), "memoryRemapRef")


def getIndirectAddressRefMemoryRemapRefID(indirectAddressRefID: str) -> str | None:
    """Return handle of memoryRemapRef element.

    Section: F.7.53.15.
    """
    owner = _indirect_reference(indirectAddressRefID, IndirectAddressRef)
    child = _reference_choice(owner, IndirectAddressRef.AddressSpaceRef, IndirectAddressRef.MemoryMapRef)[2]
    if child is None:
        return None
    _register_graph(child)
    return get_handle(child)


def getIndirectAddressRefRegisterFileRefByNames(indirectAddressRefID: str) -> list[str]:
    """Return registerFileRef attribute values.

    Section: F.7.53.16.
    """
    return [
        _indirect_reference_name(handle, "registerFileRef")
        for handle in getIndirectAddressRefRegisterFileRefIDs(indirectAddressRefID)
    ]


def getIndirectAddressRefRegisterFileRefIDs(indirectAddressRefID: str) -> list[str]:
    """Return handles of registerFileRef elements.

    Section: F.7.53.17.
    """
    return _indirect_reference_ids(
        _indirect_reference(indirectAddressRefID, IndirectAddressRef), "register_file_ref", RegisterFileRef
    )


def getIndirectAddressRefRegisterRefByName(indirectAddressRefID: str) -> str | None:
    """Return registerRef attribute value.

    Section: F.7.53.18.
    """
    return _indirect_reference_name(getIndirectAddressRefRegisterRefID(indirectAddressRefID), "registerRef")


def getIndirectAddressRefRegisterRefID(indirectAddressRefID: str) -> str | None:
    """Return handle of registerRef element.

    Section: F.7.53.19.
    """
    return _child_id(_indirect_reference(indirectAddressRefID, IndirectAddressRef), "register_ref", RegisterRef)


# IndirectDataRef getters (F.7.53.20+)


def getIndirectDataRefAddressBlockRefByName(indirectDataRefID: str) -> str | None:
    """Return addressBlockRef attribute value for data ref.

    Section: F.7.53.20.
    """
    return _indirect_reference_name(getIndirectDataRefAddressBlockRefID(indirectDataRefID), "addressBlockRef")


def getIndirectDataRefAddressBlockRefID(indirectDataRefID: str) -> str | None:
    """Return handle of addressBlockRef element (data).

    Section: F.7.53.21.
    """
    return _child_id(_indirect_reference(indirectDataRefID, IndirectDataRef), "address_block_ref", AddressBlockRef)


def getIndirectDataRefAddressSpaceRefByName(indirectDataRefID: str) -> str | None:
    """Return addressSpaceRef attribute value (data).

    Section: F.7.53.22.
    """
    return _indirect_reference_name(getIndirectDataRefAddressSpaceRefID(indirectDataRefID), "addressSpaceRef")


def getIndirectDataRefAddressSpaceRefID(indirectDataRefID: str) -> str | None:
    """Return handle of addressSpaceRef element (data).

    Section: F.7.53.23.
    """
    owner = _indirect_reference(indirectDataRefID, IndirectDataRef)
    child = _reference_choice(owner, IndirectDataRef.AddressSpaceRef, IndirectDataRef.MemoryMapRef)[0]
    return get_handle(child) if child is not None else None


def getIndirectDataRefAlternateRegisterRefByName(indirectDataRefID: str) -> str | None:
    """Return alternateRegisterRef attribute value (data).

    Section: F.7.53.24.
    """
    return _indirect_reference_name(getIndirectDataRefAlternateRegisterRefID(indirectDataRefID), "alternateRegisterRef")


def getIndirectDataRefAlternateRegisterRefID(indirectDataRefID: str) -> str | None:
    """Return handle of alternateRegisterRef element (data).

    Section: F.7.53.25.
    """
    return _child_id(
        _indirect_reference(indirectDataRefID, IndirectDataRef), "alternate_register_ref", AlternateRegisterRef
    )


def getIndirectDataRefBankRefByNames(indirectDataRefID: str) -> list[str]:
    """Return bankRef attribute values (data).

    Section: F.7.53.26.
    """
    return [_indirect_reference_name(handle, "bankRef") for handle in getIndirectDataRefBankRefIDs(indirectDataRefID)]


def getIndirectDataRefBankRefIDs(indirectDataRefID: str) -> list[str]:
    """Return handles of bankRef elements (data).

    Section: F.7.53.27.
    """
    return _indirect_reference_ids(_indirect_reference(indirectDataRefID, IndirectDataRef), "bank_ref", BankRef)


def getIndirectDataRefFieldRefByName(indirectDataRefID: str) -> str | None:
    """Return fieldRef attribute value (data).

    Section: F.7.53.28.
    """
    return _indirect_reference_name(getIndirectDataRefFieldRefID(indirectDataRefID), "fieldRef")


def getIndirectDataRefFieldRefID(indirectDataRefID: str) -> str | None:
    """Return handle of fieldRef element (data).

    Section: F.7.53.29.
    """
    return _child_id(_indirect_reference(indirectDataRefID, IndirectDataRef), "field_ref", FieldRef)


def getIndirectDataRefMemoryMapRefByName(indirectDataRefID: str) -> str | None:
    """Return memoryMapRef attribute value (data).

    Section: F.7.53.30.
    """
    return _indirect_reference_name(getIndirectDataRefMemoryMapRefID(indirectDataRefID), "memoryMapRef")


def getIndirectDataRefMemoryMapRefID(indirectDataRefID: str) -> str | None:
    """Return handle of memoryMapRef element (data).

    Section: F.7.53.31.
    """
    owner = _indirect_reference(indirectDataRefID, IndirectDataRef)
    child = _reference_choice(owner, IndirectDataRef.AddressSpaceRef, IndirectDataRef.MemoryMapRef)[1]
    return get_handle(child) if child is not None else None


def getIndirectDataRefMemoryRemapRefByID(indirectDataRefID: str) -> str | None:
    """Return the handle of the referenced memoryRemap element.

    Section: F.7.53.32.
    """
    reference_id = getIndirectDataRefMemoryRemapRefID(indirectDataRefID)
    if reference_id is None:
        return None
    getIndirectDataRefMemoryRemapRefByName(indirectDataRefID)
    return resolve_attribute_reference(reference_id, "memoryRemapRef")


def getIndirectDataRefMemoryRemapRefByName(indirectDataRefID: str) -> str | None:
    """Return the memoryRemapRef attribute value (data).

    Section: F.7.53.33.
    """
    return _indirect_reference_name(getIndirectDataRefMemoryRemapRefID(indirectDataRefID), "memoryRemapRef")


def getIndirectDataRefMemoryRemapRefID(indirectDataRefID: str) -> str | None:
    """Return handle of memoryRemapRef element (data).

    Section: F.7.53.34.
    """
    owner = _indirect_reference(indirectDataRefID, IndirectDataRef)
    child = _reference_choice(owner, IndirectDataRef.AddressSpaceRef, IndirectDataRef.MemoryMapRef)[2]
    if child is None:
        return None
    _register_graph(child)
    return get_handle(child)


def getIndirectDataRefRegisterFileRefByNames(indirectDataRefID: str) -> list[str]:
    """Return registerFileRef attribute values (data).

    Section: F.7.53.35.
    """
    return [
        _indirect_reference_name(handle, "registerFileRef")
        for handle in getIndirectDataRefRegisterFileRefIDs(indirectDataRefID)
    ]


def getIndirectDataRefRegisterFileRefIDs(indirectDataRefID: str) -> list[str]:
    """Return handles of registerFileRef elements (data).

    Section: F.7.53.36.
    """
    return _indirect_reference_ids(
        _indirect_reference(indirectDataRefID, IndirectDataRef), "register_file_ref", RegisterFileRef
    )


def getIndirectDataRefRegisterRefByName(indirectDataRefID: str) -> str | None:
    """Return registerRef attribute value (data).

    Section: F.7.53.37.
    """
    return _indirect_reference_name(getIndirectDataRefRegisterRefID(indirectDataRefID), "registerRef")


def getIndirectDataRefRegisterRefID(indirectDataRefID: str) -> str | None:
    """Return handle of registerRef element (data).

    Section: F.7.53.38.
    """
    return _child_id(_indirect_reference(indirectDataRefID, IndirectDataRef), "register_ref", RegisterRef)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.54)
# ---------------------------------------------------------------------------


def addIndirectAddressRefBankRef(indirectAddressRefID: str, bankRef: str) -> str:
    """Append a bankRef to indirectAddressRef.

    Section: F.7.54.1.
    """
    owner = _indirect_reference(indirectAddressRefID, IndirectAddressRef)
    child_id = _append_reference_path(owner, bankRef, "bank_ref", BankRef)
    getIndirectAddressRefBankRefIDs(indirectAddressRefID)
    return child_id


def addIndirectAddressRefRegisterFileRef(indirectAddressRefID: str, registerFileRef: str) -> str:
    """Append a registerFileRef to indirectAddressRef.

    Section: F.7.54.2.
    """
    owner = _indirect_reference(indirectAddressRefID, IndirectAddressRef)
    child_id = _append_reference_path(owner, registerFileRef, "register_file_ref", RegisterFileRef)
    getIndirectAddressRefRegisterFileRefIDs(indirectAddressRefID)
    return child_id


def addIndirectDataRefBankRef(indirectDataRefID: str, bankRef: str) -> str:
    """Append a bankRef to indirectDataRef.

    Section: F.7.54.3.
    """
    owner = _indirect_reference(indirectDataRefID, IndirectDataRef)
    child_id = _append_reference_path(owner, bankRef, "bank_ref", BankRef)
    getIndirectDataRefBankRefIDs(indirectDataRefID)
    return child_id


def addIndirectDataRefRegisterFileRef(indirectDataRefID: str, registerFileRef: str) -> str:
    """Append a registerFileRef to indirectDataRef.

    Section: F.7.54.4.
    """
    owner = _indirect_reference(indirectDataRefID, IndirectDataRef)
    child_id = _append_reference_path(owner, registerFileRef, "register_file_ref", RegisterFileRef)
    getIndirectDataRefRegisterFileRefIDs(indirectDataRefID)
    return child_id


def addIndirectInterfaceTransparentBridge(indirectInterfaceID: str, initiatorRef: str) -> str:
    """Add a transparentBridge element to indirectInterface.

    Section: F.7.54.5.
    """
    ii = _resolve(indirectInterfaceID)
    if ii is None:
        raise TgiError("Invalid indirectInterface handle", TgiFaultCode.INVALID_ID)
    from org.accellera.ipxact.v1685_2022.transparent_bridge import TransparentBridge

    tb = TransparentBridge(initiator_ref=initiatorRef)
    ii.transparent_bridge.append(tb)  # type: ignore[attr-defined]
    register_parent(tb, ii, ("transparent_bridge",), "list")
    return get_handle(tb)


# The following remove* functions act on handles of child elements


def removeAliasOfMemoryRemapRef(aliasOfMemoryRemapRefID: str) -> bool:
    """Remove aliasOfMemoryRemapRef (global element reference removal).

    Section: F.7.54.6.
    """
    return detach_child_by_handle(aliasOfMemoryRemapRefID)


def removeBroadcastToAddressSpaceRef(broadcastToAddressSpaceRefID: str) -> bool:
    """Remove broadcastToAddressSpaceRef.

    Section: F.7.54.7.
    """
    return detach_child_by_handle(broadcastToAddressSpaceRefID)


def removeIndirectAddressRefAddressBlockRef(indirectAddressRefID: str) -> bool:
    """Remove addressBlockRef from indirectAddressRef.

    Section: F.7.54.8.
    """
    if getIndirectAddressRefAddressBlockRefID(indirectAddressRefID) is None:
        return False
    return _remove_child(_indirect_reference(indirectAddressRefID, IndirectAddressRef), "address_block_ref")


def removeIndirectAddressRefAddressSpaceRef(indirectAddressRefID: str) -> bool:
    """Remove addressSpaceRef from indirectAddressRef.

    Section: F.7.54.9.
    """
    child_id = getIndirectAddressRefAddressSpaceRefID(indirectAddressRefID)
    if child_id is None:
        return False
    _list_attr(_indirect_reference(indirectAddressRefID, IndirectAddressRef), _REFERENCE_CHOICE)
    return detach_child_by_handle(child_id)


def removeIndirectAddressRefAlternateRegisterRef(indirectAddressRefID: str) -> bool:
    """Remove alternateRegisterRef from indirectAddressRef.

    Section: F.7.54.10.
    """
    if getIndirectAddressRefAlternateRegisterRefID(indirectAddressRefID) is None:
        return False
    return _remove_child(_indirect_reference(indirectAddressRefID, IndirectAddressRef), "alternate_register_ref")


def removeIndirectAddressRefBankRef(bankRefID: str) -> bool:
    """Remove a bankRef element (by handle).

    Section: F.7.54.11.
    """
    return _remove_indirect_path(bankRefID, IndirectAddressRef, "bank_ref", BankRef)


def removeIndirectAddressRefMemoryMapRef(indirectAddressRefID: str) -> bool:
    """Remove memoryMapRef from indirectAddressRef, including its companion memoryRemapRef.

    Section: F.7.54.12.
    """
    child_id = getIndirectAddressRefMemoryMapRefID(indirectAddressRefID)
    if child_id is None:
        return False
    removeIndirectAddressRefMemoryRemapRef(indirectAddressRefID)
    _list_attr(_indirect_reference(indirectAddressRefID, IndirectAddressRef), _REFERENCE_CHOICE)
    return detach_child_by_handle(child_id)


def removeIndirectAddressRefMemoryRemapRef(indirectAddressRefID: str) -> bool:
    """Remove memoryRemapRef from indirectAddressRef.

    Section: F.7.54.13.
    """
    child_id = getIndirectAddressRefMemoryRemapRefID(indirectAddressRefID)
    if child_id is None:
        return False
    _list_attr(_indirect_reference(indirectAddressRefID, IndirectAddressRef), _REFERENCE_CHOICE)
    return detach_child_by_handle(child_id)


def removeIndirectAddressRefRegisterFileRef(registerFileRefID: str) -> bool:
    """Remove a registerFileRef element (by handle) from indirectAddressRef.

    Section: F.7.54.14.
    """
    return _remove_indirect_path(registerFileRefID, IndirectAddressRef, "register_file_ref", RegisterFileRef)


def removeIndirectAddressRefRegisterRef(indirectAddressRefID: str) -> bool:
    """Remove registerRef from indirectAddressRef.

    Section: F.7.54.15.
    """
    if getIndirectAddressRefRegisterRefID(indirectAddressRefID) is None:
        return False
    return _remove_child(_indirect_reference(indirectAddressRefID, IndirectAddressRef), "register_ref")


def removeIndirectDataRefAddressBlockRef(indirectDataRefID: str) -> bool:
    """Remove addressBlockRef from indirectDataRef.

    Section: F.7.54.16.
    """
    if getIndirectDataRefAddressBlockRefID(indirectDataRefID) is None:
        return False
    return _remove_child(_indirect_reference(indirectDataRefID, IndirectDataRef), "address_block_ref")


def removeIndirectDataRefAddressSpaceRef(indirectDataRefID: str) -> bool:
    """Remove addressSpaceRef from indirectDataRef.

    Section: F.7.54.17.
    """
    child_id = getIndirectDataRefAddressSpaceRefID(indirectDataRefID)
    if child_id is None:
        return False
    _list_attr(_indirect_reference(indirectDataRefID, IndirectDataRef), _REFERENCE_CHOICE)
    return detach_child_by_handle(child_id)


def removeIndirectDataRefAlternateRegisterRef(indirectDataRefID: str) -> bool:
    """Remove alternateRegisterRef from indirectDataRef.

    Section: F.7.54.18.
    """
    if getIndirectDataRefAlternateRegisterRefID(indirectDataRefID) is None:
        return False
    return _remove_child(_indirect_reference(indirectDataRefID, IndirectDataRef), "alternate_register_ref")


def removeIndirectDataRefBankRef(bankRefID: str) -> bool:
    """Remove a bankRef (data) by handle.

    Section: F.7.54.19.
    """
    return _remove_indirect_path(bankRefID, IndirectDataRef, "bank_ref", BankRef)


def removeIndirectDataRefMemoryMapRef(indirectDataRefID: str) -> bool:
    """Remove memoryMapRef from indirectDataRef, including its companion memoryRemapRef.

    Section: F.7.54.20.
    """
    child_id = getIndirectDataRefMemoryMapRefID(indirectDataRefID)
    if child_id is None:
        return False
    removeIndirectDataRefMemoryRemapRef(indirectDataRefID)
    _list_attr(_indirect_reference(indirectDataRefID, IndirectDataRef), _REFERENCE_CHOICE)
    return detach_child_by_handle(child_id)


def removeIndirectDataRefMemoryRemapRef(indirectDataRefID: str) -> bool:
    """Remove memoryRemapRef from indirectDataRef.

    Section: F.7.54.21.
    """
    child_id = getIndirectDataRefMemoryRemapRefID(indirectDataRefID)
    if child_id is None:
        return False
    _list_attr(_indirect_reference(indirectDataRefID, IndirectDataRef), _REFERENCE_CHOICE)
    return detach_child_by_handle(child_id)


def removeIndirectDataRefRegisterFileRef(registerFileRefID: str) -> bool:
    """Remove registerFileRef element (data) by handle.

    Section: F.7.54.22.
    """
    return _remove_indirect_path(registerFileRefID, IndirectDataRef, "register_file_ref", RegisterFileRef)


def removeIndirectDataRefRegisterRef(indirectDataRefID: str) -> bool:
    """Remove registerRef from indirectDataRef.

    Section: F.7.54.23.
    """
    if getIndirectDataRefRegisterRefID(indirectDataRefID) is None:
        return False
    return _remove_child(_indirect_reference(indirectDataRefID, IndirectDataRef), "register_ref")


def setIndirectAddressRefAddressSpaceRef(indirectAddressRefID: str, addressSpaceRef: str) -> bool:
    """Set the normalized addressSpaceRef while preserving compatible reference wrappers.

    Section: F.7.54.27.
    """
    owner = _indirect_reference(indirectAddressRefID, IndirectAddressRef)
    replacement = IndirectAddressRef.AddressSpaceRef(address_space_ref=_name(addressSpaceRef, "Name"))
    return _set_reference_choice(
        owner, replacement, "address_space_ref", IndirectAddressRef.AddressSpaceRef, IndirectAddressRef.MemoryMapRef
    )


def setIndirectAddressRefMemoryMapRef(indirectAddressRefID: str, memoryMapRef: str) -> bool:
    """Set the normalized memoryMapRef while preserving compatible reference wrappers.

    Section: F.7.54.30.
    """
    owner = _indirect_reference(indirectAddressRefID, IndirectAddressRef)
    replacement = IndirectAddressRef.MemoryMapRef(memory_map_ref=_name(memoryMapRef, "Name"))
    return _set_reference_choice(
        owner, replacement, "memory_map_ref", IndirectAddressRef.AddressSpaceRef, IndirectAddressRef.MemoryMapRef
    )


def setIndirectAddressRefMemoryRemapRef(indirectAddressRefID: str, memoryRemapRef: str) -> bool:
    """Set the normalized memoryRemapRef while preserving compatible reference wrappers.

    Section: F.7.54.31.
    """
    owner = _indirect_reference(indirectAddressRefID, IndirectAddressRef)
    replacement = MemoryRemapRef(memory_remap_ref=_name(memoryRemapRef, "Name"))
    return _set_reference_choice(
        owner, replacement, "memory_remap_ref", IndirectAddressRef.AddressSpaceRef, IndirectAddressRef.MemoryMapRef
    )


def setIndirectDataRefAddressSpaceRef(indirectDataRefID: str, addressSpaceRef: str) -> bool:
    """Set the normalized addressSpaceRef while preserving compatible reference wrappers.

    Section: F.7.54.34.
    """
    owner = _indirect_reference(indirectDataRefID, IndirectDataRef)
    replacement = IndirectDataRef.AddressSpaceRef(address_space_ref=_name(addressSpaceRef, "Name"))
    return _set_reference_choice(
        owner, replacement, "address_space_ref", IndirectDataRef.AddressSpaceRef, IndirectDataRef.MemoryMapRef
    )


def setIndirectDataRefMemoryMapRef(indirectDataRefID: str, memoryMapRef: str) -> bool:
    """Set the normalized memoryMapRef while preserving compatible reference wrappers.

    Section: F.7.54.37.
    """
    owner = _indirect_reference(indirectDataRefID, IndirectDataRef)
    replacement = IndirectDataRef.MemoryMapRef(memory_map_ref=_name(memoryMapRef, "Name"))
    return _set_reference_choice(
        owner, replacement, "memory_map_ref", IndirectDataRef.AddressSpaceRef, IndirectDataRef.MemoryMapRef
    )


def setIndirectDataRefMemoryRemapRef(indirectDataRefID: str, memoryRemapRef: str) -> bool:
    """Set the normalized memoryRemapRef while preserving compatible reference wrappers.

    Section: F.7.54.38.
    """
    owner = _indirect_reference(indirectDataRefID, IndirectDataRef)
    replacement = MemoryRemapRef(memory_remap_ref=_name(memoryRemapRef, "Name"))
    return _set_reference_choice(
        owner, replacement, "memory_remap_ref", IndirectDataRef.AddressSpaceRef, IndirectDataRef.MemoryMapRef
    )
