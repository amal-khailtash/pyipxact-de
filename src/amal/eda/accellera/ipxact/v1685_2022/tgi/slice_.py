"""Slice category TGI functions (IEEE 1685-2022).

Named ``slice_`` to avoid clashing with Python's built-in ``slice``. Implements
BASE (F.7.77) and EXTENDED (F.7.78) Slice functions. Implemented HDL path and range
getters and mode port-reference getters reject invalid handles; field-reference
getters retain legacy neutral results (``None`` / empty list). EXTENDED mutators raise
``TgiError`` with ``TgiFaultCode.INVALID_ID`` for invalid handles and
``TgiFaultCode.INVALID_ARGUMENT`` for semantic issues.

HDL path and range access uses generated slice, path-segment, range, and
endpoint models. Mode port references use generated wrappers and part-selects.
Legacy field-reference mutations use minimal schema objects or lightweight
namespaces.
"""

# ruff: noqa: I001
from types import SimpleNamespace
from typing import Any
from collections.abc import Sequence

from org.accellera.ipxact.v1685_2022 import (
    SliceType,
    PortSliceType,
    Left,
    Right,
    SlicesType,
    PathSegmentType,
    PortPathSegmentType,
    ComponentType,
    SubPortReference,
)

from ._ranges import _range_endpoint, _range_value, _remove_range, _set_range
from .miscellaneous import getExpression
from ._expressions import _string_source
from ._model import _owned_list_ids
from .address_space import _register_owned_child, _remove_owned
from .component import _list_attr
from .port_map import _name, _set_part_select, _remove_child
from ._miscellaneous_part_select import _part_select

from .core import (
    TgiError,
    TgiFaultCode,
    resolve_handle,
    get_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.77)
    "getFieldSliceAddressBlockRefByID",
    "getFieldSliceAddressBlockRefByName",
    "getFieldSliceAddressBlockRefID",
    "getFieldSliceAddressSpaceRefByID",
    "getFieldSliceAddressSpaceRefByName",
    "getFieldSliceAddressSpaceRefID",
    "getFieldSliceAlternateRegisterRefByID",
    "getFieldSliceAlternateRegisterRefByName",
    "getFieldSliceAlternateRegisterRefID",
    "getFieldSliceBankRefByNames",
    "getFieldSliceBankRefIDs",
    "getFieldSliceFieldRefByName",
    "getFieldSliceFieldRefID",
    "getFieldSliceMemoryMapRefByID",
    "getFieldSliceMemoryMapRefByName",
    "getFieldSliceMemoryMapRefID",
    "getFieldSliceMemoryRemapRefByID",
    "getFieldSliceMemoryRemapRefByName",
    "getFieldSliceMemoryRemapRefID",
    "getFieldSliceRange",
    "getFieldSliceRangeLeftID",
    "getFieldSliceRangeRightID",
    "getLocationSliceIDs",
    "getPortSlicePartSelectID",
    "getPortSlicePortRefByName",
    "getPortSliceSubPortReferenceIDs",
    "getSlicePathSegmentIDs",
    "getSliceRange",
    "getSliceRangeExpression",
    "getSliceRangeLeftID",
    "getSliceRangeRightID",
    # EXTENDED (F.7.78)
    "addFieldSliceBankRef",
    "addFieldSliceRegisterFileRef",
    "addModeFieldSlice",
    "addModePortSlice",
    "addPortSliceSubPortReference",
    "addSlicePathSegment",
    "removeFieldSliceAlternateRegisterRef",
    "removeFieldSliceBankRef",
    "removeFieldSliceMemoryRemapRef",
    "removeFieldSliceRange",
    "removeFieldSliceRegisterFileRef",
    "removeLocationSlice",
    "removeModeFieldSlice",
    "removeModePortSlice",
    "removePortSlicePartSelect",
    "removePortSliceSubPortReference",
    "removeSlicePathSegment",
    "removeSliceRange",
    "setFieldSliceAddressBlockRef",
    "setFieldSliceAddressSpaceRef",
    "setFieldSliceAlternateRegisterRef",
    "setFieldSliceFieldRef",
    "setFieldSliceMemoryMapRef",
    "setFieldSliceMemoryRemapRef",
    "setFieldSliceRange",
    "setFieldSliceRegisterRef",
    "setPortSlicePartSelect",
    "setPortSlicePortRef",
    "setSliceRange",
]


