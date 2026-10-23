"""Miscellaneous category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.59) and EXTENDED (F.7.60) miscellaneous helper
functions. These cover generic value/expression access, part-select index
manipulation, argument/define/expression setters, VLNV registry operations
and administrative calls (init/end/message/save). Only the standard 2022
API surface (no more, no less) is exported.

Values and expressions retain their generated schema wrappers and source text.
"""

# ruff: noqa: I001
from typing import Any
from collections.abc import Sequence
from dataclasses import fields, is_dataclass
from amal.eda.systemverilog.expression_parser import SvExpressionParser, SvExpressionError
from org.accellera.ipxact.v1685_2022 import (
    ComplexBaseExpression,
    NameValuePairType,
    Value,
    UnsignedIntExpression,
    UnsignedPositiveIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveLongintExpression,
    UnsignedBitExpression,
    UnsignedBitVectorExpression,
    SignedLongintExpression,
)
from .port_map import _xml_text
from . import _miscellaneous_part_select as _part_select_ops
from . import _miscellaneous_registry as _registry_ops
import re
import math
from enum import Enum
from decimal import Decimal, InvalidOperation
from .core import register_parent, get_parent_info

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
)
from amal.utilities.log import logger
from amal.eda.ipxact_de.xml_document import XmlDocument

__all__: list[str] = [
    # BASE (F.7.59)
    "getArgumentValue",
    "getArgumentValueExpression",
    "getArgumentValueID",
    "getBooleanValue",
    "getDefineValue",
    "getDefineValueExpression",
    "getDefineValueID",
    "getExpression",
    "getExpressionIntValue",
    "getExpressionValue",
    "getGroup",
    "getPartSelectIndexIDs",
    "getPartSelectIndices",
    "getPartSelectIndicesExpression",
    "getPartSelectRange",
    "getPartSelectRangeExpression",
    "getPartSelectRangeLeftID",
    "getPartSelectRangeRightID",
    "getValue",
    "getXML",
    # EXTENDED (F.7.60)
    "addPartSelectIndex",
    "init",
    "message",
    "end",
    "isSetElement",
    "registerCatalogVLNVs",
    "registerVLNV",
    "removePartSelectIndex",
    "resolveExpression",
    "save",
    "setArgumentValue",
    "setBooleanValue",
    "setDefineValue",
    "setExpressionValue",
    "setPartSelectRange",
    "setValue",
    "removePartSelectRange",
    "unregisterCatalogVLNVs",
    "unregisterVLNV",
]


# ---------------------------------------------------------------------------
# Helper utilities (non-spec)
# ---------------------------------------------------------------------------

# Administrative session state for F.3.2 (Init / Message / End).
_session_started: bool = False
_session_ended: bool = False
_session_messages: list[tuple[str, str]] = []  # (severity, message)
_session_api_version: str | None = None
_session_failure_mode: str | None = None
_session_init_message: str | None = None


def _require(handle: str) -> Any:
    obj = resolve_handle(handle)
    if obj is None:
        raise TgiError("Invalid handle", TgiFaultCode.INVALID_ID)
    return obj


def _active_session() -> None:
    if not _session_started or _session_ended:
        raise TgiError("Call outside active session", TgiFaultCode.INVALID_ARGUMENT)


def _pair(handle: str) -> NameValuePairType:
    obj = _require(handle)
    if not isinstance(obj, NameValuePairType) or not isinstance(obj.value, Value):
        raise TgiError("Expected argument or define", TgiFaultCode.INVALID_ID)
    return obj


def _expression(handle: str) -> ComplexBaseExpression:
    obj = _require(handle)
    if not isinstance(obj, ComplexBaseExpression):
        raise TgiError("Expected expression element", TgiFaultCode.INVALID_ID)
    return obj


def _text(obj: Any) -> str:
    if isinstance(obj, NameValuePairType):
        obj = obj.value
    value = obj if isinstance(obj, str) else getattr(obj, "value", None)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    if not isinstance(value, str):
        raise TgiError("Expected simple content", TgiFaultCode.INVALID_ID)
    return value


