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


@pytest.mark.parametrize(
    "expression,expected",
    [
        ('"u.sig[3]"', "u.sig[3]"),
        ('{"u", ".", "sig"}', "u.sig"),
        ("string'(65)", "A"),
        ('1 ? "left" : "right"', "left"),
        ('""', ""),
    ],
)
def test_string_assignment_context(expression: str, expected: str) -> None:
    result = SvExpressionParser().parse_string(expression)
    assert result.value.value == expected
    assert result.bit_width is None
    with pytest.raises(SvExpressionError, match="not an integer or real"):
        result.as_python()


def test_string_context_resolves_named_constants() -> None:
    parser = SvExpressionParser({"PREFIX": 'string\'("u")', "INDEX": 3})
    result = parser.parse_string('{PREFIX, ".sig"}')
    assert result.value.value == "u.sig"
    assert parser.evaluate("INDEX + 1") == 4


@pytest.mark.parametrize("expression", ["7", "1.5", "", '"unterminated', "MISSING", "1; localparam injected=2"])
def test_invalid_string_assignment_context(expression: str) -> None:
    with pytest.raises(SvExpressionError):
        SvExpressionParser().parse_string(expression)


@pytest.mark.parametrize(
    "expression,width,expected",
    [
        ("-1", 8, 255),
        ("256", 8, 0),
        ("8'bx1z0", 8, 4),
        ("3.5", 8, 4),
        ('"AB"', 8, 66),
        ("128'hffffffffffffffffffffffffffffffff", 128, 2**128 - 1),
        ("8'shff", None, 255),
    ],
)
def test_bit_vector_assignment_context(expression: str, width: int | None, expected: int) -> None:
    result = SvExpressionParser().parse_bit_vector(expression, width)
    assert result.as_python() == expected
    assert result.bit_width == (8 if width is None else width)
    assert result.is_signed is False
    assert result.has_unknown is False
    assert result.expression == expression


@pytest.mark.parametrize("width", [0, -1, True, 1.5, "8"])
def test_invalid_bit_vector_width(width) -> None:
    with pytest.raises(SvExpressionError, match="positive integer"):
        SvExpressionParser().parse_bit_vector("1", width)


@pytest.mark.parametrize("expression", ["3.5", "string'(65)"])
def test_nonintegral_bit_vector_requires_width(expression: str) -> None:
    with pytest.raises(SvExpressionError, match="explicit bit vector width"):
        SvExpressionParser().parse_bit_vector(expression)


def test_bit_vector_named_constants_and_invalid_expression() -> None:
    parser = SvExpressionParser({"WIDTH": 8, "VALUE": -1})
    assert parser.parse_bit_vector("VALUE", 8).as_python() == 255
    with pytest.raises(SvExpressionError):
        parser.parse_bit_vector("MISSING", 8)