_ModePortSlice = ComponentType.Modes.Mode.PortSlice


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _hdl_slice(slice_id: str) -> SliceType | PortSliceType:
    """Resolve a generated HDL slice without accepting mode reference slices."""
    owner = resolve_handle(slice_id)
    if not isinstance(owner, (SliceType, PortSliceType)):
        raise TgiError("Invalid HDL slice handle", TgiFaultCode.INVALID_ID)
    return owner


def _slice_paths(owner: SliceType | PortSliceType) -> SliceType.PathSegments | PortSliceType.PathSegments | None:
    """Validate the immediate holder and its version-specific path children."""
    holder = owner.path_segments
    if holder is None:
        return None
    holder_type = SliceType.PathSegments if isinstance(owner, SliceType) else PortSliceType.PathSegments
    segment_type = PathSegmentType if isinstance(owner, SliceType) else PortPathSegmentType
    if not isinstance(holder, holder_type) or not isinstance(holder.path_segment, (list, tuple)):
        raise TgiError("Invalid pathSegments model", TgiFaultCode.INVALID_ID)
    if any(not isinstance(child, segment_type) for child in holder.path_segment):
        raise TgiError("Invalid pathSegment model", TgiFaultCode.INVALID_ID)
    register_parent(holder, owner, ("path_segments",), "single")
    return holder


def _mode_port_slice(handle: str) -> ComponentType.Modes.Mode.PortSlice:
    """Resolve a mode port reference slice, excluding HDL access slices."""
    owner = resolve_handle(handle)
    if not isinstance(owner, _ModePortSlice):
        raise TgiError("Invalid mode portSlice handle", TgiFaultCode.INVALID_ID)
    return owner


def _sub_port_references(owner: ComponentType.Modes.Mode.PortSlice) -> Sequence[SubPortReference]:
    """Validate the ordered sub-port reference path before traversal or mutation."""
    children = owner.sub_port_reference
    if not isinstance(children, (list, tuple)) or any(not isinstance(child, SubPortReference) for child in children):
        raise TgiError("Invalid subPortReference model", TgiFaultCode.INVALID_ID)
    if any(not isinstance(child.sub_port_ref, str) for child in children):
        raise TgiError("Invalid subPortRef source", TgiFaultCode.INVALID_ID)
    return children


def _resolve(objID: str) -> Any | None:
    return resolve_handle(objID)


def _maybe(obj: Any, attr: str) -> Any | None:
    return getattr(obj, attr, None) if obj is not None else None


def _ensure_slice_parent(sliceID: str) -> Any:
    sl = _resolve(sliceID)
    if sl is None:
        raise TgiError("Invalid slice handle", TgiFaultCode.INVALID_ID)
    return sl


def _value_expr(node: Any) -> tuple[Any | None, str | None, str | None]:
    if node is None:
        return (None, None, None)
    v = getattr(node, "value", None)
    expr = getattr(v, "expression", None) if v is not None else None
    val = getattr(v, "value", None) if v is not None else None
    return (val, expr, get_handle(node))


# ---------------------------------------------------------------------------
# BASE (F.7.77)
# ---------------------------------------------------------------------------


def getFieldSliceAddressBlockRefByID(fieldSliceID: str, addressBlockID: str) -> str | None:  # F.7.77.1
    sl = _resolve(fieldSliceID)
    abr = _maybe(sl, "address_block_ref")
    if abr is None:
        return None
    return get_handle(abr) if get_handle(abr) == addressBlockID else None


def getFieldSliceAddressBlockRefByName(fieldSliceID: str, name: str) -> str | None:  # F.7.77.2
    sl = _resolve(fieldSliceID)
    abr = _maybe(sl, "address_block_ref")
    if abr is None:
        return None
    return get_handle(abr) if getattr(abr, "name", None) == name else None


def getFieldSliceAddressBlockRefID(fieldSliceID: str) -> str | None:  # F.7.77.3
    sl = _resolve(fieldSliceID)
    abr = _maybe(sl, "address_block_ref")
    return None if abr is None else get_handle(abr)


def getFieldSliceAddressSpaceRefByID(fieldSliceID: str, addressSpaceID: str) -> str | None:  # F.7.77.4
    sl = _resolve(fieldSliceID)
    asr = _maybe(sl, "address_space_ref")
    if asr is None:
        return None
    return get_handle(asr) if get_handle(asr) == addressSpaceID else None


