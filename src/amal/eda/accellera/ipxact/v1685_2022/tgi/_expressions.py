"""XML source and unsigned constant-expression validation for TGI models."""

import re

from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser
from org.accellera.ipxact.v1685_2022.complex_base_expression import ComplexBaseExpression

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
        diagnostics = re.findall(r"error:\s*(.+)", str(error))
        if deferred and diagnostics and all("use of undeclared identifier" in item for item in diagnostics):
            return None
        raise TgiError("Cannot evaluate integer expression", TgiFaultCode.INVALID_ARGUMENT) from error
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise TgiError("Expression outside unsigned integer bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _source(value: str, current: ComplexBaseExpression | None = None, maximum: int | None = _UINT_MAX) -> str:
    _xml_text(value)
    if not value.strip():
        raise TgiError("Expression must be nonempty", TgiFaultCode.INVALID_ARGUMENT)
    result = _integer(value, maximum, True)
    if result is not None and current is not None:
        minimum = getattr(current, "minimum", None)
        maximum = getattr(current, "maximum", None)
        if (minimum is not None and result < minimum) or (maximum is not None and result > maximum):
            raise TgiError("Expression outside declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value
