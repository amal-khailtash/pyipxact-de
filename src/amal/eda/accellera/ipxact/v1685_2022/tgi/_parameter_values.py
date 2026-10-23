"""Numeric value helpers shared by IP-XACT parameter TGI operations."""

import re

from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser
from org.accellera.ipxact.v1685_2022 import FormatType, ModuleParameterType, ParameterType

from .core import TgiError, TgiFaultCode


def _bit_width(parameter: ModuleParameterType | ParameterType) -> int:
    vectors = parameter.vectors
    if vectors is None or not vectors.vector:
        return 1
    parser = SvExpressionParser()
    width = 1
    try:
        for vector in vectors.vector:
            left = parser.evaluate(vector.left.value)
            right = parser.evaluate(vector.right.value)
            if not isinstance(left, int) or not isinstance(right, int):
                raise ValueError("vector bounds must be integers")
            width *= abs(left - right) + 1
    except (AttributeError, SvExpressionError, TypeError, ValueError) as error:
        raise TgiError("Unable to evaluate parameter vector bounds", TgiFaultCode.INVALID_ARGUMENT) from error
    return width


def _evaluate_numeric(parameter: ModuleParameterType | ParameterType, source: str) -> int | float:
    try:
        value = SvExpressionParser().evaluate(source)
    except SvExpressionError as error:
        raise TgiError("Unable to evaluate parameter expression", TgiFaultCode.INVALID_ARGUMENT) from error

    kind = parameter.type_value
    if kind is FormatType.STRING:
        return value
    if kind in (FormatType.BIT, FormatType.BYTE, FormatType.SHORTINT, FormatType.INT, FormatType.LONGINT):
        if not isinstance(value, int):
            raise TgiError("Integer parameter requires an integer expression", TgiFaultCode.INVALID_ARGUMENT)
        if kind is FormatType.BIT:
            width = _bit_width(parameter)
            signed = getattr(parameter.sign, "value", None) == "signed"
            low = -(1 << (width - 1)) if signed else 0
            high = (1 << (width - (1 if signed else 0))) - 1
        else:
            width = {
                FormatType.BYTE: 8,
                FormatType.SHORTINT: 16,
                FormatType.INT: 32,
                FormatType.LONGINT: 64,
            }[kind]
            signed = getattr(parameter.sign, "value", None) != "unsigned"
            low = -(1 << (width - 1)) if signed else 0
            high = (1 << (width - (1 if signed else 0))) - 1
        if not low <= value <= high:
            raise TgiError(f"Parameter value is outside the {kind.value} range", TgiFaultCode.INVALID_ARGUMENT)
    elif kind in (FormatType.SHORTREAL, FormatType.REAL) and not isinstance(value, (int, float)):
        raise TgiError("Real parameter requires a numeric expression", TgiFaultCode.INVALID_ARGUMENT)

    if kind is not FormatType.STRING:
        _check_declared_bounds(parameter, value)
    return value


def _check_declared_bounds(parameter: ModuleParameterType | ParameterType, value: int | float) -> None:
    parser = SvExpressionParser()
    for label, bound, comparison in (
        ("minimum", parameter.minimum, lambda actual, limit: actual >= limit),
        ("maximum", parameter.maximum, lambda actual, limit: actual <= limit),
    ):
        if bound is None:
            continue
        try:
            limit = parser.evaluate(bound)
        except SvExpressionError as error:
            raise TgiError(f"Unable to evaluate parameter {label}", TgiFaultCode.INVALID_ARGUMENT) from error
        if not comparison(value, limit):
            raise TgiError(f"Parameter value violates its {label}", TgiFaultCode.INVALID_ARGUMENT)


def _validate_numeric_update(parameter: ModuleParameterType | ParameterType, expression: str) -> None:
    if parameter.type_value is FormatType.STRING:
        return
    try:
        _evaluate_numeric(parameter, expression)
    except TgiError as error:
        # Only undeclared names distinguish deferred expressions from malformed
        # syntax, unknown bits, non-integer values, or range violations.
        cause = error.__cause__
        diagnostics = re.findall(r"error:\s*(.+)", str(cause)) if isinstance(cause, SvExpressionError) else []
        if diagnostics and all("use of undeclared identifier" in item for item in diagnostics):
            return
        raise
