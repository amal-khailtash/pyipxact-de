"""Interactive SystemVerilog constant-expression evaluation with slang."""

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.hdl import SystemVerilogLexer

from .expression_parser import SvExpressionError, SvExpressionParser, SvExpressionResult

HELP = """SystemVerilog Constant Expression REPL (slang backend)
Enter an expression; '?' or 'help' for help; 'quit' or 'exit' to leave.
Use SV sized literals to control width. X/Z bits are preserved.
Press Ctrl+D or Ctrl+C to exit.
"""


class Repl:
    """Evaluate expressions through the reusable slang parser class."""

    def __init__(self, parser: SvExpressionParser | None = None) -> None:
        """Create a prompt with history, suggestions and SV syntax highlighting."""
        self.parser = parser or SvExpressionParser()
        self.session = PromptSession(
            "sv const expr > ",
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory(),
            lexer=PygmentsLexer(SystemVerilogLexer),
        )

    def evaluate(self, text: str) -> SvExpressionResult | None:
        """Print an evaluated constant or diagnostic and return its result."""
        try:
            result = self.parser.parse(text)
        except SvExpressionError as error:
            print(f"Parse/Eval Error: {error}")
            return None
        if result.has_unknown:
            print(f"Value: {result.literal} (contains X/Z)")
        else:
            value = result.as_python()
            if isinstance(value, int):
                print(f"Value: {value:,} (dec), {value:b} (bin), {value:o} (oct), {value:x} (hex)")
            else:
                print(f"Value: {value}")
        if result.bit_width is not None:
            print(f"SV: {result.literal}, {result.bit_width} bits, {'signed' if result.is_signed else 'unsigned'}")
        if result.diagnostics:
            print(result.diagnostics)
        return result

    def run(self) -> None:
        """Read expressions until an exit command, EOF or keyboard interrupt."""
        print(HELP)
        while True:
            try:
                text = self.session.prompt().strip()
            except EOFError, KeyboardInterrupt:
                break
            if text in ("quit", "exit"):
                break
            if text in ("?", "help"):
                print(HELP)
            elif text:
                self.evaluate(text)


def main() -> None:
    """Run the slang expression REPL."""
    Repl().run()


if __name__ == "__main__":
    main()
