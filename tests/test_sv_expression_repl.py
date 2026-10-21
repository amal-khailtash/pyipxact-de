"""The REPL routes expression evaluation through the shared parser."""

from amal.eda.systemverilog.expression_parser import SvExpressionParser
from amal.eda.systemverilog.repl import Repl


def test_repl_evaluation(capsys, monkeypatch):
    monkeypatch.setattr("amal.eda.systemverilog.repl.PromptSession", lambda *a, **k: None)
    repl = Repl(SvExpressionParser({"WIDTH": 8}))
    assert repl.evaluate("WIDTH * 2").as_python() == 16
    assert "16 (dec)" in capsys.readouterr().out
    assert repl.evaluate("4'bxx01").has_unknown
    assert "contains X/Z" in capsys.readouterr().out
    assert repl.evaluate("unknown") is None
    assert "undeclared identifier" in capsys.readouterr().out
