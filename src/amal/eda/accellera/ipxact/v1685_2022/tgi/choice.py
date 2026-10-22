# ruff: noqa: I001
"""Choice category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.25) and EXTENDED (F.7.26) Choice functions.

Provides traversal and manipulation of enumerations for :class:`Choices.Choice` objects.
All functions raise :class:`TgiError` with :class:`TgiFaultCode.INVALID_ID` for invalid handles.
"""

from collections.abc import Sequence

from org.accellera.ipxact.v1685_2022 import Choices
from .core import TgiError, TgiFaultCode, get_handle, resolve_handle, register_parent, detach_child_by_handle

__all__ = [
    # BASE (F.7.25)
    "getChoiceEnumerationIDs",
    "getEnumerationValue",
    "getEnumerationValueExpression",
    # EXTENDED (F.7.26)
    "addChoiceEnumeration",
    "removeChoiceEnumeration",
    "setEnumerationValue",
]

def _resolve_choice(choiceID: str) -> Choices.Choice | None:
    """Resolve a handle to a Choices.Choice object.

    Args:
        choiceID: Handle to a Choices.Choice element.
    Returns:
        Choices.Choice instance or None.
    """
    obj = resolve_handle(choiceID)
    return obj if isinstance(obj, Choices.Choice) else None

def _resolve_enum(enumID: str) -> Choices.Choice.Enumeration | None:
    """Resolve a handle to a Choices.Choice.Enumeration object.

    Args:
        enumID: Handle to a Choices.Choice.Enumeration element.
    Returns:
        Choices.Choice.Enumeration instance or None.
    """
    obj = resolve_handle(enumID)
    return obj if isinstance(obj, Choices.Choice.Enumeration) else None

# ---------------------------------------------------------------------------
# BASE (F.7.25)
# ---------------------------------------------------------------------------

def getChoiceEnumerationIDs(choiceID: str) -> list[str]:
    """Return handles to all choiceEnumeration elements of a choice.

    Section: F.7.25.1

    Args:
        choiceID: Handle to a Choices.Choice element.
    Returns:
        List of handles to Choices.Choice.Enumeration elements.
    Raises:
        TgiError: If the handle is invalid.
    """
    ch = _resolve_choice(choiceID)
    if ch is None:
        raise TgiError("Invalid choice handle", TgiFaultCode.INVALID_ID)
    handles = []
    for enum in ch.enumeration:
        register_parent(enum, ch, ("enumeration",), "list")
        handles.append(get_handle(enum))
    return handles

def getEnumerationValue(choiceEnumerationID: str) -> str:
    """Return the enumerationValue defined on the given enumeration element.

    Section: F.7.25.2

    Args:
        choiceEnumerationID: Handle to a Choices.Choice.Enumeration element.
    Returns:
        The enumeration value string.
    Raises:
        TgiError: If the handle is invalid.
    """
    en = _resolve_enum(choiceEnumerationID)
    if en is None:
        raise TgiError("Invalid enumeration handle", TgiFaultCode.INVALID_ID)
    return en.value

def getEnumerationValueExpression(choiceEnumerationID: str) -> str:
    """Return the expression defined on the given enumeration element.

    Section: F.7.25.3

    Args:
        choiceEnumerationID: Handle to a Choices.Choice.Enumeration element.
    Returns:
        The enumeration expression string.
    Raises:
        TgiError: If the handle is invalid.
    """
    en = _resolve_enum(choiceEnumerationID)
    if en is None:
        raise TgiError("Invalid enumeration handle", TgiFaultCode.INVALID_ID)
    return en.value

# ---------------------------------------------------------------------------
# EXTENDED (F.7.26)
# ---------------------------------------------------------------------------

def addChoiceEnumeration(choiceID: str, name: str) -> str:
    """Add a new enumeration with the given name to the choice.

    Section: F.7.26.1

    Args:
        choiceID: Handle to a Choices.Choice element.
        name: Name for the new enumeration.
    Returns:
        Handle to the new Choices.Choice.Enumeration element.
    Raises:
        TgiError: If the handle is invalid.
    """
    ch = _resolve_choice(choiceID)
    if ch is None:
        raise TgiError("Invalid choice handle", TgiFaultCode.INVALID_ID)
    if not isinstance(name, str):
        raise TgiError("Enumeration value requires a string", TgiFaultCode.INVALID_ARGUMENT)
    enum = Choices.Choice.Enumeration(value=name)
    ch.enumeration.append(enum)  # type: ignore[attr-defined]
    register_parent(enum, ch, ("enumeration",), "list")
    return get_handle(enum)

def removeChoiceEnumeration(choiceEnumerationID: str) -> bool:
    """Remove the given choiceEnumeration from its parent choice.

    Section: F.7.26.2

    Args:
        choiceEnumerationID: Handle to a Choices.Choice.Enumeration element.
    Returns:
        True if removed, False if not found.
    """
    if _resolve_enum(choiceEnumerationID) is None:
        raise TgiError("Invalid enumeration handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(choiceEnumerationID)

def setEnumerationValue(choiceEnumerationID: str, value: str) -> bool:
    """Set the value on the given enumeration element.

    Section: F.7.26.3

    Args:
        choiceEnumerationID: Handle to a Choices.Choice.Enumeration element.
        value: New value expression.
    Returns:
        True if set, False if not found.
    Raises:
        TgiError: If the handle is invalid.
    """
    en = _resolve_enum(choiceEnumerationID)
    if en is None:
        raise TgiError("Invalid enumeration handle", TgiFaultCode.INVALID_ID)
    if not isinstance(value, str):
        raise TgiError("Enumeration value requires a string", TgiFaultCode.INVALID_ARGUMENT)
    en.value = value
    return True


def _validated_choice(name: str, enumerations: Sequence[str]) -> Choices.Choice:
    """Construct a choice only after validating its name and enumeration array."""
    if not isinstance(name, str) or not name.strip():
        raise TgiError("Choice name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if isinstance(enumerations, (str, bytes)) or not isinstance(enumerations, Sequence):
        raise TgiError("Enumerations require a sequence of strings", TgiFaultCode.INVALID_ARGUMENT)
    values = list(enumerations)
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise TgiError("Enumerations require nonempty expressions", TgiFaultCode.INVALID_ARGUMENT)
    return Choices.Choice(name=name, enumeration=[Choices.Choice.Enumeration(value=value) for value in values])
