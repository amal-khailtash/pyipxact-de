"""Assertion TGI operations for IEEE 1685-2022 Annex F.7.15 and F.7.16.

Assertions describe valid parameter settings through an unsigned-bit SystemVerilog
expression. Names and descriptions communicate a failed condition. The generated
Assertions container belongs to a component, abstraction definition, abstractor,
bus definition, design, design configuration, type definitions or generator chain.

BASE getters distinguish the evaluated Boolean, source expression and expression
handle. Evaluation currently supports self-contained constants; unresolved parameter
scope and unknown bits raise INVALID_ARGUMENT. EXTENDED edits preserve expression
identity and XML metadata. Parsed traversal registers ownership for subtree removal.
Additional name/description and Expression helpers are compatibility extensions,
not separately numbered functions in Annex F.
"""

from dataclasses import fields, is_dataclass
from typing import Any

from org.accellera.ipxact.v1685_2022 import Assertion, Assertions
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)

__all__: list[str] = [
    # BASE (F.7.15)
    "getAssertionAssert",
    "getAssertionAssertExpression",
    "getAssertionAssertID",
    "getAssertionIDs",
    "getAssertionName",
    "getAssertionDisplayName",
    "getAssertionShortDescription",
    "getAssertionDescription",
    "getAssertionExpression",
    "getAssertionExpressionID",
    # EXTENDED (F.7.16)
    "addAssertion",
    "removeAssertion",
    "setAssertionAssert",
    "setAssertionName",
    "setAssertionDisplayName",
    "setAssertionShortDescription",
    "setAssertionDescription",
    "setAssertionExpression",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _require_text(value: str, label: str) -> None:
    """Validate required source/name text before a mutation."""
    if not isinstance(value, str) or not value.strip():
        raise TgiError(f"{label} must be a nonempty string", TgiFaultCode.INVALID_ARGUMENT)


def _resolve_container(handle: str) -> Any:
    """Resolve a generated owner whose schema declares assertions."""
    obj = resolve_handle(handle)
    if obj is None or not is_dataclass(obj) or not any(field.name == "assertions" for field in fields(obj)):
        raise TgiError("Invalid assertion container handle", TgiFaultCode.INVALID_ID)
    return obj


def _resolve_assertion(assertionID: str) -> Assertion:
    obj = resolve_handle(assertionID)
    if not isinstance(obj, Assertion):
        raise TgiError("Invalid assertion handle", TgiFaultCode.INVALID_ID)
    return obj


def _text_value(obj: Any, field: str) -> str | None:
    if obj is None:
        return None
    f = getattr(obj, field, None)
    if f is None:
        return None
    return getattr(f, "value", f) if not isinstance(f, str) else f


# ---------------------------------------------------------------------------
# BASE (F.7.15)
# ---------------------------------------------------------------------------


def getAssertionAssert(assertionID: str) -> bool:
    """Return the self-contained assertion Boolean value.

    Section: F.7.15.1.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Evaluated Boolean assertion result.

    Raises:
        TgiError: INVALID_ARGUMENT when the expression cannot be evaluated.
    """
    from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser

    expression = getAssertionAssertExpression(assertionID)
    try:
        value = SvExpressionParser().evaluate(expression)
    except SvExpressionError as error:
        raise TgiError("Assertion expression cannot be resolved", TgiFaultCode.INVALID_ARGUMENT) from error
    if type(value) is not int or value not in (0, 1):
        raise TgiError("Assertion expression must evaluate to an unsigned bit", TgiFaultCode.INVALID_ARGUMENT)
    return bool(value)


def getAssertionAssertExpression(assertionID: str) -> str:
    """Return the assertion source expression without evaluation.

    Section: F.7.15.2.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Original SystemVerilog assertion expression text.
    """
    return _resolve_assertion(assertionID).assert_value.value


def getAssertionAssertID(assertionID: str) -> str:
    """Return the handle to the assertion's required assert expression.

    Section: F.7.15.3.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Handle to the generated unsigned-bit expression.
    """
    assertion = _resolve_assertion(assertionID)
    register_parent(assertion.assert_value, assertion, ("assert_value",), "single")
    return get_handle(assertion.assert_value)


def getAssertionIDs(assertionContainerElementID: str) -> list[str]:  # F.7.15.4
    """Return handles of ``assertion`` children under a parent.

    Section: F.7.15.4.

    Args:
        assertionContainerElementID: Handle referencing any object which MAY own an
            ``assertions`` container.

    Returns:
        list[str]: Handles (possibly empty) of assertion elements.

    Raises:
        TgiError: If the parent handle is invalid.
    """
    parent = _resolve_container(assertionContainerElementID)
    container = parent.assertions
    if container is None:
        return []
    register_parent(container, parent, ("assertions",), "single")
    for assertion in container.assertion:
        register_parent(assertion, container, ("assertion",), "list")
    return [get_handle(assertion) for assertion in container.assertion]


def getAssertionName(assertionID: str) -> str | None:  # compatibility extension
    """Return the assertion ``name``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Source text or child handle; None if absent.
    """
    a = _resolve_assertion(assertionID)
    return getattr(a, "name", None)


def getAssertionDisplayName(assertionID: str) -> str | None:  # compatibility extension
    """Return ``displayName`` value.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Source text or child handle; None if absent.
    """
    return _text_value(_resolve_assertion(assertionID), "display_name")


def getAssertionShortDescription(assertionID: str) -> str | None:  # compatibility extension
    """Return ``shortDescription`` value.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Source text or child handle; None if absent.
    """
    return _text_value(_resolve_assertion(assertionID), "short_description")


def getAssertionDescription(assertionID: str) -> str | None:  # compatibility extension
    """Return ``description`` value.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Source text or child handle; None if absent.
    """
    return _text_value(_resolve_assertion(assertionID), "description")


def getAssertionExpression(assertionID: str) -> str | None:  # compatibility extension
    """Return the assert expression string value.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Source text or child handle; None if absent.
    """
    a = _resolve_assertion(assertionID)
    expr = getattr(a, "assert_value", None)
    return getattr(expr, "value", None) if expr is not None else None


def getAssertionExpressionID(assertionID: str) -> str | None:  # compatibility extension
    """Return handle of the underlying expression object.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        Source text or child handle; None if absent.
    """
    return getAssertionAssertID(assertionID)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.16)