def getFieldSliceAddressSpaceRefByName(fieldSliceID: str, name: str) -> str | None:  # F.7.77.5
    sl = _resolve(fieldSliceID)
    asr = _maybe(sl, "address_space_ref")
    if asr is None:
        return None
    return get_handle(asr) if getattr(asr, "name", None) == name else None


def getFieldSliceAddressSpaceRefID(fieldSliceID: str) -> str | None:  # F.7.77.6
    sl = _resolve(fieldSliceID)
    asr = _maybe(sl, "address_space_ref")
    return None if asr is None else get_handle(asr)


def getFieldSliceAlternateRegisterRefByID(fieldSliceID: str, altRegisterID: str) -> str | None:  # F.7.77.7
    sl = _resolve(fieldSliceID)
    arr = _maybe(sl, "alternate_register_ref")
    if arr is None:
        return None
    return get_handle(arr) if get_handle(arr) == altRegisterID else None


def getFieldSliceAlternateRegisterRefByName(fieldSliceID: str, name: str) -> str | None:  # F.7.77.8
    sl = _resolve(fieldSliceID)
    arr = _maybe(sl, "alternate_register_ref")
    if arr is None:
        return None
    return get_handle(arr) if getattr(arr, "name", None) == name else None


def getFieldSliceAlternateRegisterRefID(fieldSliceID: str) -> str | None:  # F.7.77.9
    sl = _resolve(fieldSliceID)
    arr = _maybe(sl, "alternate_register_ref")
    return None if arr is None else get_handle(arr)


def getFieldSliceBankRefByNames(
    fieldSliceID: str,
    vendor: str,
    library: str,
    name: str,
    version: str,
) -> str | None:  # F.7.77.10
    sl = _resolve(fieldSliceID)
    banks = getattr(sl, "bank_ref", []) if sl is not None else []
    for b in banks:
        if (
            getattr(b, "vendor", None),
            getattr(b, "library", None),
            getattr(b, "name", None),
            getattr(b, "version", None),
        ) == (vendor, library, name, version):
            return get_handle(b)
    return None


def getFieldSliceBankRefIDs(fieldSliceID: str) -> list[str]:  # F.7.77.11
    sl = _resolve(fieldSliceID)
    if sl is None:
        return []
    return [get_handle(b) for b in getattr(sl, "bank_ref", [])]


def getFieldSliceFieldRefByName(fieldSliceID: str, name: str) -> str | None:  # F.7.77.12
    sl = _resolve(fieldSliceID)
    fr = _maybe(sl, "field_ref")
    if fr is None:
        return None
    return get_handle(fr) if getattr(fr, "name", None) == name else None


def getFieldSliceFieldRefID(fieldSliceID: str) -> str | None:  # F.7.77.13
    sl = _resolve(fieldSliceID)
    fr = _maybe(sl, "field_ref")
    return None if fr is None else get_handle(fr)


def getFieldSliceMemoryMapRefByID(fieldSliceID: str, memoryMapID: str) -> str | None:  # F.7.77.14
    sl = _resolve(fieldSliceID)
    mm = _maybe(sl, "memory_map_ref")
    if mm is None:
        return None
    return get_handle(mm) if get_handle(mm) == memoryMapID else None


def getFieldSliceMemoryMapRefByName(fieldSliceID: str, name: str) -> str | None:  # F.7.77.15
    sl = _resolve(fieldSliceID)
    mm = _maybe(sl, "memory_map_ref")
    if mm is None:
        return None
    return get_handle(mm) if getattr(mm, "name", None) == name else None


def getFieldSliceMemoryMapRefID(fieldSliceID: str) -> str | None:  # F.7.77.16
    sl = _resolve(fieldSliceID)
    mm = _maybe(sl, "memory_map_ref")
    return None if mm is None else get_handle(mm)


def getFieldSliceMemoryRemapRefByID(fieldSliceID: str, memoryRemapID: str) -> str | None:  # F.7.77.17
    sl = _resolve(fieldSliceID)
    mr = _maybe(sl, "memory_remap_ref")
    if mr is None:
        return None
    return get_handle(mr) if get_handle(mr) == memoryRemapID else None


def getFieldSliceMemoryRemapRefByName(fieldSliceID: str, name: str) -> str | None:  # F.7.77.18
    sl = _resolve(fieldSliceID)
    mr = _maybe(sl, "memory_remap_ref")
    if mr is None:
        return None
    return get_handle(mr) if getattr(mr, "name", None) == name else None


