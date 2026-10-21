SystemVerilog constant expressions
=================================

``SvExpressionParser`` uses the slang compiler's Python bindings (``pyslang``)
to parse and evaluate SystemVerilog constant expressions. It is available from
``amal.eda.systemverilog`` and can be reused by IP-XACT expression consumers::

    from amal.eda.systemverilog import SvExpressionParser

    parser = SvExpressionParser({"WIDTH": 8, "MASK": "8'hff"})
    assert parser.evaluate("$clog2(256)") == 8
    result = parser.parse("MASK")
    print(result.as_python(), result.bit_width, result.is_signed)

Named constants accept integers, reals, or SystemVerilog expression source.
Use sized literals to control width: normal SystemVerilog sizing and signedness
apply, including overflow. Parameterized IP-XACT references are not resolved
by this utility; callers provide their constant environment explicitly.

``parse`` returns an ``SvExpressionResult`` containing the native slang constant,
its literal representation, width, signedness and diagnostics. X/Z bits are
preserved; ``as_python`` and ``evaluate`` reject unknown bits rather than losing
information. Real constants convert to Python floats. Syntax, name-binding and
constant evaluation errors raise ``SvExpressionError`` with slang diagnostics.
SV string literals follow slang's constant representation and may be represented
as packed integral values rather than Python strings.

Interactive use
---------------

Run ``make sv-expr-repl``, ``uv run --locked sv-expr-repl``, or
``uv run --locked python -m amal.eda.systemverilog.repl``. The prompt has
history, suggestions and SystemVerilog highlighting. Enter an expression to see
its decimal/binary/octal/hex value and native SV width/signedness. ``help`` or
``?`` displays help; ``quit``, ``exit``, Ctrl+D or Ctrl+C exits. The REPL accepts
the same expressions as the reusable parser.
