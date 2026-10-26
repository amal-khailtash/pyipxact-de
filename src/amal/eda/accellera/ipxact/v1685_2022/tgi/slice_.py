"""Slice category TGI functions (IEEE 1685-2022).

Named ``slice_`` to avoid clashing with Python's built-in ``slice``. Implements
BASE (F.7.77) and EXTENDED (F.7.78) Slice functions. Implemented HDL path and range
getters, field-range getters and mode port-reference getters reject invalid
handles; named-reference getters use generated wrappers and target getters
resolve the stored hierarchical reference in the containing document. Optional
absent references return ``None``. EXTENDED mutators raise
``TgiError`` with ``TgiFaultCode.INVALID_ID`` for invalid handles and
``TgiFaultCode.INVALID_ARGUMENT`` for semantic issues.

HDL path and range access uses generated slice, path-segment, range, and
endpoint models, shared with field reference ranges. Mode port references use
generated wrappers and part-selects.
Address-block, field and alternate-register names retain generated wrappers.
Mode and field-map reference mutations use generated schema objects with
shared ownership and removal helpers.
"""

# ruff: noqa: I001
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
    FieldMap,
    SubPortReference,
    AddressBlockRef,
    AlternateRegisterRef,
    FieldRef,
    MemoryRemapRef,
    BankRef,
    RegisterFileRef,
    RegisterRef,
)

from ._reference_choices import _reference_choice, _set_reference_choice
from ._reference_paths import _append_reference_path, _remove_reference_path, _set_named_reference
from ._ranges import _range_endpoint, _range_sources, _range_value, _remove_range, _set_range
from ._expressions import _string_source
from ._model import _owned_list_ids, _sub_port_references, _reference_list as _field_reference_list
from .address_space import _register_owned_child, _remove_owned
from .component import _list_attr
from .port_map import _child_id, _name, _set_part_select, _remove_child
from ._attribute_references import _reference_source as _field_reference_value, resolve_attribute_reference
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
    "getFieldSliceRegisterFileRefByNames",
    "getFieldSliceRegisterFileRefIDs",
    "getFieldSliceRegisterRefByID",
    "getFieldSliceRegisterRefByName",
    "getFieldSliceRegisterRefID",
    "getLocationSliceIDs",
    "getModeFieldSliceIDs",
    "getModePortSliceIDs",
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


_FieldAddressSpaceRef = ComponentType.Modes.Mode.FieldSlice.AddressSpaceRef | FieldMap.FieldSlice.AddressSpaceRef
_FieldMemoryMapRef = ComponentType.Modes.Mode.FieldSlice.MemoryMapRef | FieldMap.FieldSlice.MemoryMapRef
_FieldChoiceRef = _FieldAddressSpaceRef | _FieldMemoryMapRef | MemoryRemapRef
_FIELD_CHOICE = "address_space_ref_or_memory_map_ref_or_memory_remap_ref"


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


def _field_slice(handle: str) -> ComponentType.Modes.Mode.FieldSlice | FieldMap.FieldSlice:
    """Resolve generated field reference slices sharing fieldSliceReferenceGroup."""
    owner = resolve_handle(handle)
    if not isinstance(owner, (ComponentType.Modes.Mode.FieldSlice, FieldMap.FieldSlice)):
        raise TgiError("Invalid fieldSlice handle", TgiFaultCode.INVALID_ID)
    return owner


def _field_reference_target(reference_id: str | None, xml_name: str) -> str | None:
    """Validate a named wrapper before resolving its referenced generated target."""
    if reference_id is None:
        return None
    _field_reference_value(reference_id, xml_name)
    return resolve_attribute_reference(reference_id, xml_name)


def _field_choice(
    owner: ComponentType.Modes.Mode.FieldSlice | FieldMap.FieldSlice,
) -> tuple[_FieldAddressSpaceRef | None, _FieldMemoryMapRef | None, MemoryRemapRef | None]:
    """Validate the generated address-space or memory-map/remap reference choice."""
    address_type = (
        ComponentType.Modes.Mode.FieldSlice.AddressSpaceRef
        if isinstance(owner, ComponentType.Modes.Mode.FieldSlice)
        else FieldMap.FieldSlice.AddressSpaceRef
    )
    map_type = (
        ComponentType.Modes.Mode.FieldSlice.MemoryMapRef
        if isinstance(owner, ComponentType.Modes.Mode.FieldSlice)
        else FieldMap.FieldSlice.MemoryMapRef
    )
    return _reference_choice(owner, address_type, map_type)