def getFieldSliceMemoryRemapRefID(fieldSliceID: str) -> str | None:  # F.7.77.19
    sl = _resolve(fieldSliceID)
    mr = _maybe(sl, "memory_remap_ref")
    return None if mr is None else get_handle(mr)


def getFieldSliceRange(fieldSliceID: str) -> int | None:  # F.7.77.20
    sl = _resolve(fieldSliceID)
    rng = _maybe(sl, "range")
    val, _, _ = _value_expr(rng)
    return val


def getFieldSliceRangeLeftID(fieldSliceID: str) -> str | None:  # F.7.77.21
    sl = _resolve(fieldSliceID)
    rng = _maybe(sl, "range")
    left = getattr(rng, "left", None) if rng is not None else None
    return None if left is None else get_handle(left)


def getFieldSliceRangeRightID(fieldSliceID: str) -> str | None:  # F.7.77.22
    sl = _resolve(fieldSliceID)
    rng = _maybe(sl, "range")
    right = getattr(rng, "right", None) if rng is not None else None
    return None if right is None else get_handle(right)


def getLocationSliceIDs(locationID: str) -> list[str]:  # F.7.77.28
    """Return ordered handles to slices in a location.

    Section: F.7.77.28.
    """
    location = resolve_handle(locationID)
    if not isinstance(location, SlicesType) or not isinstance(location.slice, (list, tuple)):
        raise TgiError("Invalid location handle", TgiFaultCode.INVALID_ID)
    if any(not isinstance(child, SliceType) for child in location.slice):
        raise TgiError("Invalid location slice model", TgiFaultCode.INVALID_ID)
    return _owned_list_ids(location, location.slice, "slice")


def getPortSlicePartSelectID(portSliceID: str) -> str | None:  # F.7.77.31
    """Return the owned part-select handle, when present.

    Section: F.7.77.31.
    """
    owner = _mode_port_slice(portSliceID)
    if owner.part_select is None:
        return None
    child = _part_select(get_handle(owner.part_select))
    register_parent(child, owner, ("part_select",), "single")
    return get_handle(child)


def getPortSlicePortRefByName(portSliceID: str) -> str:  # F.7.77.32
    """Return the referenced port name stored on the mode slice.

    Section: F.7.77.32.
    """
    owner = _mode_port_slice(portSliceID)
    if not isinstance(owner.port_ref, _ModePortSlice.PortRef) or not isinstance(owner.port_ref.port_ref, str):
        raise TgiError("Invalid portRef model", TgiFaultCode.INVALID_ID)
    register_parent(owner.port_ref, owner, ("port_ref",), "single")
    return owner.port_ref.port_ref


def getPortSliceSubPortReferenceIDs(portSliceID: str) -> list[str]:  # F.7.77.33
    """Return the ordered referenced sub-port names specified by the Annex.

    Section: F.7.77.33.
    """
    owner = _mode_port_slice(portSliceID)
    children = _sub_port_references(owner)
    _owned_list_ids(owner, children, "sub_port_reference")
    return [child.sub_port_ref for child in children]


def getSlicePathSegmentIDs(sliceID: str) -> list[str]:  # F.7.77.34
    """Return ordered path-segment handles with immediate ownership.

    Section: F.7.77.34.
    """
    holder = _slice_paths(_hdl_slice(sliceID))
    return [] if holder is None else _owned_list_ids(holder, holder.path_segment, "path_segment")


def getSliceRange(sliceID: str) -> tuple[int | None, int | None]:  # F.7.77.35
    """Return evaluated left/right values of an HDL slice range.

    Section: F.7.77.35.
    """
    return (_range_value(getSliceRangeLeftID(sliceID)), _range_value(getSliceRangeRightID(sliceID)))


def getSliceRangeExpression(sliceID: str) -> tuple[str | None, str | None]:  # F.7.77.36
    """Return the original ordered endpoint expression sources.

    Section: F.7.77.36.
    """
    left_id, right_id = getSliceRangeLeftID(sliceID), getSliceRangeRightID(sliceID)
    return (None if left_id is None else getExpression(left_id), None if right_id is None else getExpression(right_id))


