"""Name group category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.63) and EXTENDED (F.7.64) functions operating on the
standard IP-XACT NameGroup (``name``, ``displayName``, ``description``,
``shortDescription``) which is reused across many schema elements. Handles
refer to any object possessing the corresponding attributes.

Optional getters return None when content is absent. Invalid or unsupported
handles fault. Description and displayName setters require existing content,
as specified by Annex F; name and shortDescription setters can create content.
Short descriptions retain their unresolved SystemVerilog expression text.
Generated text wrappers and their metadata survive edits, and removed wrappers
and descendants lose their handles. Removing a required name intentionally
leaves an incomplete model until a subsequent setName restores it. Registered
documents retain a required name; renames update their VLNV index atomically.
"""

import re
from dataclasses import is_dataclass
from functools import lru_cache
from typing import Any

from lxml import etree

from org.accellera.ipxact.v1685_2022 import Description, DisplayName, ShortDescription

from .core import _HANDLE_MANAGER, TgiError, TgiFaultCode, get_handle, register_parent, registry, resolve_handle

__all__ = [
    # BASE (F.7.63)
    "getDescription",
    "getDisplayName",
    "getName",
    "getShortDescription",
    # EXTENDED (F.7.64)
    "removeDescription",
    "removeDisplayName",
    "removeName",
    "removeShortDescription",
    "setDescription",
    "setDisplayName",
    "setName",
    "setShortDescription",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve(elementID: str, attr: str) -> tuple[Any, str]:
    """Resolve only an existing supported text field; never synthesize attributes."""
    obj = resolve_handle(elementID) if isinstance(elementID, str) else None
    variants = {"display_name": "displayName", "short_description": "shortDescription"}
    if obj is not None:
        for field in (attr, variants.get(attr, attr)):
            if hasattr(obj, field):
                return obj, field
    raise TgiError("Invalid name-group element handle", TgiFaultCode.INVALID_ID)


def _get_text(elementID: str, attr: str) -> str | None:
    obj, field = _resolve(elementID, attr)
    value = getattr(obj, field)
    if value is None:
        return None
    if hasattr(value, "value"):
        register_parent(value, obj, (field,), "single")
        value = value.value
    if not isinstance(value, str):
        raise TgiError("Invalid name-group text", TgiFaultCode.INVALID_ARGUMENT)
    return value


@lru_cache(maxsize=3)
def _name_schema(kind: str) -> etree.XMLSchema:
    """Validate the lexical rules of the five commonStructures name groups."""
    declaration = f'<xs:element name="name" type="xs:{kind}"/>'
    if kind == "portName":
        declaration = (
            '<xs:element name="name"><xs:simpleType><xs:restriction base="xs:string">'
            '<xs:whiteSpace value="collapse"/><xs:pattern value="\\i[\\p{L}\\p{N}\\.\\-:_]*"/>'
            "</xs:restriction></xs:simpleType></xs:element>"
        )
    return etree.XMLSchema(
        etree.fromstring(
            ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">' + declaration + "</xs:schema>").encode()
        )
    )


def _name_text(obj: Any, value: str) -> str:
    """Apply the target name group's type, without normalizing xs:string names."""
    if not type(obj).__module__.startswith("org.accellera.ipxact.v1685_2022"):
        return value
    classes = {base.__name__ for base in type(obj).__mro__}
    if classes & {"ParameterType", "ModuleParameterType", "NameValuePairType", "TypeParameter"}:
        return value
    if classes & {"PortType", "AbstractorPortType", "SubPortType", "AbstractorSubPortType", "AdHocConnection"}:
        kind = "portName"
    elif (
        all(hasattr(obj, field) for field in ("vendor", "library", "version"))
        or classes
        & {
            "LibraryRefType",
            "DesignInstantiationType",
            "DesignConfigurationInstantiationType",
            "ComponentInstantiationType",
        }
        or (type(obj).__qualname__ in {"ModelType.Views.View", "AbstractorModelType.Views.View"})
    ):
        kind = "NMTOKEN"
    else:
        kind = "Name"
    value = re.sub(r"[\t\n\r ]+", " ", value).strip(" ")
    element = etree.Element("name")
    element.text = value
    if not _name_schema(kind).validate(element):
        raise TgiError(f"Invalid {kind} name", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _set_text(elementID: str, attr: str, value: str, *, require_existing: bool = False) -> bool:
    obj, field = _resolve(elementID, attr)
    if not isinstance(value, str) or any(
        not (
            ch in "\t\n\r" or " " <= ch <= "\ud7ff" or "\ue000" <= ch <= "\ufffd" or "\U00010000" <= ch <= "\U0010ffff"
        )
        for ch in value
    ):
        raise TgiError("Expected XML string content", TgiFaultCode.INVALID_ARGUMENT)
    if attr == "name":
        value = _name_text(obj, value)
        if registry.rename(elementID, value):
            return True
    existing = getattr(obj, field)
    if existing is None and require_existing:
        return False
    if existing is not None and hasattr(existing, "value"):
        existing.value = value
        register_parent(existing, obj, (field,), "single")
    elif existing is None and is_dataclass(obj) and attr != "name":
        wrapper = {"description": Description, "display_name": DisplayName, "short_description": ShortDescription}[attr]
        child = wrapper(value=value)
        setattr(obj, field, child)
        register_parent(child, obj, (field,), "single")
    else:
        setattr(obj, field, value)
    return True


def _remove_attr(elementID: str, attr: str) -> bool:
    obj, field = _resolve(elementID, attr)
    existing = getattr(obj, field)
    if existing is None:
        return False
    if attr == "name" and registry.get_vlnv(elementID) is not None:
        return False
    setattr(obj, field, None)
    if is_dataclass(existing):
        _HANDLE_MANAGER.forget(get_handle(existing))
    return True


# ---------------------------------------------------------------------------
# BASE (F.7.63)
# ---------------------------------------------------------------------------


def getDescription(elementID: str) -> str | None:
    """Return the unresolved description text.

    Section: F.7.63.1.

    Args:
        elementID: Handle to an element supporting description.

    Returns:
        str | None: Source text, including empty strings; None if absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _get_text(elementID, "description")


def getDisplayName(elementID: str) -> str | None:
    """Return the unresolved displayName text.

    Section: F.7.63.2.

    Args:
        elementID: Handle to an element supporting displayName.

    Returns:
        str | None: Source text, including empty strings; None if absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _get_text(elementID, "display_name")


def getName(elementID: str) -> str | None:
    """Return the unresolved name text.

    Section: F.7.63.3.

    Args:
        elementID: Handle to an element supporting name.

    Returns:
        str | None: Source text, including empty strings; None if absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _get_text(elementID, "name")


def getShortDescription(elementID: str) -> str | None:
    """Return the unresolved shortDescription text.

    Section: F.7.63.4.

    Args:
        elementID: Handle to an element supporting shortDescription.

    Returns:
        str | None: Source text, including empty strings; None if absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _get_text(elementID, "short_description")


# ---------------------------------------------------------------------------
# EXTENDED (F.7.64)
# ---------------------------------------------------------------------------


def removeDescription(elementID: str) -> bool:
    """Remove the description content if present.

    Section: F.7.64.1.

    Args:
        elementID: Handle to an element supporting description.

    Returns:
        bool: True if removed; False if already absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _remove_attr(elementID, "description")


def removeDisplayName(elementID: str) -> bool:
    """Remove the displayName content if present.

    Section: F.7.64.2.

    Args:
        elementID: Handle to an element supporting displayName.

    Returns:
        bool: True if removed; False if already absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _remove_attr(elementID, "display_name")


def removeName(elementID: str) -> bool:
    """Remove the name content if present.

    Section: F.7.64.3.

    Args:
        elementID: Handle to an element supporting name.

    Returns:
        bool: True if removed; False if absent or required by a registered document.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _remove_attr(elementID, "name")


def removeShortDescription(elementID: str) -> bool:
    """Remove the shortDescription content if present.

    Section: F.7.64.4.

    Args:
        elementID: Handle to an element supporting shortDescription.

    Returns:
        bool: True if removed; False if already absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _remove_attr(elementID, "short_description")


def setDescription(elementID: str, description: str) -> bool:
    """Set the description text.

    Section: F.7.64.5.

    Args:
        elementID: Handle to an element supporting description.
        description: New string content.

    Returns:
        bool: True if updated; False if the content is absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _set_text(elementID, "description", description, require_existing=True)


def setDisplayName(elementID: str, displayName: str) -> bool:
    """Set the displayName text.

    Section: F.7.64.6.

    Args:
        elementID: Handle to an element supporting displayName.
        displayName: New string content.

    Returns:
        bool: True if updated; False if the content is absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _set_text(elementID, "display_name", displayName, require_existing=True)


def setName(elementID: str, name: str) -> bool:
    """Set the name text.

    Section: F.7.64.7.

    Args:
        elementID: Handle to an element supporting name.
        name: New string content.

    Returns:
        bool: True when the text is set.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content; ALREADY_EXISTS for a registered VLNV conflict.
    """
    return _set_text(elementID, "name", name)


def setShortDescription(elementID: str, shortDescription: str) -> bool:
    """Set the shortDescription text.

    Section: F.7.64.8.

    Args:
        elementID: Handle to an element supporting shortDescription.
        shortDescription: New string content (unresolved expression text).

    Returns:
        bool: True when the text is set.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed string content.
    """
    return _set_text(elementID, "short_description", shortDescription)
