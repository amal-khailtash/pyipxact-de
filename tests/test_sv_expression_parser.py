"""Slang evaluation preserves SV constant semantics and diagnostic failures."""

import pytest

from amal.eda.systemverilog import SvExpressionError, SvExpressionParser


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("1 + 2 * 3", 7),
        ("$clog2(256)", 8),
        ("8'shff", -1),
        ("{4'hA, 4'h5}", 165),
        ("3.5 / 2", 1.75),
        ("1 ? 12 : 3", 12),
        ("8'hff + 8'd1", 0),
        ("64'd2 ** 40", 2**40),
    ],
)
def test_evaluate(expression, expected):
    assert SvExpressionParser().evaluate(expression) == expected


def test_named_constants_and_sizing():
    parser = SvExpressionParser({"WIDTH": 8, "MASK": "8'hff"})
    result = parser.parse("MASK >> (WIDTH / 2)")
    assert result.as_python() == 15
    assert result.bit_width == 8
    assert result.is_signed is False


def test_four_state_value():
    result = SvExpressionParser().parse("4'b10xz")
    assert result.has_unknown
    assert result.bit_width == 4
    assert "xz" in result.literal
    with pytest.raises(SvExpressionError, match="X/Z"):
        result.as_python()


@pytest.mark.parametrize("expression", ["", "1 +", "MISSING + 1", "1; localparam injected=2"])
def test_invalid_expression(expression):
    with pytest.raises(SvExpressionError):
        SvExpressionParser().parse(expression)


def test_invalid_constant_name():
    with pytest.raises(SvExpressionError, match="constant name"):
        SvExpressionParser({"bad-name": 1}).parse("1")