def getSliceRangeLeftID(sliceID: str) -> str | None:  # F.7.77.37
    """Return the owned left endpoint handle, if present.

    Section: F.7.77.37.
    """
    endpoint = _range_endpoint(_hdl_slice(sliceID), "left", Left)
    return None if endpoint is None else get_handle(endpoint)


def getSliceRangeRightID(sliceID: str) -> str | None:  # F.7.77.38
    """Return the owned right endpoint handle, if present.

    Section: F.7.77.38.
    """
    endpoint = _range_endpoint(_hdl_slice(sliceID), "right", Right)
    return None if endpoint is None else get_handle(endpoint)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.78)
# ---------------------------------------------------------------------------


def addFieldSliceBankRef(fieldSliceID: str, vlnv: tuple[str, str, str, str]) -> str:  # F.7.78.1
    sl = _ensure_slice_parent(fieldSliceID)
    from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType

    if getattr(sl, "bank_ref", None) is None:
        sl.bank_ref = []  # type: ignore[attr-defined]
    ref = LibraryRefType(vendor=vlnv[0], library=vlnv[1], name=vlnv[2], version=vlnv[3])
    sl.bank_ref.append(ref)  # type: ignore[attr-defined]
    register_parent(ref, sl, ("bank_ref",), "list")
    return get_handle(ref)


def addFieldSliceRegisterFileRef(fieldSliceID: str, name: str) -> str:  # F.7.78.2
    sl = _ensure_slice_parent(fieldSliceID)
    rfref = SimpleNamespace(name=name)
    sl.register_file_ref = rfref  # type: ignore[attr-defined]
    register_parent(rfref, sl, ("register_file_ref",), "single")
    return get_handle(rfref)


def addModeFieldSlice(modeID: str, fieldSliceID: str) -> bool:  # F.7.78.3
    mode = _resolve(modeID)
    sl = _resolve(fieldSliceID)
    if mode is None or sl is None:
        raise TgiError("Invalid mode or slice handle", TgiFaultCode.INVALID_ID)
    mode.field_slice = sl  # type: ignore[attr-defined]
    register_parent(sl, mode, ("field_slice",), "single")
    return True


def addModePortSlice(modeID: str, portSliceID: str) -> bool:  # F.7.78.4
    mode = _resolve(modeID)
    ps = _resolve(portSliceID)
    if mode is None or ps is None:
        raise TgiError("Invalid mode or portSlice handle", TgiFaultCode.INVALID_ID)
    mode.port_slice = ps  # type: ignore[attr-defined]
    register_parent(ps, mode, ("port_slice",), "single")
    return True


def addPortSliceSubPortReference(portSliceID: str, subPortRef: str) -> str:  # F.7.78.5
    """Append an owned generated reference to the hierarchical sub-port path.

    Section: F.7.78.5.
    """
    owner = _mode_port_slice(portSliceID)
    _sub_port_references(owner)
    source = _name(subPortRef, "portName")
    child = SubPortReference(sub_port_ref=source)
    _list_attr(owner, "sub_port_reference").append(child)
    getPortSliceSubPortReferenceIDs(portSliceID)
    return get_handle(child)


def addSlicePathSegment(sliceID: str, pathSegmentValue: str) -> str:  # F.7.78.6
    """Append a generated path segment with its string expression source.

    Section: F.7.78.6.
    """
    owner = _hdl_slice(sliceID)
    holder = _slice_paths(owner)
    source = _string_source(pathSegmentValue)
    if isinstance(owner, SliceType):
        child = PathSegmentType(value=source)
        if holder is None:
            holder = SliceType.PathSegments()
    else:
        child = PortPathSegmentType(value=source)
        if holder is None:
            holder = PortSliceType.PathSegments()
    _list_attr(holder, "path_segment").append(child)
    owner.path_segments = holder
    getSlicePathSegmentIDs(sliceID)
    return get_handle(child)