def _set_simple_text(obj: Any, value: str) -> None:
    _xml_text(value)
    old = getattr(obj, "value", None)
    if isinstance(old, str):
        obj.value = value
    elif isinstance(old, bool):
        if value.strip() not in ("true", "false", "1", "0"):
            raise TgiError("Invalid XML Boolean", TgiFaultCode.INVALID_ARGUMENT)
        obj.value = value.strip() in ("true", "1")
    elif isinstance(old, Enum):
        try:
            obj.value = type(old)(value)
        except ValueError as exc:
            raise TgiError("Invalid enumeration", TgiFaultCode.INVALID_ARGUMENT) from exc
    elif type(old) in (int, float, Decimal):
        if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value.strip()):
            raise TgiError("Invalid numeric content", TgiFaultCode.INVALID_ARGUMENT)
        try:
            number = Decimal(value.strip())
            if type(old) is int and number != number.to_integral_value():
                raise ValueError("Expected integer")
            converted = type(old)(number)
            if isinstance(converted, float) and not math.isfinite(converted):
                raise ValueError("Expected finite number")
        except (ValueError, InvalidOperation, OverflowError) as exc:
            raise TgiError("Invalid numeric content", TgiFaultCode.INVALID_ARGUMENT) from exc
        obj.value = converted
    else:
        raise TgiError("Expected simple content element", TgiFaultCode.INVALID_ID)


def _boolean_target(handle: str) -> Any:
    obj = _require(handle)
    if isinstance(obj, bool):
        info = get_parent_info(handle)
        if info is not None and info.container == "single":
            owner = _require(info.parent_handle)
            for attr in info.path:
                owner = getattr(owner, attr)
            return owner
    return obj


