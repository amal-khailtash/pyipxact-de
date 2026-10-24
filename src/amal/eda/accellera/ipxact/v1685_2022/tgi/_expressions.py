"""XML source, unsigned and real constant-expression validation for TGI models."""

import math
import re

from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser
from org.accellera.ipxact.v1685_2022.complex_base_expression import ComplexBaseExpression
from org.accellera.ipxact.v1685_2022.complex_tied_value_expression import ComplexTiedValueExpression
from org.accellera.ipxact.v1685_2022.real_expression import RealExpression

from .core import TgiError, TgiFaultCode

_UINT_MAX = (1 << 32) - 1


def _xml_text(value: str) -> str:
    from lxml import etree

    if not isinstance(value, str):
        raise TgiError("Expected expression string", TgiFaultCode.INVALID_ARGUMENT)
    try:
        etree.Element("text").text = value
    except (ValueError, TypeError) as error:
        raise TgiError("Invalid XML text", TgiFaultCode.INVALID_ARGUMENT) from error
    return value


def _undeclared(error: SvExpressionError) -> bool:
    """Whether every evaluation error is an undeclared constant identifier."""
    diagnostics = re.findall(r"error:\s*(.+)", str(error))
    return bool(diagnostics) and all("use of undeclared identifier" in item for item in diagnostics)


def _integer(
    source: str,
    maximum: int | None,
    deferred: bool = False,
    *,
    minimum: int = 0,
    decimal_literals: bool = True,
) -> int | None:
    """Evaluate an integer within the caller's domain, deferring only undeclared names.

    XML decimal literals retain their mathematical value when decimal_literals
    is True. Otherwise slang applies SystemVerilog literal sizing and signedness.
    Malformed, non-integral and out-of-domain constants raise TgiError.
    """
    try:
        stripped = source.strip()
        value = (
            int(stripped, 10)
            if decimal_literals and re.fullmatch(r"[+-]?[0-9]+", stripped)
            else SvExpressionParser().evaluate(source)
        )
    except SvExpressionError as error:
        if deferred and _undeclared(error):
            return None
        raise TgiError("Cannot evaluate integer expression", TgiFaultCode.INVALID_ARGUMENT) from error
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise TgiError("Expression outside unsigned integer bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _real(
    source: str, *, minimum: float | None = None, maximum: float | None = None, deferred: bool = False
) -> float | None:
    """Evaluate a finite real constant within optional inclusive bounds (C.7.3).

    Deferred evaluation retains only expressions with undeclared identifiers.
    """
    _xml_text(source)
    for bound in (minimum, maximum):
        if bound is not None and (type(bound) not in (int, float) or (isinstance(bound, float) and math.isnan(bound))):
            raise TgiError("Invalid real expression bound", TgiFaultCode.INVALID_ARGUMENT)
    if minimum is not None and maximum is not None and minimum > maximum:
        raise TgiError("Real expression bounds are reversed", TgiFaultCode.INVALID_ARGUMENT)
    try:
        value = float(SvExpressionParser().evaluate(source))
    except SvExpressionError as error:
        if deferred and _undeclared(error):
            return None
        raise TgiError("Cannot evaluate real expression", TgiFaultCode.INVALID_ARGUMENT) from error
    except (OverflowError, ValueError) as error:
        raise TgiError("Cannot evaluate real expression", TgiFaultCode.INVALID_ARGUMENT) from error
    if not math.isfinite(value):
        raise TgiError("Real expression must be finite", TgiFaultCode.INVALID_ARGUMENT)
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise TgiError("Real expression outside declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _real_source(value: str, current: RealExpression) -> str:
    """Validate real source text before mutation, retaining unresolved constants."""
    _real(value, minimum=current.minimum, maximum=current.maximum, deferred=True)
    return value


def _bit(source: str, *, deferred: bool = False) -> bool | None:
    """Resolve an expression with the SystemVerilog one-bit cast required by C.7.9.

    Deferred evaluation retains only expressions with undeclared identifiers.
    """
    _xml_text(source)
    try:
        return bool(SvExpressionParser().evaluate(f"bit'({source})"))
    except SvExpressionError as error:
        if deferred and _undeclared(error):
            return None
        raise TgiError("Cannot cast expression to an unsigned bit", TgiFaultCode.INVALID_ARGUMENT) from error


def _source(value: str, current: ComplexBaseExpression | None = None, maximum: int | None = _UINT_MAX) -> str:
    _xml_text(value)
    if not value.strip():
        raise TgiError("Expression must be nonempty", TgiFaultCode.INVALID_ARGUMENT)
    if current is not None:
        declared_minimum, declared_maximum = getattr(current, "minimum", None), getattr(current, "maximum", None)
        if declared_minimum is not None and declared_maximum is not None and declared_minimum > declared_maximum:
            raise TgiError("Expression bounds are reversed", TgiFaultCode.INVALID_ARGUMENT)
    result = _integer(value, maximum, True)
    if result is not None and current is not None:
        minimum = getattr(current, "minimum", None)
        maximum = getattr(current, "maximum", None)
        if (minimum is not None and result < minimum) or (maximum is not None and result > maximum):
            raise TgiError("Expression outside declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _string_source(source: str) -> str:
    """Validate a C.7.5/C.7.6 string expression, deferring undeclared names."""
    _xml_text(source)
    try:
        SvExpressionParser().parse_string(source)
    except SvExpressionError as error:
        if not _undeclared(error):
            raise TgiError("Cannot resolve string expression", TgiFaultCode.INVALID_ARGUMENT) from error
    return source


def _tied_value(source: str, current: ComplexTiedValueExpression, *, deferred: bool = False) -> str | None:
    """Resolve a tied value to an unsigned integer or the standard open/default strings."""
    _xml_text(source)
    minimum, maximum = current.minimum, current.maximum
    if any(bound is not None and type(bound) is not int for bound in (minimum, maximum)):
        raise TgiError("Invalid tied-value bounds", TgiFaultCode.INVALID_ARGUMENT)
    if minimum is not None and maximum is not None and minimum > maximum:
        raise TgiError("Tied-value bounds are reversed", TgiFaultCode.INVALID_ARGUMENT)
    if source.strip() in ("open", "default"):
        return source.strip()
    try:
        result = SvExpressionParser().parse_string(source)
    except SvExpressionError:
        result = None
    if result is not None:
        value = result.value.value
        if not isinstance(value, str) or value not in ("open", "default"):
            raise TgiError("Invalid tied-value string", TgiFaultCode.INVALID_ARGUMENT)
        return value
    value = _integer(source, None, deferred, decimal_literals=False)
    if value is None:
        return None
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise TgiError("Tied value outside declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    return str(value)
