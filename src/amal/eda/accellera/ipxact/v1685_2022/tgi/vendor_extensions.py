"""Vendor extensions category TGI functions (IEEE 1685-2022).

This module implements the public TGI functions for Vendor Extensions:

* BASE (F.7.85) - retrieval of the vendor extension container and its elements.
* EXTENDED (F.7.86) - addition, removal, and replacement of extension fragments.

The IP-XACT schema models vendor extensions as an optional ``vendorExtensions``
container holding an arbitrary ordered sequence of XML elements. Generated
bindings represent that content with :class:`VendorExtensions` and its
``any_element`` list, whose entries may be xsdata ``AnyElement`` values or
registered generated extension classes.

The Annex F XML-string arguments are XML document fragments containing zero or
more extension elements. Fragments are parsed completely before a model is
changed. Parsed elements are converted to xsdata ``AnyElement`` values, keeping
expanded element and attribute names, text, tail text, child order, and
attributes so the normal IP-XACT serializer can write the extension content.
An arbitrary vendor schema is not available here, so input is checked for XML
well-formedness; vendor-specific schema validation is outside this interface.

The original helper getters remain available for compatibility. They return
neutral values for unknown handles, while the Annex F mutators report unknown
handles and malformed fragments through :class:`TgiError`.

Design choices:
* BASE getters are tolerant: invalid IDs yield neutral values (``None`` or
    empty lists) rather than raising faults.
* EXTENDED mutators raise :class:`TgiError` with
    ``TgiFaultCode.INVALID_ID`` for unknown handles and
    ``TgiFaultCode.INVALID_ARGUMENT`` for malformed XML fragments.
* Added fragments are stored as lightweight XML objects. In generated 1685-2022
    bindings these are xsdata ``AnyElement`` instances, preserving XML details
    needed by the project's serializer.
"""

from collections.abc import Sequence
from typing import Any
from xml.etree import ElementTree as ET

from xsdata.formats.dataclass.models.generics import AnyElement

from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    register_parent,
    resolve_handle,
)

