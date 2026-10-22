"""IEEE 1685-2022 Bus Definition TGI operations.

Implements the 12 BASE functions in F.7.17 and the 13 numbered EXTENDED
functions in F.7.18. The compatibility operation
``removeBusDefinitionSystemGroupName`` is specified in F.7.20.15. Other
legacy conveniences remain available and are labeled as project extensions.

F.4 configured ``busDefInstanceID`` handles reference configured top-level
objects. The 2022 generated bindings define :class:`BusDefinition` but no
configured bus definition instance class, so this module currently resolves
typed ``BusDefinition`` handles only. The configured instance wrapper remains
planned work.
"""

from collections.abc import Iterable, Sequence
from enum import Enum
from typing import Any
from unicodedata import category

from org.accellera.ipxact.v1685_2022 import BusDefinition
from org.accellera.ipxact.v1685_2022.assertion import Assertion  # type: ignore
from org.accellera.ipxact.v1685_2022.assertions import Assertions
from org.accellera.ipxact.v1685_2022.choices import Choices
from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType
from org.accellera.ipxact.v1685_2022.parameter import Parameter  # type: ignore
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression

# ruff: noqa: I001 (import ordering harmonised with sibling modules)

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
    vlnv_to_tuple,
)

__all__: list[str] = [
    # BASE (F.7.17)
    "getBusDefinitionSystemGroupNameIDs",
    "getBusDefinitionChoiceIDs",
    # Nonstandard compatibility getters.
    "getBusDefinitionParameterIDs",
    "getBusDefinitionAssertionIDs",
    "getBusDefinitionVendor",
    "getBusDefinitionLibrary",
    "getBusDefinitionName",
    "getBusDefinitionVersion",
    "getBusDefinitionDisplayName",
    "getBusDefinitionShortDescription",
    "getBusDefinitionDescription",
    # F.7.17 scalar and reference operations.
    "getBusDefinitionDirectConnection",
    "getBusDefinitionBroadcast",
    "getBusDefinitionIsAddressable",
    "getBusDefinitionExtendsVendor",
    "getBusDefinitionExtendsLibrary",
    "getBusDefinitionExtendsName",
    "getBusDefinitionExtendsVersion",
    "getBusDefinitionExtendsVLNV",
    "getBusDefinitionExtendsRefByVLNV",
    "getBusDefinitionMaxInitiators",
    "getBusDefinitionMaxInitiatorsExpression",
    "getBusDefinitionMaxInitiatorsID",
    "getBusDefinitionMaxTargets",
    "getBusDefinitionMaxTargetsExpression",
    "getBusDefinitionMaxTargetsID",
    "getBusDefinitionSystemGroupNameValue",
    # EXTENDED (F.7.18)
    "addBusDefinitionSystemGroupName",
    "addBusDefinitionChoice",
    # Nonstandard compatibility helpers.
    "addBusDefinitionParameterInteger",
    "addBusDefinitionAssertion",
    "removeBusDefinitionSystemGroupName",
    "removeBusDefinitionChoice",
    "removeBusDefinitionParameter",
    "removeBusDefinitionAssertion",
    # Nonstandard compatibility setters.
    "setBusDefinitionDisplayName",
    "setBusDefinitionShortDescription",
    "setBusDefinitionDescription",
    # F.7.18 scalar and reference operations.
    "setBusDefinitionExtends",
    "removeBusDefinitionExtends",
    "setBusDefinitionDirectConnection",
    "removeBusDefinitionDirectConnection",
    "setBusDefinitionBroadcast",
    "removeBusDefinitionBroadcast",
    "setBusDefinitionIsAddressable",
    "removeBusDefinitionIsAddressable",
    "setBusDefinitionMaxInitiators",
    "removeBusDefinitionMaxInitiators",
    "setBusDefinitionMaxTargets",
    "removeBusDefinitionMaxTargets",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve(busDefinitionID: str) -> BusDefinition:
    """Resolve and type-check a bus definition handle.

    Args:
        busDefinitionID: Handle referencing a busDefinition element.

    Returns:
        BusDefinition: Resolved schema object.

    Raises:
        TgiError: If the handle is invalid or not a BusDefinition.
    """
    obj = resolve_handle(busDefinitionID)
    if not isinstance(obj, BusDefinition):  # type: ignore[arg-type]
        raise TgiError("Invalid busDefinition handle", TgiFaultCode.INVALID_ID)
    return obj


def _ids(items: Iterable[Any]) -> list[str]:
    return [get_handle(i) for i in items]


def _scalar(obj: Any, attr: str) -> str | None:
    val = getattr(obj, attr, None)
    if val is None:
        return None
    value = getattr(val, "value", val)
    return value.value if isinstance(value, Enum) else value


_UINT_MAX = (1 << 32) - 1


def _integer_text(source: str) -> int | None:
    """Evaluate a self-contained SystemVerilog integer expression."""
    source = source.strip()
    if source.lstrip("+-").isdigit():
        return int(source, 10)
    try:
        try:
            return int(source, 0)
        except ValueError:
            from amal.eda.systemverilog.expression_parser import SvExpressionParser

            value = SvExpressionParser().evaluate(source)
            return value if type(value) is int else None
    except ImportError, ValueError, TypeError, AttributeError:
        return None


def _unsigned_value(expression: Any) -> int | None:
    """Evaluate an unsigned 32-bit expression, returning None if unresolved."""
    source = getattr(expression, "value", None)
    if type(source) is int:
        value = source
    elif isinstance(source, str) and source.strip():
        value = _integer_text(source)
    else:
        return None
    if value is None or not 0 <= value <= _UINT_MAX:
        return None
    minimum = getattr(expression, "minimum", None)
    maximum = getattr(expression, "maximum", None)
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        return None
    return value


def _expression_source(value: Any, argument: str, current: Any = None) -> str:
    """Validate setter input and evaluated unsigned-int bounds before mutation."""
    if type(value) is int:
        if not 0 <= value <= _UINT_MAX:
            raise TgiError(f"{argument} is outside the unsigned int range", TgiFaultCode.INVALID_ARGUMENT)
        source = str(value)
        numeric: int | None = value
    elif isinstance(value, str) and value.strip():
        source = value
        parsed = _integer_text(source)
        numeric = parsed if parsed is not None and 0 <= parsed <= _UINT_MAX else None
        if parsed is not None and numeric is None:
            raise TgiError(f"{argument} is outside the unsigned int range", TgiFaultCode.INVALID_ARGUMENT)
    else:
        raise TgiError(f"{argument} must be an integer or non-empty expression", TgiFaultCode.INVALID_ARGUMENT)

    minimum = getattr(current, "minimum", None)
    maximum = getattr(current, "maximum", None)
    if numeric is not None and (
        (minimum is not None and numeric < minimum) or (maximum is not None and numeric > maximum)
    ):
        raise TgiError(f"{argument} violates expression bounds", TgiFaultCode.INVALID_ARGUMENT)
    return source


def _set_unsigned_expression(bus_definition: BusDefinition, attribute: str, value: int | str) -> None:
    current = getattr(bus_definition, attribute)
    if current is not None and not isinstance(current, UnsignedIntExpression):
        raise TgiError(f"Invalid {attribute} expression", TgiFaultCode.INVALID_ID)
    source = _expression_source(value, attribute, current)
    if current is None:
        current = UnsignedIntExpression(value=source)
        setattr(bus_definition, attribute, current)
    else:
        # Preserve generated wrapper identity, range attributes and vendor attributes.
        current.value = source
    register_parent(current, bus_definition, (attribute,), "single")


def _name_value(value: Any, argument: str) -> str:
    """Validate a schema ``xs:Name`` value."""
    if not isinstance(value, str) or not value:
        raise TgiError(f"{argument} must be a non-empty xs:Name", TgiFaultCode.INVALID_ARGUMENT)

    def is_start(char: str) -> bool:
        return char in ":_" or category(char) in {"Lu", "Ll", "Lt", "Lm", "Lo", "Nl"}

    def is_part(char: str) -> bool:
        return is_start(char) or char in "-." or category(char) in {"Mn", "Mc", "Nd", "Pc"}

    if not is_start(value[0]) or any(not is_part(char) for char in value[1:]):
        raise TgiError(f"{argument} must be a valid xs:Name", TgiFaultCode.INVALID_ARGUMENT)
    return value


# ---------------------------------------------------------------------------
# Traversal
# ---------------------------------------------------------------------------


def getBusDefinitionSystemGroupNameIDs(busDefinitionID: str) -> list[str]:  # F.7.17.12
    """Return the handles of all system group names.

    Section: F.7.17.12.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        List of handles to ``systemGroupName`` elements; empty when absent.
    """
    bd = _resolve(busDefinitionID)
    sgs = getattr(bd, "system_group_names", None)
    if sgs is None:
        return []
    items = getattr(sgs, "system_group_name", [])
    for item in items:
        register_parent(item, bd, ("system_group_names", "system_group_name"), "list")
    return _ids(items)


def getBusDefinitionChoiceIDs(busDefinitionID: str) -> list[str]:  # F.7.17.2
    """Return the handles of choices on a bus definition.

    Section: F.7.17.2.

    Args:
        busDefinitionID: Handle to a bus definition element.

    Returns:
        List of choice handles; empty when no choices are defined.
    """
    bd = _resolve(busDefinitionID)
    chs = getattr(bd, "choices", None)
    if chs is None:
        return []
    for choice in chs.choice:
        register_parent(choice, bd, ("choices", "choice"), "list")
    return [get_handle(choice) for choice in chs.choice]


def getBusDefinitionParameterIDs(busDefinitionID: str) -> list[str]:  # nonstandard compatibility helper
    """Return handles of parameter children.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Handle to a bus definition element.

    Returns:
        List of parameter handles, empty when absent.
    """
    bd = _resolve(busDefinitionID)
    ps = getattr(bd, "parameters", None)
    if ps is None:
        return []
    register_parent(ps, bd, ("parameters",), "single")
    register_parent(ps, bd, ("parameters",), "single")
    for parameter in ps.parameter:
        register_parent(parameter, ps, ("parameter",), "list")
    return [get_handle(parameter) for parameter in ps.parameter]


def getBusDefinitionAssertionIDs(busDefinitionID: str) -> list[str]:  # nonstandard compatibility helper
    """Return handles of assertion children.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Handle to a bus definition element.

    Returns:
        List of assertion handles, empty when absent.
    """
    bd = _resolve(busDefinitionID)
    ats = getattr(bd, "assertions", None)
    if ats is None:
        return []
    register_parent(ats, bd, ("assertions",), "single")
    register_parent(ats, bd, ("assertions",), "single")
    for assertion in ats.assertion:
        register_parent(assertion, ats, ("assertion",), "list")
    return [get_handle(assertion) for assertion in ats.assertion]


# ---------------------------------------------------------------------------
# Getters
# ---------------------------------------------------------------------------


def getBusDefinitionVendor(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the bus definition vendor.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Vendor string.
    """
    return _scalar(_resolve(busDefinitionID), "vendor")


def getBusDefinitionLibrary(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the bus definition library.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Library string.
    """
    return _scalar(_resolve(busDefinitionID), "library")


def getBusDefinitionName(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the bus definition name.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Name string.
    """
    return _scalar(_resolve(busDefinitionID), "name")


def getBusDefinitionVersion(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the bus definition version.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Version string.
    """
    return _scalar(_resolve(busDefinitionID), "version")


def getBusDefinitionDisplayName(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the display name.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Display name string, or ``None`` when absent.
    """
    return _scalar(_resolve(busDefinitionID), "display_name")


def getBusDefinitionShortDescription(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the short description.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Short-description text, or ``None`` when absent.
    """
    return _scalar(_resolve(busDefinitionID), "short_description")


def getBusDefinitionDescription(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the description.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Description text, or ``None`` when absent.
    """
    return _scalar(_resolve(busDefinitionID), "description")


def getBusDefinitionDirectConnection(busDefOrBusDefInstanceID: str) -> bool | None:  # F.7.17.3
    """Return ``directConnection``.

    Section: F.7.17.3.

    Args:
        busDefOrBusDefInstanceID: Handle to a bus definition object. Configured
            instance handles are not available until their wrapper is implemented.

    Returns:
        Boolean value, or ``None`` if the mandatory element is absent.
    """
    bd = _resolve(busDefOrBusDefInstanceID)
    return getattr(bd, "direct_connection", None)


def getBusDefinitionBroadcast(busDefOrBusDefInstanceID: str) -> bool:  # F.7.17.1
    """Return ``broadcast`` with the standard default of ``False``.

    Section: F.7.17.1.

    Args:
        busDefOrBusDefInstanceID: Handle to a bus definition object. Configured
            instance handles are not available until their wrapper is implemented.

    Returns:
        Boolean broadcast value; an absent optional element returns ``False``.
    """
    bd = _resolve(busDefOrBusDefInstanceID)
    value = getattr(bd, "broadcast", None)
    return False if value is None else value


def getBusDefinitionIsAddressable(busDefOrBusDefInstanceID: str) -> bool | None:  # F.7.17.5
    """Return ``isAddressable``.

    Section: F.7.17.5.

    Args:
        busDefOrBusDefInstanceID: Handle to a bus definition object. Configured
            instance handles are not available until their wrapper is implemented.

    Returns:
        Boolean value, or ``None`` if the mandatory element is absent.
    """
    bd = _resolve(busDefOrBusDefInstanceID)
    return getattr(bd, "is_addressable", None)


def getBusDefinitionExtendsVendor(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the vendor from ``extends``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Vendor string, or ``None`` when no reference exists.
    """
    ext = getattr(_resolve(busDefinitionID), "extends", None)
    return getattr(ext, "vendor", None) if ext is not None else None


def getBusDefinitionExtendsLibrary(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the library from ``extends``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Library string, or ``None`` when no reference exists.
    """
    ext = getattr(_resolve(busDefinitionID), "extends", None)
    return getattr(ext, "library", None) if ext is not None else None


def getBusDefinitionExtendsName(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the name from ``extends``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Name string, or ``None`` when no reference exists.
    """
    ext = getattr(_resolve(busDefinitionID), "extends", None)
    return getattr(ext, "name", None) if ext is not None else None


def getBusDefinitionExtendsVersion(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return the version from ``extends``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Version string, or ``None`` when no reference exists.
    """
    ext = getattr(_resolve(busDefinitionID), "extends", None)
    return getattr(ext, "version", None) if ext is not None else None


def getBusDefinitionExtendsVLNV(busDefinitionID: str) -> str | None:  # nonstandard compatibility helper
    """Return colon-joined VLNV for ``extends``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Colon-joined VLNV, or ``None`` when no complete reference exists.
    """
    """Return concatenated VLNV string for ``extends`` (vendor:library:name:version)."""
    bd = _resolve(busDefinitionID)
    ext = getattr(bd, "extends", None)
    if ext is None:
        return None
    parts_raw = [getattr(ext, a, None) for a in ("vendor", "library", "name", "version")]
    if any(p is None for p in parts_raw):
        return None
    return ":".join(str(p) for p in parts_raw)


def getBusDefinitionExtendsRefByVLNV(busDefinitionID: str) -> str | None:  # F.7.17.4
    """Return the extended bus VLNV in vendor:library:name:version form.

    Annex F specifies a String result, while the WSDL response uses a string
    array. This API preserves its established colon-separated String result.

    Section: F.7.17.4.

    Args:
        busDefinitionID: Handle to a typed ``BusDefinition`` element.

    Returns:
        String VLNV, or ``None`` when ``extends`` is absent or incomplete.
    """
    return getBusDefinitionExtendsVLNV(busDefinitionID)


def getBusDefinitionMaxInitiators(busDefOrBusDefInstanceID: str) -> int | None:  # F.7.17.6
    """Return the evaluated unsigned value of ``maxInitiators``.

    Section: F.7.17.6.

    Args:
        busDefOrBusDefInstanceID: Handle to a bus definition object; configured
            instance handles are not available until their wrapper is implemented.

    Returns:
        Evaluated unsigned 32-bit value, or ``None`` when absent or unresolved.
    """
    return _unsigned_value(_resolve(busDefOrBusDefInstanceID).max_initiators)


def getBusDefinitionMaxInitiatorsExpression(busDefOrBusDefInstanceID: str) -> str | None:  # F.7.17.7
    """Return the original ``maxInitiators`` source expression.

    Section: F.7.17.7.

    Args:
        busDefOrBusDefInstanceID: Handle to a bus definition object; configured
            instance handles are not available until their wrapper is implemented.

    Returns:
        Source string, or ``None`` when the element is absent.
    """
    return _scalar(_resolve(busDefOrBusDefInstanceID), "max_initiators")


def getBusDefinitionMaxInitiatorsID(busDefID: str) -> str | None:  # F.7.17.8
    """Return the ``maxInitiators`` element handle.

    Section: F.7.17.8.

    Args:
        busDefID: Handle to a bus definition element.

    Returns:
        Expression handle, or ``None`` when the optional element is absent.
    """
    bd = _resolve(busDefID)
    expr = bd.max_initiators
    if expr is None:
        return None
    register_parent(expr, bd, ("max_initiators",), "single")
    return get_handle(expr)


def getBusDefinitionMaxTargets(busDefOrBusDefInstanceID: str) -> int | None:  # F.7.17.9
    """Return the evaluated unsigned value of ``maxTargets``.

    Section: F.7.17.9.

    Args:
        busDefOrBusDefInstanceID: Handle to a bus definition object; configured
            instance handles are not available until their wrapper is implemented.

    Returns:
        Evaluated unsigned 32-bit value, or ``None`` when absent or unresolved.
    """
    return _unsigned_value(_resolve(busDefOrBusDefInstanceID).max_targets)


def getBusDefinitionMaxTargetsExpression(busDefinitionID: str) -> str | None:  # F.7.17.10
    """Return the original ``maxTargets`` source expression.

    Section: F.7.17.10.

    Args:
        busDefinitionID: Handle to a typed ``BusDefinition`` element.

    Returns:
        Source string, or ``None`` when the element is absent.
    """
    return _scalar(_resolve(busDefinitionID), "max_targets")


def getBusDefinitionMaxTargetsID(busDefID: str) -> str | None:  # F.7.17.11
    """Return the ``maxTargets`` element handle.

    Section: F.7.17.11.

    Args:
        busDefID: Handle to a bus definition element.

    Returns:
        Expression handle, or ``None`` when the optional element is absent.
    """
    bd = _resolve(busDefID)
    expr = bd.max_targets
    if expr is None:
        return None
    register_parent(expr, bd, ("max_targets",), "single")
    return get_handle(expr)


def getBusDefinitionSystemGroupNameValue(systemGroupNameID: str) -> str | None:  # nonstandard compatibility helper
    """Return the ``value`` of a ``systemGroupName`` element.

    Args:
        systemGroupNameID: Handle of a systemGroupName element.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Returns:
        str | None: String value.

    Raises:
        TgiError: If the handle is invalid.
    """
    sgn = resolve_handle(systemGroupNameID)
    if not isinstance(sgn, BusDefinition.SystemGroupNames.SystemGroupName):
        raise TgiError("Invalid systemGroupName handle", TgiFaultCode.INVALID_ID)
    return getattr(sgn, "value", None)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.18)
# ---------------------------------------------------------------------------


def addBusDefinitionSystemGroupName(busDefinitionID: str, value: str) -> str:  # F.7.18.2
    """Append a new ``systemGroupName`` element.

    Section: F.7.18.2.

    Args:
        busDefinitionID: Bus definition handle.
        value: Group name string.

    Returns:
        str: Handle of created element.
    """
    bd = _resolve(busDefinitionID)
    value = _name_value(value, "value")
    if bd.system_group_names is None:
        bd.system_group_names = BusDefinition.SystemGroupNames()  # type: ignore[attr-defined]
    sgn = BusDefinition.SystemGroupNames.SystemGroupName(value=value)
    bd.system_group_names.system_group_name.append(sgn)  # type: ignore[attr-defined]
    register_parent(sgn, bd, ("system_group_names", "system_group_name"), "list")
    return get_handle(sgn)


def addBusDefinitionChoice(busDefinitionID: str, name: str, enumerations: Sequence[str]) -> str:  # F.7.18.1
    """Append a named choice with its enumeration values in supplied order.

    Section: F.7.18.1.

    Args:
        busDefinitionID: Handle to a bus definition element.
        name: Choice name.
        enumerations: Ordered list of non-empty enumeration expressions.

    Returns:
        Handle to the new choice.

    Raises:
        TgiError: If the handle or choice data is invalid.
    """
    from .choice import _validated_choice

    bd = _resolve(busDefinitionID)
    ch = _validated_choice(name, enumerations)
    if bd.choices is None:
        bd.choices = Choices()
    bd.choices.choice.append(ch)
    register_parent(ch, bd, ("choices", "choice"), "list")
    return get_handle(ch)


def addBusDefinitionParameterInteger(
    busDefinitionID: str, name: str, value: int
) -> str:  # nonstandard compatibility helper
    """Add a parameter with a typed integer value.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.
        name: Parameter name.
    value: Integer value (stored as string expression).

    Returns:
        Handle to the created parameter.
    """
    bd = _resolve(busDefinitionID)
    if type(value) is not int:
        raise TgiError("value must be an integer", TgiFaultCode.INVALID_ARGUMENT)
    if bd.parameters is None:
        bd.parameters = Parameters()
    from org.accellera.ipxact.v1685_2022.value import Value

    param = Parameter(name=name, value=Value(value=str(value)))
    register_parent(bd.parameters, bd, ("parameters",), "single")
    bd.parameters.parameter.append(param)
    register_parent(param, bd.parameters, ("parameter",), "list")
    return get_handle(param)


def addBusDefinitionAssertion(
    busDefinitionID: str, name: str, expression: str
) -> str:  # nonstandard compatibility helper
    """Add an assertion using the shared assertion-category contract.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.
        name: Assertion name.
        expression: Unsigned bit expression text.

    Returns:
        Handle to the created assertion.
    """
    from .assertion import addAssertion

    _resolve(busDefinitionID)
    return addAssertion(busDefinitionID, name, expression)


def removeBusDefinitionSystemGroupName(systemGroupNameID: str) -> bool:  # F.7.20.15
    """Remove the referenced systemGroupName from its owning bus definition.

    Section: F.7.20.15.

    Args:
        systemGroupNameID: Handle to a generated ``systemGroupName`` element.

    Returns:
        ``True`` if removed; ``False`` when the typed element has no active owner.

    Raises:
        TgiError: If the handle is invalid or references another element type.
    """
    item = resolve_handle(systemGroupNameID)
    if not isinstance(item, BusDefinition.SystemGroupNames.SystemGroupName):
        raise TgiError("Invalid systemGroupName handle", TgiFaultCode.INVALID_ID)
    info = get_parent_info(systemGroupNameID)
    if info is None:
        return False
    parent = resolve_handle(info.parent_handle)
    if not isinstance(parent, BusDefinition) or info.path != ("system_group_names", "system_group_name"):
        raise TgiError("systemGroupName is not owned by a bus definition", TgiFaultCode.INVALID_ID)
    removed = detach_child_by_handle(systemGroupNameID)
    if removed and parent.system_group_names is not None and not parent.system_group_names.system_group_name:
        parent.system_group_names = None
    return removed


def removeBusDefinitionChoice(choiceID: str) -> bool:  # F.7.18.4
    """Remove a choice by handle and clear its container when empty.

    Section: F.7.18.4.

    Args:
        choiceID: Handle to a choice element.

    Returns:
        ``True`` if removed; otherwise ``False`` for a valid unowned choice.

    Raises:
        TgiError: If the handle is invalid or references another element type.
    """
    obj = resolve_handle(choiceID)
    if not isinstance(obj, Choices.Choice):
        raise TgiError("Invalid choice handle", TgiFaultCode.INVALID_ID)
    info = get_parent_info(choiceID)
    if info is None:
        return False
    parent = resolve_handle(info.parent_handle)
    if not isinstance(parent, BusDefinition) or info.path != ("choices", "choice"):
        raise TgiError("Choice is not owned by a bus definition", TgiFaultCode.INVALID_ID)
    removed = detach_child_by_handle(choiceID)
    if removed and parent.choices is not None and not parent.choices.choice:
        parent.choices = None
    return removed


def removeBusDefinitionParameter(parameterID: str) -> bool:  # nonstandard compatibility helper
    """Remove a parameter and clear its optional container when empty.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        parameterID: Handle to a parameter element.

    Returns:
        ``True`` if removed; otherwise ``False`` when the element is unowned.
    """
    parameter = resolve_handle(parameterID)
    if not isinstance(parameter, Parameter):
        raise TgiError("Invalid parameter handle", TgiFaultCode.INVALID_ID)
    info = get_parent_info(parameterID)
    if info is None:
        return False
    container = resolve_handle(info.parent_handle)
    if not isinstance(container, Parameters) or info.path != ("parameter",):
        raise TgiError("Parameter is not owned by a bus definition", TgiFaultCode.INVALID_ID)
    container_info = get_parent_info(info.parent_handle)
    parent = resolve_handle(container_info.parent_handle) if container_info is not None else None
    if not isinstance(parent, BusDefinition) or container_info.path != ("parameters",):
        raise TgiError("Parameter is not owned by a bus definition", TgiFaultCode.INVALID_ID)
    removed = detach_child_by_handle(parameterID)
    if (
        removed
        and isinstance(parent, BusDefinition)
        and parent.parameters is not None
        and not parent.parameters.parameter
    ):
        parent.parameters = None
    return removed


def removeBusDefinitionAssertion(assertionID: str) -> bool:  # nonstandard compatibility helper
    """Remove an assertion and clear its optional container when empty.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        assertionID: Handle to an assertion element.

    Returns:
        ``True`` if removed; otherwise ``False`` when the element is unowned.
    """
    assertion = resolve_handle(assertionID)
    if not isinstance(assertion, Assertion):
        raise TgiError("Invalid assertion handle", TgiFaultCode.INVALID_ID)
    info = get_parent_info(assertionID)
    if info is None:
        return False
    container = resolve_handle(info.parent_handle)
    if not isinstance(container, Assertions) or info.path != ("assertion",):
        raise TgiError("Assertion is not owned by a bus definition", TgiFaultCode.INVALID_ID)
    container_info = get_parent_info(info.parent_handle)
    parent = resolve_handle(container_info.parent_handle) if container_info is not None else None
    if not isinstance(parent, BusDefinition) or container_info.path != ("assertions",):
        raise TgiError("Assertion is not owned by a bus definition", TgiFaultCode.INVALID_ID)
    removed = detach_child_by_handle(assertionID)
    if (
        removed
        and isinstance(parent, BusDefinition)
        and parent.assertions is not None
        and not parent.assertions.assertion
    ):
        parent.assertions = None
    return removed


def setBusDefinitionDisplayName(busDefinitionID: str, value: str) -> bool:  # nonstandard compatibility helper
    """Set or create ``displayName``.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.
        value: Display-name text.

    Returns:
        ``True`` after the value is set.
    """
    bd = _resolve(busDefinitionID)
    bd.display_name = value  # type: ignore[attr-defined]
    return True


def setBusDefinitionShortDescription(busDefinitionID: str, value: str) -> bool:  # nonstandard compatibility helper
    """Set or create ``shortDescription`` while preserving a present wrapper.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.
        value: Short-description text.

    Returns:
        ``True`` after the value is set.
    """
    from org.accellera.ipxact.v1685_2022.short_description import ShortDescription

    bd = _resolve(busDefinitionID)
    if bd.short_description is None:
        bd.short_description = ShortDescription(value=value)
    else:
        bd.short_description.value = value
    return True


def setBusDefinitionDescription(busDefinitionID: str, value: str) -> bool:  # nonstandard compatibility helper
    """Set or create ``description`` while preserving a present wrapper.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.
        value: Description text.

    Returns:
        ``True`` after the value is set.
    """
    from org.accellera.ipxact.v1685_2022.description import Description

    bd = _resolve(busDefinitionID)
    if bd.description is None:
        bd.description = Description(value=value)
    else:
        bd.description.value = value
    return True


def setBusDefinitionExtends(
    busDefID: str,
    busDefVLNV: Sequence[str],
) -> bool:  # F.7.18.10
    """Set or create the ``extends`` reference (VLNV).

    Section: F.7.18.10.

    Args:
        busDefID: Handle to a typed ``BusDefinition`` element.
        busDefVLNV: Four strings ``(vendor, library, name, version)``.

    Returns:
        ``True`` after the validated reference is set.

    Raises:
        TgiError: If the handle is invalid or the VLNV is malformed.
    """
    bd = _resolve(busDefID)
    vendor, library, name, version = vlnv_to_tuple(busDefVLNV)
    parts = (vendor, library, name, version)
    if any(not isinstance(part, str) or not part for part in parts):
        raise TgiError("VLNV parts must be non-empty strings", TgiFaultCode.INVALID_ARGUMENT)
    if bd.extends is not None and not isinstance(bd.extends, LibraryRefType):
        raise TgiError("Invalid extends reference on bus definition", TgiFaultCode.INVALID_ID)
    if bd.extends is None:
        bd.extends = LibraryRefType(vendor=vendor, library=library, name=name, version=version)
    else:
        bd.extends.vendor = vendor
        bd.extends.library = library
        bd.extends.name = name
        bd.extends.version = version
    register_parent(bd.extends, bd, ("extends",), "single")
    return True


def removeBusDefinitionExtends(busDefID: str) -> bool:  # F.7.18.5
    """Remove ``extends`` when present.

    Section: F.7.18.5.

    Args:
        busDefID: Handle to a bus definition element.

    Returns:
        ``True`` if removed; otherwise ``False``.
    """
    bd = _resolve(busDefID)
    if bd.extends is None:
        return False
    if not isinstance(bd.extends, LibraryRefType):
        raise TgiError("Invalid extends reference on bus definition", TgiFaultCode.INVALID_ID)
    register_parent(bd.extends, bd, ("extends",), "single")
    return detach_child_by_handle(get_handle(bd.extends))


def setBusDefinitionDirectConnection(busDefID: str, value: bool) -> bool:  # F.7.18.9
    """Set the ``directConnection`` flag.

    Section: F.7.18.9.

    Args:
        busDefID: Handle to a typed ``BusDefinition`` element.
        value: Boolean direct-connection capability.

    Returns:
        ``True`` after the flag is set.

    Raises:
        TgiError: If the handle or input value is invalid.
    """
    bd = _resolve(busDefID)
    if not isinstance(value, bool):
        raise TgiError("directConnection requires a Boolean value", TgiFaultCode.INVALID_ARGUMENT)
    bd.direct_connection = value
    return True


def removeBusDefinitionDirectConnection(busDefinitionID: str) -> bool:  # nonstandard compatibility helper
    """Reject clearing the required ``directConnection`` element.

    This retained compatibility helper has no Annex F operation. The schema
    requires the element, so clearing it would produce an invalid BusDefinition.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Never returns; raises ``TgiError`` to avoid invalidating the document.
    """
    _resolve(busDefinitionID)
    raise TgiError("directConnection is required and cannot be removed", TgiFaultCode.INVALID_ARGUMENT)


def setBusDefinitionBroadcast(busDefID: str, value: bool) -> bool:  # F.7.18.8
    """Set the ``broadcast`` flag.

    Section: F.7.18.8.

    Args:
        busDefID: Handle to a typed ``BusDefinition`` element.
        value: Boolean broadcast capability.

    Returns:
        ``True`` after the flag is set.

    Raises:
        TgiError: If the handle or input value is invalid.
    """
    bd = _resolve(busDefID)
    if not isinstance(value, bool):
        raise TgiError("broadcast requires a Boolean value", TgiFaultCode.INVALID_ARGUMENT)
    bd.broadcast = value
    return True


def removeBusDefinitionBroadcast(busDefID: str) -> bool:  # F.7.18.3
    """Remove the optional ``broadcast`` flag.

    Section: F.7.18.3.

    Args:
        busDefID: Handle to a bus definition element.

    Returns:
        ``True`` if the optional element was removed; otherwise ``False``.
    """
    bd = _resolve(busDefID)
    if bd.broadcast is not None:
        bd.broadcast = None  # type: ignore[attr-defined]
        return True
    return False


def setBusDefinitionIsAddressable(busDefID: str, value: bool) -> bool:  # F.7.18.11
    """Set the ``isAddressable`` flag.

    Section: F.7.18.11.

    Args:
        busDefID: Handle to a typed ``BusDefinition`` element.
        value: Boolean addressability flag.

    Returns:
        ``True`` after the flag is set.

    Raises:
        TgiError: If the handle or input value is invalid.
    """
    bd = _resolve(busDefID)
    if not isinstance(value, bool):
        raise TgiError("isAddressable requires a Boolean value", TgiFaultCode.INVALID_ARGUMENT)
    bd.is_addressable = value
    return True


def removeBusDefinitionIsAddressable(busDefinitionID: str) -> bool:  # nonstandard compatibility helper
    """Reject clearing the required ``isAddressable`` element.

    This retained compatibility helper has no Annex F operation. The schema
    requires the element, so clearing it would produce an invalid BusDefinition.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        busDefinitionID: Bus definition handle.

    Returns:
        Never returns; raises ``TgiError`` to avoid invalidating the document.
    """
    _resolve(busDefinitionID)
    raise TgiError("isAddressable is required and cannot be removed", TgiFaultCode.INVALID_ARGUMENT)


def setBusDefinitionMaxInitiators(busDefID: str, valueExpression: int | str) -> bool:  # F.7.18.12
    """Set the ``maxInitiators`` expression.

    Section: F.7.18.12.

    Args:
        busDefID: Handle to a bus definition element.
        valueExpression: Unsigned 32-bit integer or SystemVerilog expression source.

    Returns:
        ``True`` after the expression is set.

    Raises:
        TgiError: If the handle or known expression value is invalid.
    """
    bd = _resolve(busDefID)
    _set_unsigned_expression(bd, "max_initiators", valueExpression)
    return True


def removeBusDefinitionMaxInitiators(busDefID: str) -> bool:  # F.7.18.6
    """Remove the ``maxInitiators`` expression.

    Section: F.7.18.6.

    Args:
        busDefID: Handle to a bus definition element.

    Returns:
        ``True`` if an expression was removed; otherwise ``False``.
    """
    bd = _resolve(busDefID)
    expression = bd.max_initiators
    if expression is None:
        return False
    if not isinstance(expression, UnsignedIntExpression):
        raise TgiError("Invalid maxInitiators expression", TgiFaultCode.INVALID_ID)
    register_parent(expression, bd, ("max_initiators",), "single")
    return detach_child_by_handle(get_handle(expression))


def setBusDefinitionMaxTargets(busDefID: str, valueExpression: int | str) -> bool:  # F.7.18.13
    """Set the ``maxTargets`` expression.

    Section: F.7.18.13.

    Args:
        busDefID: Handle to a bus definition element.
        valueExpression: Unsigned 32-bit integer or SystemVerilog expression source.

    Returns:
        ``True`` after the expression is set.

    Raises:
        TgiError: If the handle or known expression value is invalid.
    """
    bd = _resolve(busDefID)
    _set_unsigned_expression(bd, "max_targets", valueExpression)
    return True


def removeBusDefinitionMaxTargets(busDefID: str) -> bool:  # F.7.18.7
    """Remove the ``maxTargets`` expression.

    Section: F.7.18.7.

    Args:
        busDefID: Handle to a bus definition element.

    Returns:
        ``True`` if an expression was removed; otherwise ``False``.
    """
    bd = _resolve(busDefID)
    expression = bd.max_targets
    if expression is None:
        return False
    if not isinstance(expression, UnsignedIntExpression):
        raise TgiError("Invalid maxTargets expression", TgiFaultCode.INVALID_ID)
    register_parent(expression, bd, ("max_targets",), "single")
    return detach_child_by_handle(get_handle(expression))