def removeFieldSliceAlternateRegisterRef(fieldSliceAlternateRegisterRefID: str) -> bool:  # F.7.78.7
    if resolve_handle(fieldSliceAlternateRegisterRefID) is None:
        raise TgiError("Invalid alternateRegisterRef", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(fieldSliceAlternateRegisterRefID)


def removeFieldSliceBankRef(fieldSliceBankRefID: str) -> bool:  # F.7.78.8
    if resolve_handle(fieldSliceBankRefID) is None:
        raise TgiError("Invalid bankRef handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(fieldSliceBankRefID)


def removeFieldSliceMemoryRemapRef(fieldSliceMemoryRemapRefID: str) -> bool:  # F.7.78.9
    if resolve_handle(fieldSliceMemoryRemapRefID) is None:
        raise TgiError("Invalid memoryRemapRef handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(fieldSliceMemoryRemapRefID)


def removeFieldSliceRange(fieldSliceRangeID: str) -> bool:  # F.7.78.10
    if resolve_handle(fieldSliceRangeID) is None:
        raise TgiError("Invalid range handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(fieldSliceRangeID)


def removeFieldSliceRegisterFileRef(fieldSliceRegisterFileRefID: str) -> bool:  # F.7.78.11
    if resolve_handle(fieldSliceRegisterFileRefID) is None:
        raise TgiError("Invalid registerFileRef handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(fieldSliceRegisterFileRefID)


def removeLocationSlice(sliceID: str) -> bool:  # F.7.78.12
    """Remove an owned location slice and invalidate its descendant handles.

    Section: F.7.78.12.
    """
    child = resolve_handle(sliceID)
    if not isinstance(child, SliceType):
        raise TgiError("Invalid location slice handle", TgiFaultCode.INVALID_ID)
    location = _register_owned_child(child, SlicesType)
    if not isinstance(location, SlicesType):
        raise TgiError("Slice has no owning location", TgiFaultCode.INVALID_ID)
    getLocationSliceIDs(get_handle(location))
    _list_attr(location, "slice")
    return _remove_owned(sliceID, SliceType, SlicesType, "location slice")


def removeModeFieldSlice(modeFieldSliceID: str) -> bool:  # F.7.78.13
    if resolve_handle(modeFieldSliceID) is None:
        raise TgiError("Invalid modeFieldSlice handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(modeFieldSliceID)


def removeModePortSlice(modePortSliceID: str) -> bool:  # F.7.78.14
    if resolve_handle(modePortSliceID) is None:
        raise TgiError("Invalid modePortSlice handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(modePortSliceID)


def removePortSlicePartSelect(portSliceID: str) -> bool:  # F.7.78.15
    """Remove a mode port slice's part-select and invalidate its descendants.

    Section: F.7.78.15.
    """
    owner = _mode_port_slice(portSliceID)
    if getPortSlicePartSelectID(portSliceID) is None:
        return False
    return _remove_child(owner, "part_select")


def removePortSliceSubPortReference(subPortReferenceID: str) -> bool:  # F.7.78.16
    """Remove an owned mode sub-port reference, discovering parsed ownership.

    Section: F.7.78.16.
    """
    child = resolve_handle(subPortReferenceID)
    if not isinstance(child, SubPortReference):
        raise TgiError("Invalid subPortReference handle", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(child, _ModePortSlice)
    if not isinstance(owner, _ModePortSlice):
        raise TgiError("Sub-port reference has no owning mode port slice", TgiFaultCode.INVALID_ID)
    getPortSliceSubPortReferenceIDs(get_handle(owner))
    _list_attr(owner, "sub_port_reference")
    return _remove_owned(subPortReferenceID, SubPortReference, _ModePortSlice, "sub-port reference")


def removeSlicePathSegment(pathSegmentID: str) -> bool:  # F.7.78.17
    """Remove an HDL slice path segment, retaining its required holder.

    Section: F.7.78.17.
    """
    child = resolve_handle(pathSegmentID)
    if isinstance(child, PathSegmentType):
        holder_type = SliceType.PathSegments
        owner_type = SliceType
    elif isinstance(child, PortPathSegmentType):
        holder_type = PortSliceType.PathSegments
        owner_type = PortSliceType
    else:
        raise TgiError("Invalid pathSegment handle", TgiFaultCode.INVALID_ID)
    holder = _register_owned_child(child, holder_type)
    if not isinstance(holder, holder_type):
        raise TgiError("Path segment has no owning slice holder", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, owner_type)
    if not isinstance(owner, owner_type):
        raise TgiError("Path segment has no owning HDL slice", TgiFaultCode.INVALID_ID)
    getSlicePathSegmentIDs(get_handle(owner))
    _list_attr(holder, "path_segment")
    return _remove_owned(pathSegmentID, type(child), holder_type, "path segment")


def removeSliceRange(sliceID: str) -> bool:  # F.7.78.18
    """Remove an HDL slice range and invalidate its descendant handles.

    Section: F.7.78.18.
    """
    return _remove_range(_hdl_slice(sliceID))


def setFieldSliceAddressBlockRef(fieldSliceID: str, name: str) -> bool:  # F.7.78.19
    sl = _ensure_slice_parent(fieldSliceID)
    sl.address_block_ref = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    register_parent(sl.address_block_ref, sl, ("address_block_ref",), "single")  # type: ignore[attr-defined]
    return True


def setFieldSliceAddressSpaceRef(fieldSliceID: str, name: str) -> bool:  # F.7.78.20
    sl = _ensure_slice_parent(fieldSliceID)
    sl.address_space_ref = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    register_parent(sl.address_space_ref, sl, ("address_space_ref",), "single")  # type: ignore[attr-defined]
    return True


def setFieldSliceAlternateRegisterRef(fieldSliceID: str, name: str) -> bool:  # F.7.78.21
    sl = _ensure_slice_parent(fieldSliceID)
    sl.alternate_register_ref = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    register_parent(sl.alternate_register_ref, sl, ("alternate_register_ref",), "single")  # type: ignore[attr-defined]
    return True


def setFieldSliceFieldRef(fieldSliceID: str, name: str) -> bool:  # F.7.78.22
    sl = _ensure_slice_parent(fieldSliceID)
    sl.field_ref = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    register_parent(sl.field_ref, sl, ("field_ref",), "single")  # type: ignore[attr-defined]
    return True


def setFieldSliceMemoryMapRef(fieldSliceID: str, name: str) -> bool:  # F.7.78.23
    sl = _ensure_slice_parent(fieldSliceID)
    sl.memory_map_ref = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    register_parent(sl.memory_map_ref, sl, ("memory_map_ref",), "single")  # type: ignore[attr-defined]
    return True


def setFieldSliceMemoryRemapRef(fieldSliceID: str, name: str) -> bool:  # F.7.78.24
    sl = _ensure_slice_parent(fieldSliceID)
    sl.memory_remap_ref = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    register_parent(sl.memory_remap_ref, sl, ("memory_remap_ref",), "single")  # type: ignore[attr-defined]
    return True


def setFieldSliceRange(fieldSliceID: str, value: int | None = None, expression: str | None = None) -> bool:  # F.7.78.25
    if value is None and expression is None:
        raise TgiError("value or expression required", TgiFaultCode.INVALID_ARGUMENT)
    sl = _ensure_slice_parent(fieldSliceID)
    sl.range = SimpleNamespace(value=SimpleNamespace(value=value, expression=expression))  # type: ignore[attr-defined]
    register_parent(sl.range, sl, ("range",), "single")  # type: ignore[attr-defined]
    return True


def setFieldSliceRegisterRef(fieldSliceID: str, name: str) -> bool:  # F.7.78.26
    sl = _ensure_slice_parent(fieldSliceID)
    sl.register_ref = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    register_parent(sl.register_ref, sl, ("register_ref",), "single")  # type: ignore[attr-defined]
    return True


def setPortSlicePartSelect(
    portSliceID: str, range: Sequence[str] | None, indices: Sequence[str] | None
) -> bool:  # F.7.78.27
    """Set generated range and index choices through the shared atomic setter.

    Section: F.7.78.27.
    """
    owner = _mode_port_slice(portSliceID)
    _set_part_select(owner, range, indices)
    getPortSlicePartSelectID(portSliceID)
    return True


def setPortSlicePortRef(portSliceID: str, portRef: str) -> bool:  # F.7.78.28
    """Set the normalized referenced port name while retaining its wrapper.

    Section: F.7.78.28.
    """
    owner = _mode_port_slice(portSliceID)
    source = _name(portRef, "portName")
    if owner.port_ref is None:
        owner.port_ref = _ModePortSlice.PortRef(port_ref=source)
    elif not isinstance(owner.port_ref, _ModePortSlice.PortRef):
        raise TgiError("Invalid portRef model", TgiFaultCode.INVALID_ID)
    else:
        owner.port_ref.port_ref = source
    register_parent(owner.port_ref, owner, ("port_ref",), "single")
    return True


def setSliceRange(sliceID: str, range: Sequence[str]) -> bool:  # F.7.78.29
    """Set two HDL slice endpoint sources atomically, retaining existing metadata.

    Section: F.7.78.29.
    """
    return _set_range(_hdl_slice(sliceID), range)