# ---------------------------------------------------------------------------


def addAssertion(assertionContainerElementID: str, name: str, expression: str) -> str:  # F.7.16.1
    """Create and append a new ``assertion`` element.

    Section: F.7.16.1.

    The parent must support an ``assertions.assertion`` list. The container
    will be created if absent.

    Args:
        assertionContainerElementID: Parent element handle.
        name: Assertion name.
        expression: Expression string for the assert condition.

    Returns:
        str: Handle of created assertion.

    Raises:
        TgiError: If parent handle invalid.
    """
    parent = _resolve_container(assertionContainerElementID)
    _require_text(name, "name")
    _require_text(expression, "expression")
    if parent.assertions is not None and any(item.name == name for item in parent.assertions.assertion):
        raise TgiError("Assertion name already exists", TgiFaultCode.INVALID_ARGUMENT)
    assertion = Assertion(name=name, assert_value=UnsignedBitExpression(value=expression))
    if parent.assertions is None:
        parent.assertions = Assertions()
    register_parent(parent.assertions, parent, ("assertions",), "single")
    parent.assertions.assertion.append(assertion)
    register_parent(assertion, parent.assertions, ("assertion",), "list")
    register_parent(assertion.assert_value, assertion, ("assert_value",), "single")
    return get_handle(assertion)


def removeAssertion(assertionID: str) -> bool:  # F.7.16.2
    """Remove an ``assertion`` element.

    Section: F.7.16.2.

    Args:
        assertionID: Assertion handle.

    Returns:
        bool: True if removed else False.
    """
    assertion = _resolve_assertion(assertionID)
    if get_parent_info(assertionID) is None:
        for root_id in registry.iter_by_predicate(lambda _root: True):
            root = resolve_handle(root_id)
            container = getattr(root, "assertions", None)
            if container is not None and any(item is assertion for item in container.assertion):
                register_parent(container, root, ("assertions",), "single")
                register_parent(assertion, container, ("assertion",), "list")
                break
    return detach_child_by_handle(assertionID)


def setAssertionAssert(assertionID: str, assertExpression: str) -> bool:
    """Set the assertion source expression, preserving its handle and attributes.

    Section: F.7.16.3.

    Args:
        assertionID: Handle to an assertion element.
        assertExpression: Nonempty SystemVerilog expression text; stored without evaluation.

    Returns:
        True after updating the expression.
    """
    assertion = _resolve_assertion(assertionID)
    _require_text(assertExpression, "assertExpression")
    assertion.assert_value.value = assertExpression
    register_parent(assertion.assert_value, assertion, ("assert_value",), "single")
    return True


def setAssertionName(assertionID: str, name: str) -> bool:  # compatibility extension
    """Set assertion ``name``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.
        name: Text value to assign.

    Returns:
        True after assignment.
    """
    a = _resolve_assertion(assertionID)
    _require_text(name, "name")
    a.name = name
    return True


def setAssertionDisplayName(assertionID: str, value: str) -> bool:  # compatibility extension
    """Set or create ``displayName``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.
        value: Text value to assign.

    Returns:
        True after assignment.
    """
    a = _resolve_assertion(assertionID)
    if not isinstance(value, str):
        raise TgiError("Value must be a string", TgiFaultCode.INVALID_ARGUMENT)
    if a.display_name is None:
        a.display_name = DisplayName(value=value)
    else:
        a.display_name.value = value
    return True


def setAssertionShortDescription(assertionID: str, value: str) -> bool:  # compatibility extension
    """Set or create ``shortDescription``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.
        value: Text value to assign.

    Returns:
        True after assignment.
    """
    a = _resolve_assertion(assertionID)
    if not isinstance(value, str):
        raise TgiError("Value must be a string", TgiFaultCode.INVALID_ARGUMENT)
    if a.short_description is None:
        a.short_description = ShortDescription(value=value)
    else:
        a.short_description.value = value
    return True


def setAssertionDescription(assertionID: str, value: str) -> bool:  # compatibility extension
    """Set or create ``description``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.
        value: Text value to assign.

    Returns:
        True after assignment.
    """
    a = _resolve_assertion(assertionID)
    if not isinstance(value, str):
        raise TgiError("Value must be a string", TgiFaultCode.INVALID_ARGUMENT)
    if a.description is None:
        a.description = Description(value=value)
    else:
        a.description.value = value
    return True


def setAssertionExpression(assertionID: str, expression: str) -> bool:  # compatibility extension
    """Set the assert expression string.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.
        expression: Text value to assign.

    Returns:
        True after assignment.
    """
    return setAssertionAssert(assertionID, expression)
