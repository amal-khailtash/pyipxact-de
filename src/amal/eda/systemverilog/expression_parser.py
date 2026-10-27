"""Parse and evaluate SystemVerilog constant expressions with slang."""

import re
from collections.abc import Mapping
from dataclasses import dataclass

import pyslang

__all__ = ["SvExpressionError", "SvExpressionParser", "SvExpressionResult"]


class SvExpressionError(ValueError):
    """A SystemVerilog expression cannot be parsed or evaluated as a constant."""


@dataclass(frozen=True)
class SvExpressionResult:
    """A slang constant retaining SystemVerilog width, signedness and unknown bits.

    ``value`` exposes the native slang constant. ``as_python`` converts known
    integral and real values; X/Z values must be inspected through ``literal``.
    """

    expression: str
    value: pyslang.ConstantValue
    diagnostics: str = ""

    @property
    def literal(self) -> str:
        """Return slang's representation of the evaluated constant."""
        return str(self.value)

    @property
    def has_unknown(self) -> bool:
        """Whether the constant contains SystemVerilog X or Z bits."""
        return self.value.hasUnknown()

    @property
    def bit_width(self) -> int | None:
        """Return integral bit width, or None for a non-integral constant."""
        raw = self.value.value
        return raw.bitWidth if isinstance(raw, pyslang.SVInt) else None

    @property
    def is_signed(self) -> bool | None:
        """Return integral signedness, or None for a non-integral constant."""
        raw = self.value.value
        return raw.isSigned if isinstance(raw, pyslang.SVInt) else None

    def as_python(self) -> int | float:
        """Convert a known integer or real without discarding X/Z information.

        Raises:
            SvExpressionError: For unknown bits or a non-numeric constant.
        """
        if self.has_unknown:
            raise SvExpressionError("Cannot convert a constant containing X/Z bits to a Python number")
        raw = self.value.value
        if isinstance(raw, pyslang.SVInt):
            return int(raw)
        if isinstance(raw, float):
            return raw
        raise SvExpressionError("Constant is not an integer or real number")


class SvExpressionParser:
    """Evaluate constant expressions using slang's SystemVerilog compiler.

    Constants map simple SV identifiers to Python integers/reals or SV source
    expressions. Strings are interpreted as SV source, so an SV string literal
    must include its quotes. Native SV sizing rules apply; no implicit widening
    or IP-XACT parameter resolution is performed.
    """

    def __init__(self, constants: Mapping[str, int | float | str] | None = None) -> None:
        """Copy the named constant environment for subsequent evaluations."""
        self.constants = dict(constants or {})

    def parse(self, expression: str) -> SvExpressionResult:
        """Parse and evaluate one expression, retaining slang diagnostics.

        Raises:
            SvExpressionError: On syntax, binding or constant evaluation errors.
        """
        return self._parse(expression, "")

    def parse_string(self, expression: str) -> SvExpressionResult:
        """Resolve an expression in a SystemVerilog string assignment context.

        String literals and compatible expressions follow IEEE 1800 assignment
        rules; numeric values without an explicit string cast are rejected.
        """
        return self._parse(expression, "string ")

    def parse_bit_vector(self, expression: str, width: int | None = None) -> SvExpressionResult:
        """Resolve an expression as an unsigned two-state packed bit vector.

        Assignment conversion applies the supplied width, including truncation,
        sign extension, rounding and X/Z conversion. Without a width, an integral
        expression supplies its own width; other types require an explicit width.
        """
        if width is not None and (isinstance(width, bool) or not isinstance(width, int) or width <= 0):
            raise SvExpressionError("Bit vector width must be a positive integer")
        if width is None:
            width = self.parse(expression).bit_width
            if width is None:
                raise SvExpressionError("A non-integral expression requires an explicit bit vector width")
        return self._parse(expression, f"bit [{width - 1}:0] ")

    def _parse(self, expression: str, result_type: str) -> SvExpressionResult:
        if not expression.strip():
            raise SvExpressionError("Expression must not be empty")
        declarations = []
        for name, value in self.constants.items():
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", name) or name.startswith("__ipxact_"):
                raise SvExpressionError(f"Invalid constant name: {name!r}")
            declarations.append(f"localparam {name} = ({value});")
        source = "module __ipxact_expression;\n" + "\n".join(declarations)
        source += f"\nlocalparam {result_type}__ipxact_result = ({expression});\nendmodule\n"
        tree = pyslang.syntax.SyntaxTree.fromText(source, name="sv-expression")
        compilation = pyslang.ast.Compilation()
        compilation.addSyntaxTree(tree)
        root = compilation.getRoot()
        diagnostics = compilation.getAllDiagnostics()
        rendered = pyslang.DiagnosticEngine.reportAll(tree.sourceManager, diagnostics)
        if any(diagnostic.isError() for diagnostic in diagnostics):
            raise SvExpressionError(rendered.strip())
        parameter = root.topInstances[0].body.find("__ipxact_result")
        if parameter is None or parameter.value.value is None:
            raise SvExpressionError(rendered.strip() or "Expression has no constant value")
        return SvExpressionResult(expression, parameter.value, rendered.strip())

    def evaluate(self, expression: str) -> int | float:
        """Evaluate an expression as a known Python integer or real value."""
        return self.parse(expression).as_python()