def _expression_source(value: str, obj: ComplexBaseExpression) -> str:
    _xml_text(value)
    try:
        result = SvExpressionParser().parse(value)
    except SvExpressionError as exc:
        diagnostics = re.findall(r"error:\s*(.+)", str(exc))
        if not diagnostics or not all("use of undeclared identifier" in item for item in diagnostics):
            raise TgiError("Invalid expression source", TgiFaultCode.INVALID_ARGUMENT) from exc
        return value
    bounds: tuple[int, int | None] | None = None
    if isinstance(obj, (UnsignedPositiveIntExpression, UnsignedIntExpression)):
        bounds = (1 if isinstance(obj, UnsignedPositiveIntExpression) else 0, (1 << 32) - 1)
    elif isinstance(obj, (UnsignedPositiveLongintExpression, UnsignedLongintExpression)):
        bounds = (1 if isinstance(obj, UnsignedPositiveLongintExpression) else 0, (1 << 64) - 1)
    elif isinstance(obj, UnsignedBitExpression):
        bounds = (0, 1)
    elif isinstance(obj, UnsignedBitVectorExpression):
        bounds = (0, None)
    elif isinstance(obj, SignedLongintExpression):
        bounds = (-(1 << 63), (1 << 63) - 1)
    if bounds is not None:
        try:
            number = result.as_python()
        except SvExpressionError as exc:
            raise TgiError("Expected known numeric constant", TgiFaultCode.INVALID_ARGUMENT) from exc
        minimum, maximum = bounds
        if type(number) is not int or number < minimum or (maximum is not None and number > maximum):
            raise TgiError("Expression outside schema bounds", TgiFaultCode.INVALID_ARGUMENT)
        declared_min, declared_max = getattr(obj, "minimum", None), getattr(obj, "maximum", None)
        if (declared_min is not None and number < declared_min) or (declared_max is not None and number > declared_max):
            raise TgiError("Expression outside declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _evaluate(source: str) -> int | float:
    try:
        return SvExpressionParser().evaluate(source)
    except SvExpressionError as exc:
        raise TgiError("Cannot evaluate constant expression", TgiFaultCode.INVALID_ARGUMENT) from exc


def _evaluated_text(source: str, constants: dict[str, str] | None = None) -> str:
    try:
        result = SvExpressionParser(constants).parse(source)
        try:
            return str(result.as_python())
        except SvExpressionError:
            return result.literal
    except SvExpressionError as exc:
        raise TgiError("Cannot evaluate constant expression", TgiFaultCode.INVALID_ARGUMENT) from exc


def _log_with_severity(severity: str, text: str) -> None:
    """Log ``text`` using loguru at a level matching ``severity``.

    Accepts common aliases case-insensitively: TRACE, DEBUG, INFO,
    SUCCESS, WARN/WARNING, ERROR/ERR, CRITICAL/FATAL.
    Unknown levels fall back to INFO.
    """
    lvl = (severity or "").strip().upper()
    if lvl == "TRACE":
        logger.trace(text)
    elif lvl == "DEBUG":
        logger.debug(text)
    elif lvl in ("SUCCESS",):
        logger.success(text)
    elif lvl in ("WARN", "WARNING"):
        logger.warning(text)
    elif lvl in ("ERROR", "ERR"):
        logger.error(text)
    elif lvl in ("CRITICAL", "FATAL"):
        logger.critical(text)
    else:
        logger.info(text)


# ---------------------------------------------------------------------------
# BASE (F.7.59)
# ---------------------------------------------------------------------------


def getArgumentValue(argumentID: str) -> str:
    """Return the source text of the owned value element.

    Section: F.7.59.1.

    Args:
        argumentID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _text(_pair(argumentID).value)


def getArgumentValueExpression(argumentID: str) -> str:
    """Return the source text of the owned value element.

    Section: F.7.59.2.

    Args:
        argumentID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _text(_pair(argumentID).value)


def getArgumentValueID(argumentID: str) -> str:
    """Return the handle of the owned value element.

    Section: F.7.59.3.

    Args:
        argumentID: Standard operation input.

    Returns:
        The standard operation result.
    """
    parent = _pair(argumentID)
    register_parent(parent.value, parent, ("value",), "single")
    return get_handle(parent.value)


def getBooleanValue(elementID: str) -> bool:
    """Return an XML Schema Boolean value.

    Section: F.7.59.4.

    Args:
        elementID: Standard operation input.

    Returns:
        The standard operation result.
    """
    obj = _boolean_target(elementID)
    value = obj if isinstance(obj, bool) else getattr(obj, "value", None)
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip() in ("true", "false", "1", "0"):
        return value.strip() in ("true", "1")
    raise TgiError("Invalid XML Boolean", TgiFaultCode.INVALID_ARGUMENT)


def getDefineValue(defineID: str) -> str:
    """Return the source text of the owned value element.

    Section: F.7.59.5.

    Args:
        defineID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _text(_pair(defineID).value)


def getDefineValueExpression(defineID: str) -> str:
    """Return the source text of the owned value element.

    Section: F.7.59.6.

    Args:
        defineID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _text(_pair(defineID).value)


def getDefineValueID(defineID: str) -> str:
    """Return the handle of the owned value element.

    Section: F.7.59.7.

    Args:
        defineID: Standard operation input.

    Returns:
        The standard operation result.
    """
    parent = _pair(defineID)
    register_parent(parent.value, parent, ("value",), "single")
    return get_handle(parent.value)


def getExpression(expressionID: str) -> str:
    """Return the specified element content.

    Section: F.7.59.8.

    Args:
        expressionID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _text(_expression(expressionID))


def getExpressionIntValue(expressionID: str) -> int:
    """Return the specified element content.

    Section: F.7.59.9.

    Args:
        expressionID: Standard operation input.

    Returns:
        The standard operation result.
    """
    value = _evaluate(_text(_expression(expressionID)))
    if not isinstance(value, int) or not -(1 << 63) <= value < (1 << 63):
        raise TgiError("Expression is outside TGI Long bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def getExpressionValue(expressionID: str) -> str:
    """Return the specified element content.

    Section: F.7.59.10.

    Args:
        expressionID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _evaluated_text(_text(_expression(expressionID)))


def getGroup(groupID: str) -> str:
    """Return the specified element content.

    Section: F.7.59.11.

    Args:
        groupID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _text(_require(groupID))


def getPartSelectIndexIDs(partSelectID: str) -> list[str]:
    """getPartSelectIndexIDs on the specified schema content.

    Section: F.7.59.12.

    Args:
        partSelectID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _part_select_ops.getPartSelectIndexIDs(partSelectID)


def getPartSelectIndices(partSelectID: str) -> list[int]:
    """getPartSelectIndices on the specified schema content.

    Section: F.7.59.13.

    Args:
        partSelectID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _part_select_ops.getPartSelectIndices(partSelectID)


def getPartSelectIndicesExpression(partSelectID: str) -> list[str]:
    """getPartSelectIndicesExpression on the specified schema content.

    Section: F.7.59.14.

    Args:
        partSelectID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _part_select_ops.getPartSelectIndicesExpression(partSelectID)


def getPartSelectRange(partSelectID: str) -> list[int] | None:
    """getPartSelectRange on the specified schema content.

    Section: F.7.59.15.

    Args:
        partSelectID: Standard operation input.

    Returns:
        The operation result; absent optional schema content returns None.
    """
    return _part_select_ops.getPartSelectRange(partSelectID)


def getPartSelectRangeExpression(partSelectID: str) -> list[str] | None:
    """getPartSelectRangeExpression on the specified schema content.

    Section: F.7.59.16.

    Args:
        partSelectID: Standard operation input.

    Returns:
        The operation result; absent optional schema content returns None.
    """
    return _part_select_ops.getPartSelectRangeExpression(partSelectID)


def getPartSelectRangeLeftID(partSelectID: str) -> str | None:
    """getPartSelectRangeLeftID on the specified schema content.

    Section: F.7.59.17.

    Args:
        partSelectID: Standard operation input.

    Returns:
        The operation result; absent optional schema content returns None.
    """
    return _part_select_ops.getPartSelectRangeLeftID(partSelectID)


def getPartSelectRangeRightID(partSelectID: str) -> str | None:
    """getPartSelectRangeRightID on the specified schema content.

    Section: F.7.59.18.

    Args:
        partSelectID: Standard operation input.

    Returns:
        The operation result; absent optional schema content returns None.
    """
    return _part_select_ops.getPartSelectRangeRightID(partSelectID)


def getValue(elementID: str) -> str:
    """Return the specified element content.

    Section: F.7.59.19.

    Args:
        elementID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _text(_require(elementID))


def getXML(elementID: str) -> str:
    """Return the specified element content.

    Section: F.7.59.20.

    Args:
        elementID: Standard operation input.

    Returns:
        The standard operation result.
    """
    try:
        return XmlDocument.serializer().render(_require(elementID))
    except TgiError:
        raise
    except Exception as exc:
        raise TgiError("Cannot serialize element", TgiFaultCode.INVALID_ARGUMENT) from exc


# ---------------------------------------------------------------------------
# EXTENDED (F.7.60)
# ---------------------------------------------------------------------------


def addPartSelectIndex(partSelectID: str, value: str) -> str:
    """addPartSelectIndex on the specified schema content.

    Section: F.7.60.1.

    Args:
        partSelectID: Standard operation input.
        value: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _part_select_ops.addPartSelectIndex(partSelectID, value)


def init(apiVersion: str, failureMode: str, message: str) -> bool:
    """Initialize the generator administrative session.

    Section: F.7.60.3.

    Args:
        apiVersion: Standard operation input.
        failureMode: Standard operation input.
        message: Standard operation input.

    Returns:
        The standard operation result.
    """
    global _session_started, _session_ended, _session_api_version, _session_failure_mode, _session_init_message
    _xml_text(apiVersion)
    _xml_text(message)
    if failureMode not in ("fail", "error", "warning"):
        raise TgiError("Invalid failure mode", TgiFaultCode.INVALID_ARGUMENT)
    if _session_started and not _session_ended:
        raise TgiError("Session already initialized", TgiFaultCode.ALREADY_EXISTS)
    _session_started, _session_ended = True, False
    _session_api_version, _session_failure_mode, _session_init_message = apiVersion, failureMode, message
    _session_messages.clear()
    _session_messages.append(("info", message))
    _log_with_severity("info", message)
    return True


def end(genStatus: int, message: str) -> int:
    """End the session and return zero when the DE accepts the termination.

    Section: F.7.60.2.

    Args:
        genStatus: Standard operation input.
        message: Standard operation input.

    Returns:
        The standard operation result.
    """
    global _session_ended
    _active_session()
    if isinstance(genStatus, bool) or not isinstance(genStatus, int) or not -(1 << 63) <= genStatus < (1 << 63):
        raise TgiError("Expected TGI Long status", TgiFaultCode.INVALID_ARGUMENT)
    _xml_text(message)
    _session_messages.append(("info", message))
    _log_with_severity("info", message)
    _session_ended = True
    return 0


def message(severity: str, message: str) -> bool:
    """Record a generator status message during an active session.

    Section: F.7.60.5.

    Args:
        severity: Standard operation input.
        message: Standard operation input.

    Returns:
        The standard operation result.
    """
    _active_session()
    _xml_text(severity)
    _xml_text(message)
    _session_messages.append((severity, message))
    _log_with_severity(severity, message)
    return True


def isSetElement(elementContainerID: str, elementName: str) -> bool:
    """Return whether the named child element is present.

    Section: F.7.60.4.

    Args:
        elementContainerID: Standard operation input.
        elementName: Standard operation input.

    Returns:
        The standard operation result.
    """
    obj = _require(elementContainerID)
    _xml_text(elementName)
    if not is_dataclass(obj):
        raise TgiError("Expected an element container", TgiFaultCode.INVALID_ID)
    for field in fields(obj):
        if field.metadata.get("type") in ("Element", "Elements") and (
            field.metadata.get("name", field.name) == elementName or field.name == elementName
        ):
            value = getattr(obj, field.name)
            return value is not None and (not isinstance(value, (list, tuple)) or bool(value))
    return False


def registerCatalogVLNVs(catalogID: str) -> bool:
    """registerCatalogVLNVs on the specified schema content.

    Section: F.7.60.6.

    Args:
        catalogID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _registry_ops.registerCatalogVLNVs(catalogID)


def registerVLNV(fileName: str, replace: bool) -> bool:
    """registerVLNV on the specified schema content.

    Section: F.7.60.7.

    Args:
        fileName: Standard operation input.
        replace: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _registry_ops.registerVLNV(fileName, replace)


def removePartSelectIndex(indexID: str) -> bool:
    """removePartSelectIndex on the specified schema content.

    Section: F.7.60.8.

    Args:
        indexID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _part_select_ops.removePartSelectIndex(indexID)


def resolveExpression(expression: str, values: Sequence[str]) -> str:
    """Evaluate an expression using the supplied constant name/value pairs.

    Section: F.7.60.9.

    Args:
        expression: Standard operation input.
        values: Standard operation input.

    Returns:
        The standard operation result.
    """
    _xml_text(expression)
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TgiError("Expected name/value pairs", TgiFaultCode.INVALID_ARGUMENT)
    constants: dict[str, str] = {}
    for pair in values:
        _xml_text(pair)
        name, separator, source = pair.partition("=")
        name = name.strip()
        if not separator or name in constants:
            raise TgiError("Invalid or duplicate constant pair", TgiFaultCode.INVALID_ARGUMENT)
        try:
            SvExpressionParser().parse(source)
        except SvExpressionError as exc:
            raise TgiError("Value must be a constant", TgiFaultCode.INVALID_ARGUMENT) from exc
        constants[name] = source
    return _evaluated_text(expression, constants)


def save() -> bool:
    """save on the specified schema content.

    Section: F.7.60.10.

    Args:
        None.

    Returns:
        The standard operation result.
    """
    return _registry_ops.save()


def setArgumentValue(argumentID: str, value: str) -> bool:
    """Assign source content while preserving the schema wrapper.

    Section: F.7.60.11.

    Args:
        argumentID: Standard operation input.
        value: Standard operation input.

    Returns:
        The standard operation result.
    """
    _pair(argumentID).value.value = _xml_text(value)
    return True


def setBooleanValue(elementID: str, value: bool) -> bool:
    """Assign an XML Boolean to its owning schema element.

    Section: F.7.60.12.

    Args:
        elementID: Standard operation input.
        value: Standard operation input.

    Returns:
        The standard operation result.
    """
    if not isinstance(value, bool):
        raise TgiError("Expected Boolean", TgiFaultCode.INVALID_ARGUMENT)
    obj = _boolean_target(elementID)
    if isinstance(obj, bool):
        info = get_parent_info(elementID)
        if info is None or info.container != "single":
            raise TgiError("Boolean has no owning element", TgiFaultCode.INVALID_ID)
        owner = _require(info.parent_handle)
        for attr in info.path[:-1]:
            owner = getattr(owner, attr)
        setattr(owner, info.path[-1], value)
    else:
        old = getattr(obj, "value", None)
        getBooleanValue(elementID)
        obj.value = value if isinstance(old, bool) else ("true" if value else "false")
    return True


def setDefineValue(argumentID: str, value: str) -> bool:
    """Assign source content while preserving the schema wrapper.

    Section: F.7.60.13.

    Args:
        argumentID: Standard operation input.
        value: Standard operation input.

    Returns:
        The standard operation result.
    """
    _pair(argumentID).value.value = _xml_text(value)
    return True


def setExpressionValue(expressionID: str, value: str) -> bool:
    """Assign source content while preserving the schema wrapper.

    Section: F.7.60.14.

    Args:
        expressionID: Standard operation input.
        value: Standard operation input.

    Returns:
        The standard operation result.
    """
    obj = _expression(expressionID)
    obj.value = _expression_source(value, obj)
    return True


def setPartSelectRange(partSelectID: str, left: str, right: str) -> bool:
    """setPartSelectRange on the specified schema content.

    Section: F.7.60.15.

    Args:
        partSelectID: Standard operation input.
        left: Standard operation input.
        right: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _part_select_ops.setPartSelectRange(partSelectID, left, right)


def setValue(elementID: str, value: str) -> bool:
    """Assign source content while preserving the schema wrapper.

    Section: F.7.60.16.

    Args:
        elementID: Standard operation input.
        value: Standard operation input.

    Returns:
        The standard operation result.
    """
    obj = _require(elementID)
    if isinstance(obj, NameValuePairType):
        obj = obj.value
    if isinstance(obj, ComplexBaseExpression):
        obj.value = _xml_text(value)
    else:
        _set_simple_text(obj, value)
    return True


def removePartSelectRange(partSelectID: str) -> bool:
    """removePartSelectRange on the specified schema content.

    Section: F.7.60.17.

    Args:
        partSelectID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _part_select_ops.removePartSelectRange(partSelectID)


def unregisterCatalogVLNVs(catalogID: str) -> bool:
    """unregisterCatalogVLNVs on the specified schema content.

    Section: F.7.60.18.

    Args:
        catalogID: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _registry_ops.unregisterCatalogVLNVs(catalogID)


def unregisterVLNV(VLNV: Sequence[str]) -> bool:
    """unregisterVLNV on the specified schema content.

    Section: F.7.60.19.

    Args:
        VLNV: Standard operation input.

    Returns:
        The standard operation result.
    """
    return _registry_ops.unregisterVLNV(VLNV)
