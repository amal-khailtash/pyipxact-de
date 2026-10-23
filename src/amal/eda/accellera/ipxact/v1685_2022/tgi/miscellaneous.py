"""Miscellaneous category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.59) and EXTENDED (F.7.60) miscellaneous helper
functions. These cover generic value/expression access, part-select index
manipulation, argument/define/expression setters, VLNV registry operations
and administrative calls (init/end/message/save). Only the standard 2022
API surface (no more, no less) is exported.

Where the underlying schema objects have simple content, generic access
uses their ``value`` attributes with strict fault code semantics. Argument
and define values use typed generated Value wrappers; expression source is
stored in simple content. Values, expressions and part-select edits retain
their generated schema wrappers and metadata.
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
from ._expressions import _xml_text
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

# Administrative session state for F.3.2 (Init / Message / End).  This is a
# lightweight in-memory representation for current DE embedding scenarios.
# The standard requires Init first and End last; Message is only valid
# between them. The administrative calls enforce this session ordering;
# ordinary model operations do not establish or check a transport session.
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
    # Simple content objects may themselves have a value attribute.
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


def getArgumentValue(argumentID: str) -> str:  # F.7.59.1
    """Return argument value as the source string of its value element.

    Section: F.7.59.1.

    The generated Value wrapper and its source text are retained; this getter does not evaluate the source.

    Args:
        argumentID: Handle to the argument element.

    Returns:
        The value element's source string.
    """
    return getValue(getArgumentValueID(argumentID))


def getArgumentValueExpression(argumentID: str) -> str:  # F.7.59.2
    """Return associated expression string for an argument if present.

    Section: F.7.59.2.

    Expression source is stored in the owned Value element's simple content.

    Args:
        argumentID: Handle to the argument element.

    Returns:
        The value element's expression source string.
    """
    return getArgumentValue(argumentID)


def getArgumentValueID(argumentID: str) -> str:  # F.7.59.3
    """Return handle to the value element owned by the argument.

    Section: F.7.59.3.

    Args:
        argumentID: Handle to the argument element.

    Returns:
        Handle to the owned Value element.
    """
    parent = _pair(argumentID)
    register_parent(parent.value, parent, ("value",), "single")
    return get_handle(parent.value)


def getBooleanValue(elementID: str) -> bool:  # F.7.59.4
    """Return boolean simple content value.

    Section: F.7.59.4.

    Args:
        elementID: Handle to the IP-XACT element.

    Returns:
        The XML Schema Boolean value.
    """
    obj = _boolean_target(elementID)
    value = obj if isinstance(obj, bool) else getattr(obj, "value", None)
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip() in ("true", "false", "1", "0"):
        return value.strip() in ("true", "1")
    raise TgiError("Invalid XML Boolean", TgiFaultCode.INVALID_ARGUMENT)


def getDefineValue(defineID: str) -> str:  # F.7.59.5
    """Return define value string.

    Section: F.7.59.5.

    Args:
        defineID: Handle to the define element.

    Returns:
        The define value string.
    """
    return getValue(getDefineValueID(defineID))


def getDefineValueExpression(defineID: str) -> str:  # F.7.59.6
    """Return expression for define value.

    Section: F.7.59.6.

    Expression source is stored in the owned Value element's simple content.

    Args:
        defineID: Handle to the define element.

    Returns:
        The define value's expression source string.
    """
    return getDefineValue(defineID)


def getDefineValueID(defineID: str) -> str:  # F.7.59.7
    """Return handle to the value element owned by the define.

    Section: F.7.59.7.

    Args:
        defineID: Handle to the define element.

    Returns:
        Handle to the owned Value element.
    """
    return getArgumentValueID(defineID)


def getExpression(expressionID: str) -> str:  # F.7.59.8
    """Return raw expression text.

    Section: F.7.59.8.

    Args:
        expressionID: Handle to the expression element.

    Returns:
        The raw expression text.
    """
    return _text(_expression(expressionID))


def getExpressionIntValue(expressionID: str) -> int:  # F.7.59.9
    """Return the evaluated integer value of an expression.

    Section: F.7.59.9.

    Uses SvExpressionParser for SystemVerilog constant evaluation. Unresolved, non-integral and out-of-range values
    raise TgiError; the result must fit the signed 64-bit TGI Long domain.

    Args:
        expressionID: Handle to the expression element.

    Returns:
        The evaluated integer as a TGI Long.
    """
    value = _evaluate(getExpression(expressionID))
    if not isinstance(value, int) or not -(1 << 63) <= value < (1 << 63):
        raise TgiError("Expression is outside TGI Long bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def getExpressionValue(expressionID: str) -> str:  # F.7.59.10
    """Return evaluated value as a string.

    Section: F.7.59.10.

    Uses SvExpressionParser for constant evaluation. Numeric constants are returned as strings; other constant values
    retain the parser's literal representation. Unresolved expressions raise TgiError.

    Args:
        expressionID: Handle to the expression element.

    Returns:
        The evaluated constant as a string.
    """
    return _evaluated_text(getExpression(expressionID))


def getGroup(groupID: str) -> str:  # F.7.59.11
    """Return the group name defined on the given group element.

    Section: F.7.59.11.

    Args:
        groupID: Handle to the group element.

    Returns:
        The group name.
    """
    return getValue(groupID)


def getPartSelectIndexIDs(partSelectID: str) -> list[str]:  # F.7.59.12
    """Return handles of each index element in a partSelect.

    Section: F.7.59.12.

    Traverses generated Indices/Index children in the partSelect range_or_indices choice and registers their ownership.

    Args:
        partSelectID: Handle to the partSelect element.

    Returns:
        Index handles in source order, or an empty list when no indices are defined.
    """
    return _part_select_ops.getPartSelectIndexIDs(partSelectID)


def getPartSelectIndices(partSelectID: str) -> list[int]:  # F.7.59.13
    """Return concrete integer indices for part select.

    Section: F.7.59.13.

    Uses SvExpressionParser for constant expressions. Unresolved or out-of-domain indices raise TgiError.

    Args:
        partSelectID: Handle to the partSelect element.

    Returns:
        Evaluated unsigned 32-bit indices in source order.
    """
    return _part_select_ops.getPartSelectIndices(partSelectID)


def getPartSelectIndicesExpression(partSelectID: str) -> list[str]:  # F.7.59.14
    """Return raw expressions/values for each index.

    Section: F.7.59.14.

    Args:
        partSelectID: Handle to the partSelect element.

    Returns:
        Index source expressions in source order.
    """
    return _part_select_ops.getPartSelectIndicesExpression(partSelectID)


def getPartSelectRange(partSelectID: str) -> list[int] | None:  # F.7.59.15
    """Return [left, right] numeric range, or None when no range is defined.

    Section: F.7.59.15.

    Uses SvExpressionParser for constant expressions. Unresolved or out-of-domain bounds raise TgiError.

    Args:
        partSelectID: Handle to the partSelect element.

    Returns:
        [left, right] evaluated unsigned 32-bit bounds, or None when absent.
    """
    return _part_select_ops.getPartSelectRange(partSelectID)


def getPartSelectRangeExpression(partSelectID: str) -> list[str] | None:  # F.7.59.16
    """Return [leftExpr, rightExpr] raw expression/value strings, or None when no range is defined.

    Section: F.7.59.16.

    Args:
        partSelectID: Handle to the partSelect element.

    Returns:
        [left, right] source expressions, or None when absent.
    """
    return _part_select_ops.getPartSelectRangeExpression(partSelectID)


def getPartSelectRangeLeftID(partSelectID: str) -> str | None:  # F.7.59.17
    """Return handle of left expression element if present.

    Section: F.7.59.17.

    Args:
        partSelectID: Handle to the partSelect element.

    Returns:
        Handle to the left bound element, or None when absent.
    """
    return _part_select_ops.getPartSelectRangeLeftID(partSelectID)


def getPartSelectRangeRightID(partSelectID: str) -> str | None:  # F.7.59.18
    """Return handle of right expression element if present.

    Section: F.7.59.18.

    Args:
        partSelectID: Handle to the partSelect element.

    Returns:
        Handle to the right bound element, or None when absent.
    """
    return _part_select_ops.getPartSelectRangeRightID(partSelectID)


def getValue(elementID: str) -> str:  # F.7.59.19
    """Return generic simple content value.

    Section: F.7.59.19.

    Args:
        elementID: Handle to the IP-XACT element.

    Returns:
        The simple content as a string.
    """
    return _text(_require(elementID))


def getXML(elementID: str) -> str:  # F.7.59.20
    """Serialize an element to XML using xsdata's ``XmlSerializer``.

    Section: F.7.59.20. Uses the project-wide serializer configuration
    (indentation two spaces). If the element cannot be resolved, TgiError
    is raised with INVALID_ID. Errors during serialization raise TgiError
    with INVALID_ARGUMENT.

    Args:
        elementID: Handle to the IP-XACT element.

    Returns:
        The serialized XML fragment.
    """
    try:
        return XmlDocument.serializer().render(_require(elementID))
    except TgiError:
        raise
    except Exception as exc:  # defensive: surface as TGI error
        raise TgiError("Cannot serialize element", TgiFaultCode.INVALID_ARGUMENT) from exc


# ---------------------------------------------------------------------------
# EXTENDED (F.7.60)
# ---------------------------------------------------------------------------


def addPartSelectIndex(partSelectID: str, value: str) -> str:  # F.7.60.1
    """Add a new index entry to partSelect returning its handle.

    Section: F.7.60.1.

    Args:
        partSelectID: Handle to the partSelect element.
        value: Source value to assign.

    Returns:
        Handle to the new Index element.
    """
    return _part_select_ops.addPartSelectIndex(partSelectID, value)


def init(apiVersion: str, failureMode: str, message: str) -> bool:  # F.7.60.3
    """Initialize a new TGI administrative session (Init command).

    Section: F.7.60.3.

    Section F.3.2 specifies Init as the required first administrative
    message from the generator to the DE. F.7.60.3 requires an API version,
    compatibility failure mode and message, with a boolean return status.
    These values are recorded for the active session.

    Args:
        apiVersion: API version string requested/advertised by the
            generator (e.g. "1685-2022"). Stored for later inspection.
        failureMode: Compatibility failure mode: "fail", "error" or
            "warning". The value is validated and stored.
        message: Initial status line to record and display with informational
            severity. The message is required; its text may be empty.

    Raises:
        TgiError: If a session is already active (no intervening End),
            fault code ``ALREADY_EXISTS``; or if an input is invalid,
            fault code ``INVALID_ARGUMENT``.

    Returns:
        True when initialization succeeds.
    """
    global _session_started, _session_ended, _session_api_version, _session_failure_mode, _session_init_message
    _xml_text(apiVersion)
    _xml_text(message)
    if failureMode not in ("fail", "error", "warning"):
        raise TgiError("Invalid failure mode", TgiFaultCode.INVALID_ARGUMENT)
    if _session_started and not _session_ended:
        raise TgiError("Session already initialized", TgiFaultCode.ALREADY_EXISTS)
    # Reset state for new lifecycle
    _session_started, _session_ended = True, False
    _session_api_version, _session_failure_mode, _session_init_message = apiVersion, failureMode, message
    _session_messages.clear()
    _session_messages.append(("info", message))
    # Log initialization message
    _log_with_severity("info", message)
    return True


def end(genStatus: int, message: str) -> int:  # F.7.60.2
    """Terminate the active TGI administrative session.

    Section: F.7.60.2.

    Implements the End administrative command defined in section F.3.2.
    According to the specification this shall be the final message sent
    from the generator to the DE and conveys that the generator no longer
    requires the DE to listen for further TGI calls. The IEEE text also
    notes that a generator is not strictly required to terminate after
    sending End.

    Ordering rules enforced:
        * ``init()`` must have been called successfully first; otherwise a
            ``TgiError`` is raised with ``INVALID_ARGUMENT``.
        * The session must still be active. Repeated ``end()`` calls after
            termination raise ``TgiError`` with ``INVALID_ARGUMENT``.

    Side effects:
        * Records and displays the generator's termination message.
        * Marks the session as ended. Additional administrative calls that
            depend on an open session (``message``) will raise.

    Args:
        genStatus: TGI Long status indicator from the generator. Non-zero
            implies a generator error; this is separate from the DE status.
        message: Message that the DE may display to the user.

    Raises:
        TgiError: If the session is not active, genStatus is not a signed
            64-bit integer or message is invalid, with ``INVALID_ARGUMENT``.

    Returns:
        Zero when the DE accepts termination. A non-zero DE status would
        indicate a DE error; generator errors are supplied through genStatus.
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


