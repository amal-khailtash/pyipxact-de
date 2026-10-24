"""Registry output batching, literal text, and terminal styling."""

from io import StringIO
from unittest.mock import patch

from rich.console import Console

from amal.eda.ipxact_de.cli import _RegistryOutput


def test_plain_output_preserves_long_literal_rows_without_wrapping() -> None:
    sink = StringIO()
    console = Console(file=sink, width=20, force_terminal=True, color_system="standard")
    output = _RegistryOutput(console, plain=True)
    name = "[literal]" + "long_name_" * 30
    with patch.object(console, "print") as render:
        output.write((name, "vlnv.name"), "  ", ("SPIRIT 1685-2009", "dim"))
        output.flush()
    assert sink.getvalue() == name + "  SPIRIT 1685-2009\n"
    render.assert_not_called()


def test_terminal_output_batches_rows_and_keeps_styles() -> None:
    sink = StringIO()
    console = Console(file=sink, force_terminal=True, color_system="standard")
    output = _RegistryOutput(console, plain=False)
    with patch.object(console, "print", wraps=console.print) as render:
        for index in range(1000):
            output.write((f"row-{index}", "bold red"), "  ", ("SPIRIT 1685-2009", "dim"))
        output.flush()
    assert 1 < render.call_count < 10
    text = sink.getvalue()
    assert "\x1b[" in text
    assert text.count("SPIRIT 1685-2009") == 1000
    assert "row-0" in text and "row-999" in text


def test_plain_rows_stream_before_the_producer_finishes() -> None:
    sink = StringIO()
    output = _RegistryOutput(Console(file=sink, force_terminal=False), plain=True)
    for index in range(1000):
        output.write(f"row-{index}")
        if index == 500:
            assert "row-0\n" in sink.getvalue()
            assert "row-999" not in sink.getvalue()
    output.flush()
    assert sink.getvalue().endswith("row-999\n")