def _set_field_choice(
    owner: ComponentType.Modes.Mode.FieldSlice | FieldMap.FieldSlice, replacement: _FieldChoiceRef, attribute: str
) -> bool:
    """Update a reference choice, invalidating only alternatives removed from it."""
    address_type = (
        ComponentType.Modes.Mode.FieldSlice.AddressSpaceRef
        if isinstance(owner, ComponentType.Modes.Mode.FieldSlice)
        else FieldMap.FieldSlice.AddressSpaceRef
    )
    map_type = (
        ComponentType.Modes.Mode.FieldSlice.MemoryMapRef
        if isinstance(owner, ComponentType.Modes.Mode.FieldSlice)
        else FieldMap.FieldSlice.MemoryMapRef
    )
    return _set_reference_choice(owner, replacement, attribute, address_type, map_type)


def _set_field_reference(
    owner: ComponentType.Modes.Mode.FieldSlice | FieldMap.FieldSlice,
    attribute: str,
    replacement: AddressBlockRef | AlternateRegisterRef | FieldRef | RegisterRef,
) -> bool:
    """Attach a missing wrapper or update its source without replacing indices."""
    return _set_named_reference(owner, attribute, replacement)


def _add_field_reference[T: BankRef | RegisterFileRef](
    field_slice_id: str, source: str, attribute: str, model_type: type[T]
) -> str:
    """Append a generated named reference to its ordered owned path."""
    return _append_reference_path(_field_slice(field_slice_id), source, attribute, model_type)


def _remove_field_reference[T: BankRef | RegisterFileRef](
    reference_id: str, attribute: str, model_type: type[T]
) -> bool:
    """Remove an owned reference, discovering parsed ownership before detachment."""
    child = resolve_handle(reference_id)
    if not isinstance(child, model_type):
        raise TgiError("Invalid field reference handle", TgiFaultCode.INVALID_ID)
    owner_type = (ComponentType.Modes.Mode.FieldSlice, FieldMap.FieldSlice)
    owner = _register_owned_child(child, owner_type)
    if not isinstance(owner, owner_type):
        raise TgiError("Reference has no owning field slice", TgiFaultCode.INVALID_ID)
    return _remove_reference_path(owner, reference_id, attribute, model_type)


def _mode_slice_list[T: ComponentType.Modes.Mode.FieldSlice | ComponentType.Modes.Mode.PortSlice](
    mode_id: str, attribute: str, model_type: type[T]
) -> tuple[ComponentType.Modes.Mode, Sequence[T]]:
    """Validate a mode's generated slice list for traversal and mutation."""
    owner = resolve_handle(mode_id)
    if not isinstance(owner, ComponentType.Modes.Mode):
        raise TgiError("Invalid mode handle", TgiFaultCode.INVALID_ID)
    children = getattr(owner, attribute)
    if not isinstance(children, (list, tuple)) or any(not isinstance(child, model_type) for child in children):
        raise TgiError("Invalid mode slice list", TgiFaultCode.INVALID_ID)
    return owner, children