def message(severity: str, message: str) -> bool:  # F.7.60.5
    """Record a status message (Message command) for the active session.

    Section: F.7.60.5.

    Section F.3.2 defines Message as a way for a generator to convey
    status to the user. This implementation captures both a required
    severity tag and the message text, storing them in the session log.

    Args:
        severity: Free-form severity level (e.g. ``INFO``, ``WARN``,
            ``ERROR``). No severity enumeration is enforced; callers may
            adopt any taxonomy. Known levels are mapped to the logger.
        message: Message body. Empty strings are recorded and accepted.

    Raises:
        TgiError: If called before ``init`` or after ``end`` with fault
            code ``INVALID_ARGUMENT``, or if an input is invalid.

    Returns:
        True if the message is accepted.
    """
    _active_session()
    _xml_text(severity)
    _xml_text(message)
    _session_messages.append((severity, message))
    _log_with_severity(severity, message)
    return True


def isSetElement(elementContainerID: str, elementName: str) -> bool:  # F.7.60.4
    """Return True if the named child element is set on its container.

    Section: F.7.60.4.

    Args:
        elementContainerID: Handle to the parent element container.
        elementName: XML name of the child element to check.

    Returns:
        True when the named child element is present; False otherwise.
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


def registerCatalogVLNVs(catalogID: str) -> bool:  # F.7.60.6
    """Register the VLNVs of the top-level documents referenced by a catalog.

    Section: F.7.60.6.

    Catalog file references are resolved relative to the registered catalog file. Each referenced file must contain
    a supported 2022 top-level document with the declared VLNV and document type. All references are checked before
    registration; existing registrations or conflicting references return False.

    Args:
        catalogID: Handle to the registered catalog document.

    Returns:
        True when registration succeeds; False otherwise.
    """
    return _registry_ops.registerCatalogVLNVs(catalogID)


def registerVLNV(fileName: str, replace: bool) -> bool:  # F.7.60.7
    """Register a single VLNV for a top-level document loaded from a file.

    Section: F.7.60.7.

    Accepts a filename and a Boolean replace flag. Only supported IEEE 1685-2022 top-level roots are registered.
    An existing VLNV returns False unless replace is True; loading or registration failures return False.

    Args:
        fileName: Filename of the top-level IP-XACT document to register.
        replace: Whether an existing VLNV registration may be replaced.

    Returns:
        True when registration succeeds; False otherwise.
    """
    return _registry_ops.registerVLNV(fileName, replace)


def removePartSelectIndex(indexID: str) -> bool:  # F.7.60.8
    """Remove an index element from its parent partSelect list.

    Section: F.7.60.8.

    Detaches the owned Index, invalidates its handle and removes an empty Indices holder.

    Args:
        indexID: Handle to the index element to remove.

    Returns:
        True when the owned index is removed.
    """
    return _part_select_ops.removePartSelectIndex(indexID)


def resolveExpression(expression: str, values: Sequence[str]) -> str:  # F.7.60.9
    """Resolve an expression using the supplied constant name/value pairs.

    Section: F.7.60.9.

    Each values entry has the form "name = value"; the value must be a self-contained SystemVerilog constant.
    SvExpressionParser evaluates the expression in that constant environment. Invalid or duplicate pairs raise TgiError.

    Args:
        expression: SystemVerilog expression to evaluate.
        values: Constant assignments in "name = value" form.

    Returns:
        The evaluated constant as a string.
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