__all__: list[str] = [
    # BASE (F.7.85)
    "getVendorExtensions",
    "getVendorExtensionsIDs",
    "getVendorExtensionElementNames",
    "getVendorExtensionElementsRaw",
    "getVendorExtensionElementText",
    "getVendorExtensionElementAttributeNames",
    "getVendorExtensionElementAttributeValue",
    # EXTENDED (F.7.86)
    "addVendorExtensions",
    "removeVendorExtensions",
    "setVendorExtensions",
    "removeVendorExtensionsElement",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve(parentID: str) -> Any | None:
    """Resolve a handle used by the compatibility getters."""
    return resolve_handle(parentID)


def _vendor_extensions_container(obj: Any) -> Any:
    """Return an object's optional generated vendorExtensions child."""
    return getattr(obj, "vendor_extensions", None)


def _extension_entries(container: Any) -> tuple[str | None, list[Any]]:
    """Return the content list and its binding field name, if available."""
    if container is None:
        return None, []

    # ``any_element`` is the xsdata-generated 1685-2022 field. The other names
    # retain compatibility with hand-written or older test model objects.
    for name in ("any_element", "any", "vendor_extension", "items"):
        value = getattr(container, name, None)
        if isinstance(value, list):
            return name, value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return name, list(value)

    if isinstance(container, list):
        return None, container
    if isinstance(container, Sequence) and not isinstance(container, (str, bytes)):
        return None, list(container)
    return None, []


def _register_container(parent: Any, container: Any) -> str:
    """Register the vendorExtensions model child and return its handle."""
    container_handle = get_handle(container)
    register_parent(container, parent, ("vendor_extensions",), "single")
    return container_handle


def _ext_elems(parentID: str) -> list[Any]:
    """Return extension children and register their container ownership."""
    parent = _resolve(parentID)
    if parent is None:
        return []
    container = _vendor_extensions_container(parent)
    field_name, elems = _extension_entries(container)
    if container is not None and field_name is not None:
        _register_container(parent, container)
        for elem in elems:
            register_parent(elem, container, (field_name,), "list")
    return elems


def _qname(obj: Any) -> str | None:
    """Return an element's tag or xsdata wildcard QName."""
    tag = getattr(obj, "tag", None)
    if isinstance(tag, str):
        return tag
    qname = getattr(obj, "qname", None)
    return qname if isinstance(qname, str) else None


def _local_name(tag: str) -> str:
    """Return a QName's local part."""
    return tag.rsplit("}", 1)[-1]


def _attributes(obj: Any) -> dict[str, str]:
    """Return an element's attributes across XML and xsdata representations."""
    value = getattr(obj, "attrib", None)
    if not isinstance(value, dict):
        value = getattr(obj, "attributes", None)
    return value if isinstance(value, dict) else {}


def _to_any_element(elem: ET.Element) -> AnyElement:
    """Convert an ElementTree node to xsdata's namespace-aware wildcard model."""
    return AnyElement(
        qname=elem.tag,
        text=elem.text,
        tail=elem.tail,
        attributes=dict(elem.attrib),
        children=[_to_any_element(child) for child in list(elem)],
    )


def _parse_fragment(xmlFragment: str) -> list[AnyElement]:
    """Parse an XML fragment as ordered top-level wildcard elements."""
    if not isinstance(xmlFragment, str):
        raise TgiError("Vendor extension value must be an XML string", TgiFaultCode.INVALID_ARGUMENT)
    if not xmlFragment.strip():
        return []

    # A wrapper permits multiple top-level extension elements while the XML
    # parser still validates the entire supplied string before mutation.
    try:
        root = ET.fromstring(f"<tgiVendorExtensions>{xmlFragment}</tgiVendorExtensions>")
    except (ET.ParseError, ValueError, TypeError) as exc:
        raise TgiError(
            f"Malformed vendor extension XML fragment: {exc}",
            TgiFaultCode.INVALID_ARGUMENT,
        ) from exc

    if root.text and root.text.strip():
        raise TgiError(
            "Vendor extension fragments may contain XML elements only",
            TgiFaultCode.INVALID_ARGUMENT,
        )
    return [_to_any_element(child) for child in list(root)]


def _require_parent(parentID: str) -> Any:
    """Resolve a mutator's owning IP-XACT element or raise INVALID_ID."""
    parent = resolve_handle(parentID)
    if parent is None:
        raise TgiError("Invalid ID", TgiFaultCode.INVALID_ID)
    return parent


def _ensure_vendor_extensions(parent: Any) -> VendorExtensions:
    """Create and assign a generated vendorExtensions container as needed."""
    container = _vendor_extensions_container(parent)
    if container is None:
        container = VendorExtensions()
        try:
            parent.vendor_extensions = container
        except (AttributeError, TypeError) as exc:
            raise TgiError(
                "Element does not support vendor extensions",
                TgiFaultCode.INVALID_ARGUMENT,
            ) from exc
    if not hasattr(container, "any_element"):
        raise TgiError(
            "Vendor extensions container is not a 1685-2022 binding",
            TgiFaultCode.INVALID_ARGUMENT,
        )
    return container


def _store_extensions(parent: Any, container: Any, elements: list[AnyElement]) -> None:
    """Replace a container's wildcard list and register new element ownership."""
    field_name, current = _extension_entries(container)
    if field_name is None:
        raise TgiError("Vendor extensions container has no mutable element list", TgiFaultCode.INVALID_ARGUMENT)

    target = getattr(container, field_name)
    if not isinstance(target, list):
        try:
            setattr(container, field_name, list(current))
        except (AttributeError, TypeError) as exc:
            raise TgiError("Vendor extensions element list is not mutable", TgiFaultCode.INVALID_ARGUMENT) from exc

    # Invalidate old element handles and descendants before replacing the list.
    for elem in list(getattr(container, field_name)):
        elem_handle = get_handle(elem)
        register_parent(elem, container, (field_name,), "list")
        detach_child_by_handle(elem_handle)

    target = getattr(container, field_name)
    if not isinstance(target, list):
        try:
            setattr(container, field_name, [])
        except (AttributeError, TypeError) as exc:
            raise TgiError("Vendor extensions element list is not mutable", TgiFaultCode.INVALID_ARGUMENT) from exc
        target = getattr(container, field_name)

    target.extend(elements)
    _register_container(parent, container)
    for elem in elements:
        register_parent(elem, container, (field_name,), "list")


def _append_extensions(parent: Any, container: Any, elements: list[AnyElement]) -> None:
    """Append parsed elements while keeping existing child handles valid."""
    field_name, current = _extension_entries(container)
    if field_name is None:
        raise TgiError("Vendor extensions container has no mutable element list", TgiFaultCode.INVALID_ARGUMENT)

    target = getattr(container, field_name)
    if not isinstance(target, list):
        try:
            target = list(current)
            setattr(container, field_name, target)
        except (AttributeError, TypeError) as exc:
            raise TgiError("Vendor extensions element list is not mutable", TgiFaultCode.INVALID_ARGUMENT) from exc

    _register_container(parent, container)
    target.extend(elements)
    for elem in elements:
        register_parent(elem, container, (field_name,), "list")


# ---------------------------------------------------------------------------
# BASE (F.7.85)
# ---------------------------------------------------------------------------


def getVendorExtensions(vendorExtensionsContainerElementID: str) -> str | None:  # F.7.85.1
    """Return the handle of an element's vendorExtensions container.

    Args:
        vendorExtensionsContainerElementID: Handle to an element that may have
            a vendorExtensions child.

    Returns:
        The vendorExtensions container handle, or ``None`` when the handle is
        unknown or the element has no vendorExtensions child.

    Section: F.7.85.1.
    """
    parent = _resolve(vendorExtensionsContainerElementID)
    if parent is None:
        return None
    container = _vendor_extensions_container(parent)
    if container is None:
        return None
    return _register_container(parent, container)


def getVendorExtensionsIDs(parentID: str) -> list[str]:  # compatibility helper
    """Return handles for each wildcard extension element.

    Args:
        parentID: Handle to an element containing vendor extensions.

    Returns:
        Handles for extension children in document order, or an empty list for
        an unknown ID or absent container.

    Section: F.7.85 (compatibility helper; not a separate Annex F operation).
    """
    return [get_handle(e) for e in _ext_elems(parentID)]


def getVendorExtensionElementNames(parentID: str) -> list[str]:  # compatibility helper
    """Return local element names from a vendor extension list.

    Args:
        parentID: Handle to an element containing vendor extensions.

    Returns:
        Local names of recognized wildcard elements in order.

    Section: F.7.85 (compatibility helper; not a separate Annex F operation).
    """
    names: list[str] = []
    for elem in _ext_elems(parentID):
        tag = _qname(elem)
        if tag is not None:
            names.append(_local_name(tag))
    return names


def getVendorExtensionElementsRaw(parentID: str) -> list[Any]:  # compatibility helper
    """Return raw generated or wildcard extension children.

    Args:
        parentID: Handle to an element containing vendor extensions.

    Returns:
        Extension child objects in document order.

    Section: F.7.85 (compatibility helper; not a separate Annex F operation).
    """
    return list(_ext_elems(parentID))


def getVendorExtensionElementText(parentID: str, elementName: str) -> list[str]:  # compatibility helper
    """Return text values for matching extension elements.

    Args:
        parentID: Handle to an element containing vendor extensions.
        elementName: Local name of the wildcard elements to inspect.

    Returns:
        Text values for matching elements that have text.

    Section: F.7.85 (compatibility helper; not a separate Annex F operation).
    """
    texts: list[str] = []
    for elem in _ext_elems(parentID):
        tag = _qname(elem)
        if tag is not None and _local_name(tag) == elementName:
            text_val = getattr(elem, "text", None)
            if isinstance(text_val, str):
                texts.append(text_val)
    return texts


def getVendorExtensionElementAttributeNames(parentID: str, elementName: str) -> list[str]:  # compatibility helper
    """Return attribute names for matching extension elements.

    Args:
        parentID: Handle to an element containing vendor extensions.
        elementName: Local name of the wildcard elements to inspect.

    Returns:
        Attribute names from matching elements in element order.

    Section: F.7.85 (compatibility helper; not a separate Annex F operation).
    """
    names: list[str] = []
    for elem in _ext_elems(parentID):
        tag = _qname(elem)
        if tag is not None and _local_name(tag) == elementName:
            names.extend(_attributes(elem).keys())
    return names


def getVendorExtensionElementAttributeValue(
    parentID: str,
    elementName: str,
    attributeName: str,
) -> list[str]:  # compatibility helper
    """Return values of an attribute on matching extension elements.

    Args:
        parentID: Handle to an element containing vendor extensions.
        elementName: Local name of the wildcard elements to inspect.
        attributeName: Exact attribute QName whose value is requested.

    Returns:
        Attribute values for matching elements that contain the attribute.

    Section: Compatibility helper for the Vendor extensions BASE category.
    """
    values: list[str] = []
    for elem in _ext_elems(parentID):
        tag = _qname(elem)
        attrib = _attributes(elem)
        if tag is not None and _local_name(tag) == elementName and attributeName in attrib:
            val = attrib[attributeName]
            if isinstance(val, str):
                values.append(val)
    return values


# ---------------------------------------------------------------------------
# EXTENDED (F.7.86)
# ---------------------------------------------------------------------------


def addVendorExtensions(
    vendorExtensionsContainerElementID: str,
    vendorExtensions: str,
) -> bool:  # F.7.86.1
    """Append XML fragment elements to an element's vendorExtensions list.

    Args:
        vendorExtensionsContainerElementID: Handle to the owning IP-XACT
            element.
        vendorExtensions: XML fragment containing zero or more extension
            elements.

    Returns:
        ``True`` when the extension elements were appended.

    Raises:
        TgiError: With ``INVALID_ID`` for an unknown owner, or
            ``INVALID_ARGUMENT`` when the fragment is malformed or the owner
            cannot hold a generated vendorExtensions container.

    Section: F.7.86.1.
    """
    parent = _require_parent(vendorExtensionsContainerElementID)
    elements = _parse_fragment(vendorExtensions)
    if not elements:
        return True
    container = _ensure_vendor_extensions(parent)
    _append_extensions(parent, container, elements)
    return True


def removeVendorExtensions(vendorExtensionsContainerElementID: str) -> bool:  # F.7.86.2
    """Remove an element's vendorExtensions child and invalidate its subtree.

    Args:
        vendorExtensionsContainerElementID: Handle to the owning IP-XACT
            element.

    Returns:
        ``True`` when the optional child was removed or was already absent.

    Raises:
        TgiError: With ``INVALID_ID`` when the owner handle is unknown.

    Section: F.7.86.2.
    """
    parent = _require_parent(vendorExtensionsContainerElementID)
    container = _vendor_extensions_container(parent)
    if container is None:
        return True
    container_handle = _register_container(parent, container)
    if not detach_child_by_handle(container_handle):
        try:
            parent.vendor_extensions = None
        except (AttributeError, TypeError) as exc:
            raise TgiError("Vendor extensions container cannot be removed", TgiFaultCode.INVALID_ARGUMENT) from exc
    return True


def setVendorExtensions(
    vendorExtensionsContainerElementID: str,
    vendorExtensions: str,
) -> bool:  # F.7.86.3
    """Replace an element's vendorExtensions content from an XML fragment.

    Args:
        vendorExtensionsContainerElementID: Handle to the owning IP-XACT
            element.
        vendorExtensions: XML fragment containing the complete replacement
            sequence of extension elements. An empty string leaves an empty
            vendorExtensions container.

    Returns:
        ``True`` when the replacement succeeded.

    Raises:
        TgiError: With ``INVALID_ID`` for an unknown owner, or
            ``INVALID_ARGUMENT`` when the fragment is malformed or the owner
            cannot hold a generated vendorExtensions container.

    Section: F.7.86.3.
    """
    parent = _require_parent(vendorExtensionsContainerElementID)
    elements = _parse_fragment(vendorExtensions)
    container = _ensure_vendor_extensions(parent)
    _store_extensions(parent, container, elements)
    return True


def removeVendorExtensionsElement(extensionID: str) -> bool:  # compatibility helper
    """Remove one extension element by its child handle.

    Args:
        extensionID: Handle to a wildcard extension element.

    Returns:
        ``True`` when the element was detached or was already unowned.

    Raises:
        TgiError: With ``INVALID_ID`` when the handle is unknown.

    Section: F.7.86 (compatibility helper; not a separate Annex F operation).
    """
    if resolve_handle(extensionID) is None:
        raise TgiError("Invalid ID", TgiFaultCode.INVALID_ID)
    detach_child_by_handle(extensionID)
    return True


## End of file