def _remove_mode_slice[T: ComponentType.Modes.Mode.FieldSlice | ComponentType.Modes.Mode.PortSlice](
    slice_id: str, attribute: str, model_type: type[T]
) -> bool:
    """Remove a mode slice and descendants, discovering parsed ownership."""
    child = resolve_handle(slice_id)
    if not isinstance(child, model_type):
        raise TgiError("Invalid mode slice handle", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(child, ComponentType.Modes.Mode)
    if not isinstance(owner, ComponentType.Modes.Mode):
        raise TgiError("Slice has no owning mode", TgiFaultCode.INVALID_ID)
    owner, children = _mode_slice_list(get_handle(owner), attribute, model_type)
    _owned_list_ids(owner, children, attribute)
    _list_attr(owner, attribute)
    return _remove_owned(slice_id, model_type, ComponentType.Modes.Mode, "mode slice")


# ---------------------------------------------------------------------------
# BASE (F.7.77)
# ---------------------------------------------------------------------------


def getFieldSliceAddressBlockRefByID(fieldSliceID: str) -> str | None:  # F.7.77.1
    """Return the referenced addressBlock model handle. Section: F.7.77.1."""
    reference_id = getFieldSliceAddressBlockRefID(fieldSliceID)
    return _field_reference_target(reference_id, "addressBlockRef")


def getFieldSliceAddressBlockRefByName(fieldSliceID: str) -> str | None:  # F.7.77.2
    """Return the stored referenced address-block name.

    Section: F.7.77.2.
    """
    return _field_reference_value(getFieldSliceAddressBlockRefID(fieldSliceID), "addressBlockRef")


def getFieldSliceAddressBlockRefID(fieldSliceID: str) -> str | None:  # F.7.77.3
    """Return the owned generated addressBlockRef handle, when present.

    Section: F.7.77.3.
    """
    return _child_id(_field_slice(fieldSliceID), "address_block_ref", AddressBlockRef)


def getFieldSliceAddressSpaceRefByID(fieldSliceID: str) -> str | None:  # F.7.77.4
    """Return the referenced addressSpace model handle. Section: F.7.77.4."""
    reference_id = getFieldSliceAddressSpaceRefID(fieldSliceID)
    return _field_reference_target(reference_id, "addressSpaceRef")


def getFieldSliceAddressSpaceRefByName(fieldSliceID: str) -> str | None:  # F.7.77.5
    """Return the stored addressSpaceRef name from the generated choice.

    Section: F.7.77.5.
    """
    return _field_reference_value(getFieldSliceAddressSpaceRefID(fieldSliceID), "addressSpaceRef")


def getFieldSliceAddressSpaceRefID(fieldSliceID: str) -> str | None:  # F.7.77.6
    """Return the owned addressSpaceRef wrapper handle, when selected.

    Section: F.7.77.6.
    """
    child = _field_choice(_field_slice(fieldSliceID))[0]
    return None if child is None else get_handle(child)


def getFieldSliceAlternateRegisterRefByID(fieldSliceID: str) -> str | None:  # F.7.77.7
    """Return the referenced alternateRegister model handle. Section: F.7.77.7."""
    reference_id = getFieldSliceAlternateRegisterRefID(fieldSliceID)
    return _field_reference_target(reference_id, "alternateRegisterRef")


def getFieldSliceAlternateRegisterRefByName(fieldSliceID: str) -> str | None:  # F.7.77.8
    """Return the stored referenced alternate-register name.

    Section: F.7.77.8.
    """
    return _field_reference_value(getFieldSliceAlternateRegisterRefID(fieldSliceID), "alternateRegisterRef")


def getFieldSliceAlternateRegisterRefID(fieldSliceID: str) -> str | None:  # F.7.77.9
    """Return the owned alternateRegisterRef handle, when present.

    Section: F.7.77.9.
    """
    return _child_id(_field_slice(fieldSliceID), "alternate_register_ref", AlternateRegisterRef)


def getFieldSliceBankRefByNames(fieldSliceID: str) -> list[str]:  # F.7.77.10
    """Return the ordered referenced bank names. Section: F.7.77.10."""
    return [_field_reference_value(handle, "bankRef") for handle in getFieldSliceBankRefIDs(fieldSliceID)]


def getFieldSliceBankRefIDs(fieldSliceID: str) -> list[str]:  # F.7.77.11
    """Return owned handles in hierarchical bank-reference order. Section: F.7.77.11."""
    owner = _field_slice(fieldSliceID)
    return _owned_list_ids(owner, _field_reference_list(owner, "bank_ref", BankRef), "bank_ref")


def getFieldSliceFieldRefByName(fieldSliceID: str) -> str | None:  # F.7.77.12
    """Return the stored referenced field name.

    Section: F.7.77.12.
    """
    return _field_reference_value(getFieldSliceFieldRefID(fieldSliceID), "fieldRef")


def getFieldSliceFieldRefID(fieldSliceID: str) -> str | None:  # F.7.77.13
    """Return the owned generated fieldRef handle, when present.

    Section: F.7.77.13.
    """
    return _child_id(_field_slice(fieldSliceID), "field_ref", FieldRef)


def getFieldSliceMemoryMapRefByID(fieldSliceID: str) -> str | None:  # F.7.77.14
    """Return the referenced memoryMap model handle. Section: F.7.77.14."""
    reference_id = getFieldSliceMemoryMapRefID(fieldSliceID)
    return _field_reference_target(reference_id, "memoryMapRef")


def getFieldSliceMemoryMapRefByName(fieldSliceID: str) -> str | None:  # F.7.77.15
    """Return the stored memoryMapRef name from the generated choice.

    Section: F.7.77.15.
    """
    return _field_reference_value(getFieldSliceMemoryMapRefID(fieldSliceID), "memoryMapRef")


def getFieldSliceMemoryMapRefID(fieldSliceID: str) -> str | None:  # F.7.77.16
    """Return the owned memoryMapRef wrapper handle, when selected.

    Section: F.7.77.16.
    """
    child = _field_choice(_field_slice(fieldSliceID))[1]
    return None if child is None else get_handle(child)


def getFieldSliceMemoryRemapRefByID(fieldSliceID: str) -> str | None:  # F.7.77.17
    """Return the referenced memoryRemap model handle. Section: F.7.77.17."""
    reference_id = getFieldSliceMemoryRemapRefID(fieldSliceID)
    return _field_reference_target(reference_id, "memoryRemapRef")


def getFieldSliceMemoryRemapRefByName(fieldSliceID: str) -> str | None:  # F.7.77.18
    """Return the stored memoryRemapRef name from the generated choice.

    Section: F.7.77.18.
    """
    return _field_reference_value(getFieldSliceMemoryRemapRefID(fieldSliceID), "memoryRemapRef")


def getFieldSliceMemoryRemapRefID(fieldSliceID: str) -> str | None:  # F.7.77.19
    """Return the owned memoryRemapRef wrapper handle, when selected.

    Section: F.7.77.19.
    """
    child = _field_choice(_field_slice(fieldSliceID))[2]
    return None if child is None else get_handle(child)


def getFieldSliceRange(fieldSliceID: str) -> tuple[str | None, str | None]:  # F.7.77.20
    """Return the ordered range expression sources required by the String array contract.

    Section: F.7.77.20.
    """
    return _range_sources(getFieldSliceRangeLeftID(fieldSliceID), getFieldSliceRangeRightID(fieldSliceID))


def getFieldSliceRangeLeftID(fieldSliceID: str) -> str | None:  # F.7.77.21
    """Return the owned left range endpoint handle, when present.

    Section: F.7.77.21.
    """
    endpoint = _range_endpoint(_field_slice(fieldSliceID), "left", Left)
    return None if endpoint is None else get_handle(endpoint)


def getFieldSliceRangeRightID(fieldSliceID: str) -> str | None:  # F.7.77.22
    """Return the owned right range endpoint handle, when present.

    Section: F.7.77.22.
    """
    endpoint = _range_endpoint(_field_slice(fieldSliceID), "right", Right)
    return None if endpoint is None else get_handle(endpoint)


def getFieldSliceRegisterFileRefByNames(fieldSliceID: str) -> list[str]:  # F.7.77.23
    """Return the ordered referenced register-file names. Section: F.7.77.23."""
    return [
        _field_reference_value(handle, "registerFileRef") for handle in getFieldSliceRegisterFileRefIDs(fieldSliceID)
    ]


def getFieldSliceRegisterFileRefIDs(fieldSliceID: str) -> list[str]:  # F.7.77.24
    """Return owned handles in register-file-reference order. Section: F.7.77.24."""
    owner = _field_slice(fieldSliceID)
    return _owned_list_ids(
        owner, _field_reference_list(owner, "register_file_ref", RegisterFileRef), "register_file_ref"
    )


def getFieldSliceRegisterRefByID(fieldSliceID: str) -> str | None:  # F.7.77.25
    """Return the referenced register model handle. Section: F.7.77.25."""
    reference_id = getFieldSliceRegisterRefID(fieldSliceID)
    return _field_reference_target(reference_id, "registerRef")


def getFieldSliceRegisterRefByName(fieldSliceID: str) -> str | None:  # F.7.77.26
    """Return the stored referenced register name. Section: F.7.77.26."""
    return _field_reference_value(getFieldSliceRegisterRefID(fieldSliceID), "registerRef")


def getFieldSliceRegisterRefID(fieldSliceID: str) -> str | None:  # F.7.77.27
    """Return the owned generated registerRef wrapper handle. Section: F.7.77.27."""
    return _child_id(_field_slice(fieldSliceID), "register_ref", RegisterRef)


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


def getModeFieldSliceIDs(modeID: str) -> list[str]:  # F.7.77.29
    """Return ordered handles to the mode's field slices. Section: F.7.77.29."""
    owner, children = _mode_slice_list(modeID, "field_slice", ComponentType.Modes.Mode.FieldSlice)
    return _owned_list_ids(owner, children, "field_slice")


def getModePortSliceIDs(modeID: str) -> list[str]:  # F.7.77.30
    """Return ordered handles to the mode's port slices. Section: F.7.77.30."""
    owner, children = _mode_slice_list(modeID, "port_slice", _ModePortSlice)
    return _owned_list_ids(owner, children, "port_slice")


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
    return _range_sources(getSliceRangeLeftID(sliceID), getSliceRangeRightID(sliceID))


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


def addFieldSliceBankRef(fieldSliceID: str, bankRef: str) -> str:  # F.7.78.1
    """Append a normalized generated bank reference. Section: F.7.78.1."""
    return _add_field_reference(fieldSliceID, bankRef, "bank_ref", BankRef)


def addFieldSliceRegisterFileRef(fieldSliceID: str, registerFileRef: str) -> str:  # F.7.78.2
    """Append a normalized generated register-file reference. Section: F.7.78.2."""
    return _add_field_reference(fieldSliceID, registerFileRef, "register_file_ref", RegisterFileRef)


def addModeFieldSlice(
    modeID: str, name: str, memoryMapRef: str, addressBlockRef: str, registerRef: str, fieldRef: str
) -> str:  # F.7.78.3
    """Build an owned mode field slice with all required named references.

    Section: F.7.78.3; the Annex and WSDL specify the four reference arguments.
    """
    owner, _ = _mode_slice_list(modeID, "field_slice", ComponentType.Modes.Mode.FieldSlice)
    sources = tuple(_name(source, "Name") for source in (name, memoryMapRef, addressBlockRef, registerRef, fieldRef))
    child = ComponentType.Modes.Mode.FieldSlice(
        name=sources[0],
        address_block_ref=AddressBlockRef(address_block_ref=sources[2]),
        register_ref=RegisterRef(register_ref=sources[3]),
        field_ref=FieldRef(field_ref=sources[4]),
    )
    handle = get_handle(child)
    setFieldSliceMemoryMapRef(handle, sources[1])
    _list_attr(owner, "field_slice").append(child)
    getModeFieldSliceIDs(modeID)
    return handle


def addModePortSlice(modeID: str, name: str, portRef: str) -> str:  # F.7.78.4
    """Build an owned mode port slice with its required port reference. Section: F.7.78.4."""
    owner, _ = _mode_slice_list(modeID, "port_slice", _ModePortSlice)
    source_name, source_ref = _name(name, "Name"), _name(portRef, "portName")
    child = _ModePortSlice(name=source_name, port_ref=_ModePortSlice.PortRef(port_ref=source_ref))
    _list_attr(owner, "port_slice").append(child)
    getModePortSliceIDs(modeID)
    return get_handle(child)


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


def removeFieldSliceAlternateRegisterRef(fieldSliceID: str) -> bool:  # F.7.78.7
    """Remove the owner's optional alternate-register wrapper.

    Section: F.7.78.7.
    """
    owner = _field_slice(fieldSliceID)
    if getFieldSliceAlternateRegisterRefID(fieldSliceID) is None:
        return False
    return _remove_child(owner, "alternate_register_ref")


def removeFieldSliceBankRef(fieldSliceBankRefID: str) -> bool:  # F.7.78.8
    """Remove an owned bank-reference path entry. Section: F.7.78.8."""
    return _remove_field_reference(fieldSliceBankRefID, "bank_ref", BankRef)


def removeFieldSliceMemoryRemapRef(fieldSliceID: str) -> bool:  # F.7.78.9
    """Remove the owner's optional remap reference while retaining its memory map.

    Section: F.7.78.9.
    """
    owner = _field_slice(fieldSliceID)
    remap_id = getFieldSliceMemoryRemapRefID(fieldSliceID)
    if remap_id is None:
        return False
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = list(
        owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    )
    return detach_child_by_handle(remap_id)


def removeFieldSliceRange(fieldSliceID: str) -> bool:  # F.7.78.10
    """Remove a field slice's range and invalidate its endpoint descendants.

    Section: F.7.78.10.
    """
    return _remove_range(_field_slice(fieldSliceID))


def removeFieldSliceRegisterFileRef(fieldSliceRegisterFileRefID: str) -> bool:  # F.7.78.11
    """Remove an owned register-file reference and its indices. Section: F.7.78.11."""
    return _remove_field_reference(fieldSliceRegisterFileRefID, "register_file_ref", RegisterFileRef)


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
    """Remove an owned mode field slice and its reference descendants. Section: F.7.78.13."""
    return _remove_mode_slice(modeFieldSliceID, "field_slice", ComponentType.Modes.Mode.FieldSlice)


def removeModePortSlice(modePortSliceID: str) -> bool:  # F.7.78.14
    """Remove an owned mode port slice and its descendants. Section: F.7.78.14."""
    return _remove_mode_slice(modePortSliceID, "port_slice", _ModePortSlice)


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


def setFieldSliceAddressBlockRef(fieldSliceID: str, addressBlockRef: str) -> bool:  # F.7.78.19
    """Set a normalized address-block name while retaining its reference indices.

    Section: F.7.78.19.
    """
    owner = _field_slice(fieldSliceID)
    child = AddressBlockRef(address_block_ref=_name(addressBlockRef, "Name"))
    return _set_field_reference(owner, "address_block_ref", child)


def setFieldSliceAddressSpaceRef(fieldSliceID: str, addressSpaceRef: str) -> bool:  # F.7.78.20
    """Set the normalized addressSpaceRef while preserving compatible choice wrappers.

    Section: F.7.78.20.
    """
    owner = _field_slice(fieldSliceID)
    model_type = (
        ComponentType.Modes.Mode.FieldSlice.AddressSpaceRef
        if isinstance(owner, ComponentType.Modes.Mode.FieldSlice)
        else FieldMap.FieldSlice.AddressSpaceRef
    )
    child = model_type(address_space_ref=_name(addressSpaceRef, "Name"))
    return _set_field_choice(owner, child, "address_space_ref")


def setFieldSliceAlternateRegisterRef(fieldSliceID: str, alternateRegisterRef: str) -> bool:  # F.7.78.21
    """Set the normalized alternate-register name, preserving an existing wrapper.

    Section: F.7.78.21.
    """
    owner = _field_slice(fieldSliceID)
    child = AlternateRegisterRef(alternate_register_ref=_name(alternateRegisterRef, "Name"))
    return _set_field_reference(owner, "alternate_register_ref", child)


def setFieldSliceFieldRef(fieldSliceID: str, fieldRef: str) -> bool:  # F.7.78.22
    """Set a normalized field name while retaining its reference indices.

    Section: F.7.78.22.
    """
    owner = _field_slice(fieldSliceID)
    child = FieldRef(field_ref=_name(fieldRef, "Name"))
    return _set_field_reference(owner, "field_ref", child)


def setFieldSliceMemoryMapRef(fieldSliceID: str, memoryMapRef: str) -> bool:  # F.7.78.23
    """Set the normalized memoryMapRef while preserving compatible choice wrappers.

    Section: F.7.78.23.
    """
    owner = _field_slice(fieldSliceID)
    model_type = (
        ComponentType.Modes.Mode.FieldSlice.MemoryMapRef
        if isinstance(owner, ComponentType.Modes.Mode.FieldSlice)
        else FieldMap.FieldSlice.MemoryMapRef
    )
    child = model_type(memory_map_ref=_name(memoryMapRef, "Name"))
    return _set_field_choice(owner, child, "memory_map_ref")


def setFieldSliceMemoryRemapRef(fieldSliceID: str, memoryRemapRef: str) -> bool:  # F.7.78.24
    """Set the normalized memoryRemapRef while preserving compatible choice wrappers.

    Section: F.7.78.24.
    """
    owner = _field_slice(fieldSliceID)
    child = MemoryRemapRef(memory_remap_ref=_name(memoryRemapRef, "Name"))
    return _set_field_choice(owner, child, "memory_remap_ref")


def setFieldSliceRange(fieldSliceID: str, range: Sequence[str]) -> bool:  # F.7.78.25
    """Set both range expression sources atomically, retaining generated metadata.

    Section: F.7.78.25.
    """
    return _set_range(_field_slice(fieldSliceID), range)


def setFieldSliceRegisterRef(fieldSliceID: str, registerRef: str) -> bool:  # F.7.78.26
    """Set a normalized register name while retaining its indices. Section: F.7.78.26."""
    owner = _field_slice(fieldSliceID)
    child = RegisterRef(register_ref=_name(registerRef, "Name"))
    return _set_field_reference(owner, "register_ref", child)


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