def save() -> bool:  # F.7.60.10
    """Persist current model state to the registered document files after XML validation.

    Section: F.7.60.10.

    Uses the project-wide serializer configuration. All registered top-level documents are staged and schema-validated
    before their files are replaced. File permissions are preserved. Invalid documents, missing source files or
    persistence failures return False.

    Args:
        None.

    Returns:
        True when persistence succeeds; False otherwise.
    """
    return _registry_ops.save()


def setArgumentValue(argumentID: str, value: str) -> bool:  # F.7.60.11
    """Set argument value while preserving its owned value element.

    Section: F.7.60.11.

    Args:
        argumentID: Handle to the argument element.
        value: Source value to assign.

    Returns:
        True when the value is assigned successfully.
    """
    return setValue(getArgumentValueID(argumentID), value)


def setBooleanValue(elementID: str, value: bool) -> bool:  # F.7.60.12
    """Set boolean value on the given element or its registered owning field.

    Section: F.7.60.12.

    Args:
        elementID: Handle to the IP-XACT element.
        value: Boolean value to assign.

    Returns:
        True when the value is assigned successfully.
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


def setDefineValue(argumentID: str, value: str) -> bool:  # F.7.60.13
    """Set define value while preserving its owned value element.

    Section: F.7.60.13.

    Args:
        argumentID: Handle to the define element; Annex F.7.60.13 retains the name argumentID.
        value: Source value to assign.

    Returns:
        True when the value is assigned successfully.
    """
    return setValue(getDefineValueID(argumentID), value)


def setExpressionValue(expressionID: str, value: str) -> bool:  # F.7.60.14
    """Set expression text while preserving the expression element.

    Section: F.7.60.14.

    Malformed constant expressions and known intrinsic/declared bound violations are rejected before mutation.
    Unresolved identifiers remain source text for later configured evaluation.

    Args:
        expressionID: Handle to the expression element.
        value: Source value to assign.

    Returns:
        True when the value is assigned successfully.
    """
    obj = _expression(expressionID)
    obj.value = _expression_source(value, obj)
    return True


def setPartSelectRange(partSelectID: str, left: str, right: str) -> bool:  # F.7.60.15
    """Set [left, right] range expressions while preserving existing bound elements.

    Section: F.7.60.15.

    Sibling indices and bound metadata are retained. The combined choice follows schema child order, indices then range.

    Args:
        partSelectID: Handle to the partSelect element.
        left: Source expression for the left range bound.
        right: Source expression for the right range bound.

    Returns:
        True when the value is assigned successfully.
    """
    return _part_select_ops.setPartSelectRange(partSelectID, left, right)


def setValue(elementID: str, value: str) -> bool:  # F.7.60.16
    """Set generic value simple content.

    Section: F.7.60.16.

    Args:
        elementID: Handle to the IP-XACT element.
        value: Source value to assign.

    Returns:
        True when the value is assigned successfully.
    """
    obj = _require(elementID)
    if isinstance(obj, NameValuePairType):
        obj = obj.value
    if isinstance(obj, ComplexBaseExpression):
        obj.value = _xml_text(value)
    else:
        _set_simple_text(obj, value)
    return True


def removePartSelectRange(partSelectID: str) -> bool:  # F.7.60.17
    """Remove range (left/right) elements.

    Section: F.7.60.17.

    Invalidates the removed range and its bound handles, while retaining sibling indices.

    Args:
        partSelectID: Handle to the partSelect element.

    Returns:
        True when a range is removed; False when no range is defined.
    """
    return _part_select_ops.removePartSelectRange(partSelectID)


def unregisterCatalogVLNVs(catalogID: str) -> bool:  # F.7.60.18
    """Unregister the VLNVs declared by the given catalog.

    Section: F.7.60.18.

    Uses the catalog's declared VLNVs; referenced files need not still exist.

    Args:
        catalogID: Handle to the registered catalog document.

    Returns:
        True when the catalog declarations are processed successfully; False otherwise.
    """
    return _registry_ops.unregisterCatalogVLNVs(catalogID)


def unregisterVLNV(VLNV: Sequence[str]) -> bool:  # F.7.60.19
    """Unregister a single VLNV mapping.

    Section: F.7.60.19.

    Args:
        VLNV: Four strings identifying vendor, library, name and version.

    Returns:
        True when the VLNV is unregistered; False when it was not registered or the input is invalid.
    """
    return _registry_ops.unregisterVLNV(VLNV)
