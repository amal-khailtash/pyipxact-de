"""Access handle category TGI functions.

Implements BASE (F.7.7) and EXTENDED (F.7.8) access handle functions covering
enumeration of accessHandle elements, indices, slices and viewRef children plus
add/remove/set operations. Access handles appear underneath several IP-XACT
objects (registers, fields, banks, etc.) inside an optional ``accessHandles``
container; this module centralizes traversal and mutation logic.
"""

from collections.abc import Iterable, Sequence
from typing import Any, Protocol, get_args, get_type_hints

from org.accellera.ipxact.v1685_2022 import (
    PortAccessHandle,
    SimpleAccessHandle,
    SlicedAccessHandle,
)

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    resolve_handle,
)

AccessHandleType = SimpleAccessHandle | SlicedAccessHandle | PortAccessHandle


class _AccessHandlesContainer(Protocol):
    @property
    def access_handle(self) -> Sequence[AccessHandleType]: ...

__all__ = [
    # BASE (F.7.7)
    "getAccessHandleForce",
    "getAccessHandleIDs",
    "getAccessHandleIndicesIDs",
    "getAccessHandlePathSegmentIDs",
    "getAccessHandleSliceIDs",
    "getAccessHandleViewRefIDs",
    # EXTENDED (F.7.8)
    "addAccessHandle",
    "addAccessHandleIndex",
    "addAccessHandlePathSegment",
    "addAccessHandleSlice",
    "addAccessHandleViewRef",
    "removeAccessHandle",
    "removeAccessHandleIndex",
    "removeAccessHandlePathSegment",
    "removeAccessHandleSlice",
    "removeAccessHandleViewRef",
    "setAccessHandleForce",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _resolve(accessHandleID: str) -> AccessHandleType | None:
    """Resolve a handle to an accessHandle element.

    Args:
        accessHandleID: Handle referencing a simple/sliced/port accessHandle.

    Returns:
        Resolved object or ``None`` if the handle does not reference one of
        the supported accessHandle types.
    """
    obj = resolve_handle(accessHandleID)
    if isinstance(obj, SimpleAccessHandle | SlicedAccessHandle | PortAccessHandle):
        return obj
    return None


def _owned_ids(owner: Any, attr: str) -> list[str]:
    """Register loaded child ownership before returning handles."""
    children = getattr(owner, attr)
    for child in children:
        register_parent(child, owner, (attr,), "list")
    return [get_handle(child) for child in children]


def _ids_from(items: Iterable[Any]) -> list[str]:
    """Return handles for iterable items."""
    return [get_handle(i) for i in items]


def _ensure_port(accessHandleID: str) -> PortAccessHandle:
    """Return a PortAccessHandle or raise.

    Raises:
        TgiError: If the handle is invalid or not a portAccessHandle.
    """
    ah = _resolve(accessHandleID)
    if not isinstance(ah, PortAccessHandle):
        raise TgiError("Access handle is not portAccessHandle", TgiFaultCode.INVALID_ARGUMENT)
    return ah


def _ensure_sliced(accessHandleID: str) -> SlicedAccessHandle:
    """Return a SlicedAccessHandle or raise."""
    ah = _resolve(accessHandleID)
    if not isinstance(ah, SlicedAccessHandle):
        raise TgiError("Access handle is not slicedAccessHandle", TgiFaultCode.INVALID_ARGUMENT)
    return ah


def _ensure_simple(accessHandleID: str) -> SimpleAccessHandle:
    """Return a SimpleAccessHandle or raise."""
    ah = _resolve(accessHandleID)
    if not isinstance(ah, SimpleAccessHandle):
        raise TgiError("Access handle is not simpleAccessHandle", TgiFaultCode.INVALID_ARGUMENT)
    return ah


def _ensure_access_handles_container(parentID: str) -> _AccessHandlesContainer:
    """Return/create an ``accessHandles`` container for a parent element.

    The parent element types that may own accessHandles share the attribute
    name ``access_handles`` (snake_case generated from schema). We lazily
    allocate the container list wrapper when first needed.
    """
    parent = resolve_handle(parentID)
    if parent is None:
        raise TgiError("Invalid parent handle", TgiFaultCode.INVALID_ID)
    annotation = get_type_hints(type(parent)).get("access_handles")
    classes = [cls for cls in get_args(annotation) if cls is not type(None)]
    if not classes:
        raise TgiError("Parent does not support accessHandles", TgiFaultCode.INVALID_ARGUMENT)
    if parent.access_handles is None:
        parent.access_handles = classes[0]()
    register_parent(parent.access_handles, parent, ("access_handles",), "single")
    return parent.access_handles


def _append_and_register(container: object, element: object, list_attr: tuple[str, ...]) -> None:
    """Append element to container list attribute and register parent."""
    getattr(container, list_attr[-1]).append(element)
    register_parent(element, container, list_attr, "list")


# ---------------------------------------------------------------------------
# BASE (F.7.7)
# ---------------------------------------------------------------------------


def getAccessHandleForce(accessHandleID: str) -> bool | None:
    """Return the ``force`` attribute of a port/sliced handle.

    Section: F.7.7.1.

    Args:
        accessHandleID: Handle to the accessHandle element.

    Returns:
        Defined force value; simple access handles return None.
    """
    ah = _resolve(accessHandleID)
    if ah is None:
        raise TgiError("Invalid accessHandle handle", TgiFaultCode.INVALID_ID)
    if isinstance(ah, SimpleAccessHandle):
        return None
    return getattr(ah, "force", None)


def getAccessHandleIDs(parentID: str) -> list[str]:
    """Return handles of accessHandle children of a parent.

    Section: F.7.7.2.

    Args:
        parentID: Handle to the parent element.

    Returns:
        Ordered child handles; an absent collection returns an empty list.
    """
    parent = resolve_handle(parentID)
    if parent is None:
        raise TgiError("Invalid parent handle", TgiFaultCode.INVALID_ID)
    container = getattr(parent, "access_handles", None)
    if container is None:
        return []
    register_parent(container, parent, ("access_handles",), "single")
    return _owned_ids(container, "access_handle")


def getAccessHandleIndicesIDs(accessHandleID: str) -> list[str]:
    """Return index element handles of a portAccessHandle.

    Section: F.7.7.3.

    Args:
        accessHandleID: Handle to the accessHandle element.

    Returns:
        Ordered child handles; an absent collection returns an empty list.
    """
    ah = _resolve(accessHandleID)
    if ah is None:
        raise TgiError("Invalid accessHandle handle", TgiFaultCode.INVALID_ID)
    if not isinstance(ah, PortAccessHandle):
        return []
    if ah.indices is None:
        return []
    register_parent(ah.indices, ah, ("indices",), "single")
    return _owned_ids(ah.indices, "index")


def getAccessHandlePathSegmentIDs(accessHandleID: str) -> list[str]:
    """Return pathSegment handles of a simpleAccessHandle.

    Section: F.7.7.4.

    Args:
        accessHandleID: Handle to the accessHandle element.

    Returns:
        Ordered child handles; an absent collection returns an empty list.
    """
    ah = _resolve(accessHandleID)
    if ah is None:
        raise TgiError("Invalid accessHandle handle", TgiFaultCode.INVALID_ID)
    if not isinstance(ah, SimpleAccessHandle):
        return []
    ps = ah.path_segments
    if ps is None:
        return []
    register_parent(ps, ah, ("path_segments",), "single")
    return _owned_ids(ps, "path_segment")


def getAccessHandleSliceIDs(accessHandleID: str) -> list[str]:
    """Return slice handles of a portAccessHandle or slicedAccessHandle.

    Section: F.7.7.5.

    Args:
        accessHandleID: Handle to the accessHandle element.

    Returns:
        Ordered child handles; an absent collection returns an empty list.
    """
    ah = _resolve(accessHandleID)
    if ah is None:
        raise TgiError("Invalid accessHandle handle", TgiFaultCode.INVALID_ID)
    if isinstance(ah, PortAccessHandle | SlicedAccessHandle):
        slices = getattr(ah, "slices", None)
        if slices is None:
            return []
        register_parent(slices, ah, ("slices",), "single")
        return _owned_ids(slices, "slice")
    return []


def getAccessHandleViewRefIDs(accessHandleID: str) -> list[str]:
    """Return viewRef handles for any accessHandle variant.

    Section: F.7.7.6.

    Args:
        accessHandleID: Handle to the accessHandle element.

    Returns:
        Ordered child handles; an absent collection returns an empty list.
    """
    ah = _resolve(accessHandleID)
    if ah is None:
        raise TgiError("Invalid accessHandle handle", TgiFaultCode.INVALID_ID)
    return _owned_ids(ah, "view_ref")


# ---------------------------------------------------------------------------
# EXTENDED (F.7.8)
# ---------------------------------------------------------------------------


def addAccessHandle(elementID: str, pathSegment: str) -> str:
    """Add the schema-selected access handle with an initial HDL path segment.

    Section: F.7.8.1.

    Args:
        elementID: Handle to the element element.
        pathSegment: Initial HDL path segment text.

    Returns:
        Handle to the added element.
    """
    if not isinstance(pathSegment, str) or not pathSegment:
        raise TgiError("pathSegment must be a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    container = _ensure_access_handles_container(elementID)
    cls = get_args(get_type_hints(type(container))["access_handle"])[0]
    from org.accellera.ipxact.v1685_2022 import (
        PathSegmentType,
        PortPathSegmentType,
        PortSlicesType,
        PortSliceType,
        SlicesType,
        SliceType,
    )

    if cls is SimpleAccessHandle:
        ah = cls(path_segments=cls.PathSegments(path_segment=[PathSegmentType(value=pathSegment)]))
    elif cls is SlicedAccessHandle:
        sl = SliceType(path_segments=SliceType.PathSegments(path_segment=[PathSegmentType(value=pathSegment)]))
        ah = cls(slices=SlicesType(slice=[sl]))
    elif cls is PortAccessHandle:
        sl = PortSliceType(
            path_segments=PortSliceType.PathSegments(path_segment=[PortPathSegmentType(value=pathSegment)])
        )
        ah = cls(slices=PortSlicesType(slice=[sl]))
    else:
        raise TgiError("Unsupported accessHandle model", TgiFaultCode.INVALID_ARGUMENT)
    _append_and_register(container, ah, ("access_handle",))
    return get_handle(ah)


def addAccessHandleIndex(accessHandleID: str, value: str) -> str:
    """Add an ``index`` element to a portAccessHandle.

    Section: F.7.8.2.

    Args:
        accessHandleID: Handle to the accessHandle element.
        value: Value to assign; force requires a Boolean.

    Returns:
        Handle to the added element.
    """
    if not isinstance(value, str) or not value:
        raise TgiError("Value must be a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    ah = _ensure_port(accessHandleID)
    from org.accellera.ipxact.v1685_2022.port_access_handle import PortAccessHandle as PAH

    if ah.indices is None:
        ah.indices = PAH.Indices(index=[])  # type: ignore[arg-type]
    register_parent(ah.indices, ah, ("indices",), "single")
    idx = PAH.Indices.Index(value=value)  # type: ignore[arg-type]
    ah.indices.index.append(idx)  # type: ignore[attr-defined]
    register_parent(idx, ah.indices, ("index",), "list")
    return get_handle(idx)


def addAccessHandlePathSegment(accessHandleID: str, value: str) -> str:
    """Add a pathSegment to a simpleAccessHandle.

    Section: F.7.8.3.

    Args:
        accessHandleID: Handle to the accessHandle element.
        value: Value to assign; force requires a Boolean.

    Returns:
        Handle to the added element.
    """
    if not isinstance(value, str) or not value:
        raise TgiError("Value must be a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    ah = _ensure_simple(accessHandleID)
    from org.accellera.ipxact.v1685_2022.path_segment_type import PathSegmentType
    from org.accellera.ipxact.v1685_2022.simple_access_handle import (
        SimpleAccessHandle as SAH,
    )

    if ah.path_segments is None:
        ah.path_segments = SAH.PathSegments(path_segment=[])  # type: ignore[arg-type]
    register_parent(ah.path_segments, ah, ("path_segments",), "single")
    seg = PathSegmentType(value=value)  # type: ignore[arg-type]
    ah.path_segments.path_segment.append(seg)  # type: ignore[attr-defined]
    register_parent(seg, ah.path_segments, ("path_segment",), "list")
    return get_handle(seg)


def addAccessHandleSlice(accessHandleID: str, pathSegment: str) -> str:
    """Add a slice with an initial HDL path segment to a sliced or port access handle.

    Section: F.7.8.4.

    Args:
        accessHandleID: Handle to the accessHandle element.
        pathSegment: Initial HDL path segment text.

    Returns:
        Handle to the added element.
    """
    ah = _resolve(accessHandleID)
    if not isinstance(pathSegment, str) or not pathSegment:
        raise TgiError("pathSegment must be a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    from org.accellera.ipxact.v1685_2022 import PathSegmentType, PortPathSegmentType, PortSliceType, SliceType

    if isinstance(ah, PortAccessHandle):
        sl = PortSliceType(
            path_segments=PortSliceType.PathSegments(path_segment=[PortPathSegmentType(value=pathSegment)])
        )
    elif isinstance(ah, SlicedAccessHandle):
        sl = SliceType(path_segments=SliceType.PathSegments(path_segment=[PathSegmentType(value=pathSegment)]))
    else:
        raise TgiError("Access handle does not support slices", TgiFaultCode.INVALID_ARGUMENT)
    register_parent(ah.slices, ah, ("slices",), "single")
    _append_and_register(ah.slices, sl, ("slice",))
    return get_handle(sl)


def addAccessHandleViewRef(accessHandleID: str, viewName: str) -> str:
    """Add a viewRef child to any accessHandle variant.

    Section: F.7.8.5.

    Args:
        accessHandleID: Handle to the accessHandle element.
        viewName: Name of the referenced view.

    Returns:
        Handle to the added element.
    """
    if not isinstance(viewName, str) or not viewName:
        raise TgiError("Value must be a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    ah = _resolve(accessHandleID)
    if ah is None:
        raise TgiError("Invalid accessHandle handle", TgiFaultCode.INVALID_ID)
    # Each variant defines an inner ViewRef dataclass named ViewRef.
    view_ref_cls = type(ah).ViewRef  # type: ignore[attr-defined]
    vr = view_ref_cls(value=viewName)  # type: ignore[arg-type]
    ah.view_ref.append(vr)  # type: ignore[attr-defined]
    register_parent(vr, ah, ("view_ref",), "list")
    return get_handle(vr)


def removeAccessHandle(accessHandleID: str) -> bool:
    """Remove an accessHandle element.

    Section: F.7.8.6.

    Args:
        accessHandleID: Handle to the accessHandle element.

    Returns:
        True when removal or assignment succeeds; False when inapplicable or absent.
    """
    if _resolve(accessHandleID) is None:
        return False
    return detach_child_by_handle(accessHandleID)


def removeAccessHandleIndex(indexID: str) -> bool:
    """Remove an index element.

    Section: F.7.8.7.

    Args:
        indexID: Handle to the index element.

    Returns:
        True when removal or assignment succeeds; False when inapplicable or absent.
    """
    obj = resolve_handle(indexID)
    info = get_parent_info(indexID)
    if obj is None or info is None or info.path[-1:] != ("index",):
        return False
    return detach_child_by_handle(indexID)


def removeAccessHandlePathSegment(pathSegmentID: str) -> bool:
    """Remove a pathSegment element.

    Section: F.7.8.8.

    Args:
        pathSegmentID: Handle to the pathSegment element.

    Returns:
        True when removal or assignment succeeds; False when inapplicable or absent.
    """
    obj = resolve_handle(pathSegmentID)
    info = get_parent_info(pathSegmentID)
    if obj is None or info is None or info.path[-1:] != ("path_segment",):
        return False
    return detach_child_by_handle(pathSegmentID)


def removeAccessHandleSlice(sliceID: str) -> bool:
    """Remove a slice element (port/sliced variants).

    Section: F.7.8.9.

    Args:
        sliceID: Handle to the slice element.

    Returns:
        True when removal or assignment succeeds; False when inapplicable or absent.
    """
    obj = resolve_handle(sliceID)
    info = get_parent_info(sliceID)
    if obj is None or info is None or info.path[-1:] != ("slice",):
        return False
    return detach_child_by_handle(sliceID)


def removeAccessHandleViewRef(viewRefID: str) -> bool:
    """Remove a viewRef element.

    Section: F.7.8.10.

    Args:
        viewRefID: Handle to the viewRef element.

    Returns:
        True when removal or assignment succeeds; False when inapplicable or absent.
    """
    obj = resolve_handle(viewRefID)
    info = get_parent_info(viewRefID)
    if obj is None or info is None or info.path[-1:] != ("view_ref",):
        return False
    return detach_child_by_handle(viewRefID)


def setAccessHandleForce(accessHandleID: str, value: bool) -> bool:
    """Set the Boolean force attribute of a sliced or port access handle.

    Section: F.7.8.11.

    Args:
        accessHandleID: Handle to the accessHandle element.
        value: Value to assign; force requires a Boolean.

    Returns:
        True when removal or assignment succeeds; False when inapplicable or absent.
    """
    ah = _resolve(accessHandleID)
    if type(value) is not bool:
        raise TgiError("force must be Boolean", TgiFaultCode.INVALID_ARGUMENT)
    if isinstance(ah, PortAccessHandle | SlicedAccessHandle):
        ah.force = value
        return True
    return False
