"""Clearbox category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.27) and EXTENDED (F.7.28) Clearbox functions.

Provides traversal and manipulation utilities for clearbox elements, clearboxElementRef
and clearboxElementRefLocation structures. Functions raise :class:`TgiError` with
``TgiFaultCode.INVALID_ID`` when a supplied handle does not reference the expected
schema object.
"""

from org.accellera.ipxact.v1685_2022 import (
    ClearboxElementRefType,
    ClearboxElementType,
    PathSegmentType,
    SlicesType,
    SliceType,
)

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    register_parent,
    resolve_handle,
)

__all__ = [
    # BASE (F.7.27)
    "getClearboxElementClearboxType",
    "getClearboxElementDriveable",
    "getClearboxElementRefByID",
    "getClearboxElementRefLocationIDs",
    # EXTENDED (F.7.28)
    "addClearboxElementRefLocation",
    "addLocationSlice",
    "removeClearboxElementDriveable",
    "removeClearboxElementRefLocation",
    "setClearboxElementClearboxType",
    "setClearboxElementDriveable",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------

def _new_location(value: str) -> SlicesType:
    """Build a required location/slice/pathSegments chain from source text."""
    if not isinstance(value, str):
        raise TgiError("Expected path segment source text", TgiFaultCode.INVALID_ARGUMENT)
    return SlicesType(slice=[_new_slice(value)])


def _new_slice(value: str) -> SliceType:
    """Build a generated slice without evaluating its path expression."""
    if not isinstance(value, str):
        raise TgiError("Expected path segment source text", TgiFaultCode.INVALID_ARGUMENT)
    return SliceType(path_segments=SliceType.PathSegments(path_segment=[PathSegmentType(value=value)]))


def _resolve_clearbox_element(elementID: str) -> ClearboxElementType | None:
    obj = resolve_handle(elementID)
    return obj if isinstance(obj, ClearboxElementType) else None


def _resolve_clearbox_element_ref(refID: str) -> ClearboxElementRefType | None:
    obj = resolve_handle(refID)
    return obj if isinstance(obj, ClearboxElementRefType) else None


def _resolve_location(locationID: str):  # return location or None
    obj = resolve_handle(locationID)
    # Location is an inner class inside clearboxElementRefLocation? We treat generically.
    return obj


def _resolve_ref_location(refLocationID: str):  # generic resolution
    return resolve_handle(refLocationID)


# ---------------------------------------------------------------------------
# BASE (F.7.27)
# ---------------------------------------------------------------------------

def getClearboxElementClearboxType(clearboxElementID: str) -> str | None:
    """Return the ``clearboxType`` value for a clearboxElement.

    Section: F.7.27.1

    Args:
        clearboxElementID: Handle to a clearboxElement element.
    Returns:
        The clearboxType enumeration value as string, or None if not set.
    Raises:
        TgiError: If the handle is invalid.
    """
    el = _resolve_clearbox_element(clearboxElementID)
    if el is None:
        raise TgiError("Invalid clearboxElement handle", TgiFaultCode.INVALID_ID)
    cb = getattr(el, "clearbox_type", None)
    if cb is None:
        return None
    # SimpleClearboxType enum => return its value
    return getattr(cb, "value", cb)


def getClearboxElementDriveable(clearboxElementID: str) -> bool | None:
    """Return the ``driveable`` value for a clearboxElement.

    Section: F.7.27.2

    Args:
        clearboxElementID: Handle to a clearboxElement element.
    Returns:
        Boolean driveable value or None if not present.
    Raises:
        TgiError: If the handle is invalid.
    """
    el = _resolve_clearbox_element(clearboxElementID)
    if el is None:
        raise TgiError("Invalid clearboxElement handle", TgiFaultCode.INVALID_ID)
    return getattr(el, "driveable", None)


def getClearboxElementRefByID(clearboxElementRefID: str) -> str | None:
    """Return handle to the clearboxElement referenced by a clearboxElementRef.

    Section: F.7.27.3

    Args:
        clearboxElementRefID: Handle to a clearboxElementRef element.
    Returns:
        Handle to the referenced clearboxElement.
    Raises:
        TgiError: If the ref handle is invalid, it has no component owner, or
            its name does not resolve to exactly one clearboxElement in the
            owning component.
    """
    ref = _resolve_clearbox_element_ref(clearboxElementRefID)
    if ref is None:
        raise TgiError("Invalid clearboxElementRef handle", TgiFaultCode.INVALID_ID)
    from org.accellera.ipxact.v1685_2022 import ComponentInstantiationType, ComponentType

    from .core import get_parent_info, registry

    ref_info = get_parent_info(clearboxElementRefID)
    if ref_info is None or ref_info.path != ("clearbox_element_refs", "clearbox_element_ref"):
        # Registered roots provide enough information to recover parent links
        # when callers obtained the ref handle directly from a parsed model.
        for root_id in registry.iter_by_predicate(lambda root: isinstance(root, ComponentType)):
            root = resolve_handle(root_id)
            model = root.model
            instantiations = model.instantiations if model is not None else None
            instances = (
                instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation
                if instantiations is not None else []
            )
            for inst in instances:
                if not isinstance(inst, ComponentInstantiationType):
                    continue
                refs = inst.clearbox_element_refs
                if refs is not None and any(candidate is ref for candidate in refs.clearbox_element_ref):
                    register_parent(inst, root, (
                        "model", "instantiations",
                        "component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
                    ), "list")
                    register_parent(ref, inst, ("clearbox_element_refs", "clearbox_element_ref"), "list")
                    ref_info = get_parent_info(clearboxElementRefID)
                    break
            if ref_info is not None:
                break
    if (ref_info is None or ref_info.path != ("clearbox_element_refs", "clearbox_element_ref")
            or ref_info.container != "list"):
        raise TgiError("clearboxElementRef has no component instantiation owner", TgiFaultCode.INVALID_ID)

    instantiation = resolve_handle(ref_info.parent_handle)
    if not isinstance(instantiation, ComponentInstantiationType):
        raise TgiError("clearboxElementRef has no component instantiation owner", TgiFaultCode.INVALID_ID)
    inst_info = get_parent_info(ref_info.parent_handle)
    if (inst_info is None or inst_info.path != (
            "model", "instantiations",
            "component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
        ) or inst_info.container != "list"):
        raise TgiError("componentInstantiation has no component owner", TgiFaultCode.INVALID_ID)
    component = resolve_handle(inst_info.parent_handle)
    if not isinstance(component, ComponentType):
        raise TgiError("componentInstantiation has no component owner", TgiFaultCode.INVALID_ID)

    elements = component.clearbox_elements
    candidates = elements.clearbox_element if elements is not None else []
    matches = [candidate for candidate in candidates if candidate.name == ref.name]
    if len(matches) != 1:
        raise TgiError("clearboxElement reference is missing or ambiguous", TgiFaultCode.NOT_FOUND)
    target = matches[0]
    register_parent(target, component, ("clearbox_elements", "clearbox_element"), "list")
    return get_handle(target)


def getClearboxElementRefLocationIDs(clearboxElementRefID: str) -> list[str]:
    """Return handles to all clearboxElementRefLocation elements.

    Section: F.7.27.4

    Args:
        clearboxElementRefID: Handle to a clearboxElementRef element.
    Returns:
        List of handles for each clearboxElementRefLocation.
    Raises:
        TgiError: If the ref handle is invalid.
    """
    ref = _resolve_clearbox_element_ref(clearboxElementRefID)
    if ref is None:
        raise TgiError("Invalid clearboxElementRef handle", TgiFaultCode.INVALID_ID)
    for loc in ref.location:
        register_parent(loc, ref, ("location",), "list")
    return [get_handle(loc) for loc in ref.location]


def addClearboxElementRefLocation(clearboxElementRefID: str, value: str) -> str:
    """Add a ``clearboxElementRefLocation`` to a clearboxElementRef.

    Section: F.7.28.1

    Args:
        clearboxElementRefID: Handle to a clearboxElementRef element.
        value: Path segment value.
    Returns:
        Handle of the newly added clearboxElementRefLocation.
    Raises:
        TgiError: If the ref handle is invalid.
    """
    ref = _resolve_clearbox_element_ref(clearboxElementRefID)
    if ref is None:
        raise TgiError("Invalid clearboxElementRef handle", TgiFaultCode.INVALID_ID)
    loc = _new_location(value)
    ref.location.append(loc)
    register_parent(loc, ref, ("location",), "list")
    return get_handle(loc)


def addLocationSlice(locationID: str, value: str) -> str:
    """Add a slice to a Location element.

    Section: F.7.28.2

    Args:
        locationID: Handle to a location element.
        value: Slice value (path segment).
    Returns:
        Handle to the new slice element.
    Raises:
        TgiError: If the location handle is invalid.
    """
    loc = resolve_handle(locationID)
    if not isinstance(loc, SlicesType):
        raise TgiError("Invalid location handle", TgiFaultCode.INVALID_ID)
    sl = _new_slice(value)
    loc.slice.append(sl)
    register_parent(sl, loc, ("slice",), "list")
    return get_handle(sl)


def removeClearboxElementDriveable(clearboxElementID: str) -> bool:
    """Remove the ``driveable`` element from a clearboxElement.

    Section: F.7.28.3

    Args:
        clearboxElementID: Handle to a clearboxElement element.
    Returns:
        True if cleared, False if absent; invalid handles raise INVALID_ID.
    """
    el = _resolve_clearbox_element(clearboxElementID)
    if el is None:
        raise TgiError("Invalid clearboxElement handle", TgiFaultCode.INVALID_ID)
    if el.driveable is None:
        return False
    el.driveable = None
    return True


def removeClearboxElementRefLocation(clearboxElementRefLocationID: str) -> bool:
    """Remove a clearboxElementRefLocation element.

    Section: F.7.28.4

    Args:
        clearboxElementRefLocationID: Handle to a clearboxElementRefLocation element.
    Returns:
        True if removed, False otherwise.
    """
    return detach_child_by_handle(clearboxElementRefLocationID)


def setClearboxElementClearboxType(clearboxID: str, clearboxType: str) -> bool:
    """Set the generated signal/pin/interface enum atomically.

    Section: F.7.28.5

    Args:
        clearboxID: Handle to a clearboxElement element.
        clearboxType: New clearbox type string.
    Returns:
        True if set, False if not found.
    Raises:
        TgiError: If the handle is invalid.
    """
    el = _resolve_clearbox_element(clearboxID)
    if el is None:
        raise TgiError("Invalid clearboxElement handle", TgiFaultCode.INVALID_ID)
    from org.accellera.ipxact.v1685_2022 import SimpleClearboxType

    if not isinstance(clearboxType, str):
        raise TgiError("Expected a clearbox type string", TgiFaultCode.INVALID_ARGUMENT)
    try:
        value = SimpleClearboxType(clearboxType)
    except ValueError as exc:
        raise TgiError("Invalid clearbox type", TgiFaultCode.INVALID_ARGUMENT) from exc
    el.clearbox_type = value
    return True


def setClearboxElementDriveable(clearboxElementID: str, value: bool) -> bool:
    """Set Boolean driveable state atomically, preserving other fields.

    Section: F.7.28.6

    Args:
        clearboxElementID: Handle to a clearboxElement element.
        value: Boolean driveable state.
    Returns:
        True if set, False if not found.
    Raises:
        TgiError: If the handle is invalid.
    """
    el = _resolve_clearbox_element(clearboxElementID)
    if el is None:
        raise TgiError("Invalid clearboxElement handle", TgiFaultCode.INVALID_ID)
    if not isinstance(value, bool):
        raise TgiError("Expected Boolean driveable state", TgiFaultCode.INVALID_ARGUMENT)
    el.driveable = value
    return True
