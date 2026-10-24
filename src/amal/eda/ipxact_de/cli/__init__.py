import argparse
import os
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from types import TracebackType
from typing import TYPE_CHECKING, Self

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from org.accellera.standard import STANDARDS

from .. import __description__, __version__
from .commands import ARROW, convert_xml, identify_xml, validate_xml

if TYPE_CHECKING:
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import VlnvRegistry

# Global Rich console (single theme) reused for all help rendering.
_CLI_THEME = Theme(
    {
        "heading": "bold bright_green",
        "command": "bright_cyan",
        "command.bold": "bold bright_cyan",
        "flag": "bold bright_cyan",
        "usage.label": "bold bright_green",
        "usage.prog": "bold bright_cyan",
        "usage.meta": "cyan",
        "footer": "dim",
        # VLNV display styles
        "vlnv.vendor": "bold bright_green",
        "vlnv.library": "bright_cyan",
        "vlnv.name": "bold white",
        "vlnv.version": "bright_yellow",
        "vlnv.sep": "dim",
        "vlnv.type": "bright_magenta",
    }
)
console = Console(theme=_CLI_THEME, highlight=False)


@dataclass(slots=True)
class HelpSection:
    """Runtime help section (built dynamically)."""

    title: str
    rows: list[tuple[str, str]]
    priority: int = 100


_COMMANDS_ORDER: list[str] = [
    "standards",
    "identify",
    "validate",
    "convert",
    "registry",
    "web",
    "gui",
    "mcp",
    "help",
    "version",
]
_ACTION_METADATA: dict[int, tuple[str, int]] = {}


def _build_sections(
    parser: argparse.ArgumentParser, subparser_map: dict[str, argparse.ArgumentParser]
) -> list[HelpSection]:
    """Create ordered help sections from parser metadata."""
    sections: dict[str, HelpSection] = {}

    # Commands section
    cmd_entries: list[tuple[int, str, str]] = []  # (order, name, desc)
    for name, sp in subparser_map.items():
        order = _COMMANDS_ORDER.index(name) if name in _COMMANDS_ORDER else 1000
        desc = sp.description or name
        cmd_entries.append((order, name, desc))
    if cmd_entries:
        cmd_entries.sort(key=lambda t: (t[0], t[1]))
        sections["Commands:"] = HelpSection("Commands:", [(n, d) for _, n, d in cmd_entries], priority=10)

    # Options grouped by registered metadata
    for action in parser._actions:  # noqa: SLF001
        if not action.option_strings:
            continue
        if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
            continue
        title, prio = _ACTION_METADATA.get(id(action), ("Global options:", 90))
        if title in sections:
            hs = sections[title]
        else:
            hs = HelpSection(title, [], priority=prio)
            sections[title] = hs
        flags = ", ".join(action.option_strings)
        hs.rows.append((flags, action.help or ""))

    return sorted(sections.values(), key=lambda s: (s.priority, s.title))


def _format_flags(flags: str) -> str:
    """Return flags (already provided in desired form)."""
    return flags


def _natural_key(text: str) -> list[int | str]:
    """Natural sort key for strings with embedded numbers.

    Splits the input into digit and non-digit runs; digits compare as integers,
    text compares case-insensitively. This provides intuitive ordering for
    semantic versions (e.g., 1.9 < 1.10) and mixed tokens (e.g., r2p0_6).

    Args:
        text: Input string to turn into a sortable key.

    Returns:
        A list of ints and strings usable as a sort key.
    """
    parts = re.split(r"(\d+)", text)
    key: list[int | str] = []
    for part in parts:
        if not part:
            continue
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.casefold())
    return key


def _get_type_for_handle(handle: str) -> str:
    """Return the registered element type for a handle, or empty string."""
    t = _get_registry().get_element_type(handle)
    return t or ""


def _get_registry() -> VlnvRegistry:
    """Return the shared TGI registry, importing the full API only when needed."""
    registry = globals().get("registry")
    if registry is None:
        from amal.eda.accellera.ipxact.v1685_2022.tgi.core import registry
    return registry


def __getattr__(name: str) -> VlnvRegistry:
    """Preserve public registry access without loading the TGI API at CLI startup."""
    if name == "registry":
        return _get_registry()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def load_registry_from_cache(
    *,
    cache_dir: Path | None = None,
    validate_files: bool = True,
    progress: Callable[[str, int, int], None] | None = None,
) -> bool:
    """Load the saved registry on demand; retained as a patchable CLI module name."""
    from ..loader import load_registry_from_cache as load

    return load(cache_dir=cache_dir, validate_files=validate_files, progress=progress)


def load_registry_from_paths(
    paths: Iterable[str],
    *,
    cache_dir: Path | None = None,
    progress: Callable[[str, int, int], None] | None = None,
    document_reporter: Callable[[Path, str, str, str], None] | None = None,
) -> None:
    """Scan registry paths on demand; retained as a patchable CLI module name."""
    from ..loader import load_registry_from_paths as load

    return load(paths, cache_dir=cache_dir, progress=progress, document_reporter=document_reporter)


class _RichSubHelpAction(argparse.Action):
    """Custom help action for subcommands to show Rich-styled help and exit early.

    This avoids argparse enforcing required positionals before displaying help.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object = None,
        option_string: str | None = None,
    ) -> None:  # type: ignore[override]
        parts = parser.prog.split()
        parent_prog = parts[0] if parts else "ipxact-de"
        subcmd = parts[-1] if len(parts) > 1 else parser.prog
        _print_subcommand_help(parent_prog, subcmd, parser)
        parser.exit()


def _print_top_level_help(parser: argparse.ArgumentParser) -> None:
    """Print top-level help building sections dynamically from parser state."""
    prog = parser.prog
    if parser.description:
        console.print(parser.description)
        console.print()
    usage_line = (
        Text("Usage:", style="usage.label")
        .append(" ")
        .append(prog, style="usage.prog")
        .append(" ")
        .append("[OPTIONS] <COMMAND>", style="usage.meta")
    )
    console.print(usage_line)
    console.print()

    # Discover subparsers to build command section
    subparser_map: dict[str, argparse.ArgumentParser] = {}
    for action in parser._actions:  # noqa: SLF001
        if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
            for name, sp in action._name_parser_map.items():  # type: ignore[attr-defined]
                subparser_map[name] = sp

    sections = _build_sections(parser, subparser_map)
    for section in sections:
        console.print(Text(section.title, style="heading"))
        table = Table(show_header=False, box=None, pad_edge=False)
        table.add_column(no_wrap=True)
        table.add_column()
        pad_width = max(len(flags) for flags, _ in section.rows) if section.rows else 0
        for left, help_text in section.rows:
            pad = f"{left:<{pad_width}}"
            style = "command.bold" if section.title.startswith("Commands") else "flag"
            table.add_row(f"  [{style}]{pad}[/]", help_text)
        console.print(table)
        console.print()

    console.print(Text("Use `ipxact-de help` for more details.", style="footer"))


def _print_subcommand_help(parent_prog: str, name: str, subparser: argparse.ArgumentParser) -> None:
    """Print Rich-styled help for a specific subcommand.

    Args:
        parent_prog: Top-level program name.
        name: Subcommand name.
        subparser: The argparse subparser instance.
    """
    usage = f"{parent_prog} {name}"
    # Collect actions
    positional: list[tuple[str, str]] = []
    options: list[tuple[str, str]] = []
    subcommands: list[tuple[str, str]] = []
    for action in subparser._actions:  # noqa: SLF001
        if isinstance(action, argparse._HelpAction):  # skip built-in help
            continue
        if isinstance(action, argparse._SubParsersAction):
            # Collect nested subcommands (e.g., registry -> scan/list)
            for sub_name, sp in action._name_parser_map.items():  # type: ignore[attr-defined]
                desc = sp.description or sub_name
                subcommands.append((sub_name, desc))
            continue
        help_text = action.help or ""
        if action.option_strings:
            flags = ", ".join(action.option_strings)
            # Determine if value placeholder needed
            needs_value = getattr(action, "nargs", None) not in (0, None) or (
                getattr(action, "nargs", None) is None
                and not isinstance(action, argparse._StoreTrueAction | argparse._StoreFalseAction)
            )
            if not action.option_strings or isinstance(action, argparse._StoreTrueAction | argparse._StoreFalseAction):
                needs_value = False
            if needs_value:
                placeholder = action.metavar or action.dest.upper().replace("-", "_")
                flags_display = f"{flags} {placeholder}"
            else:
                flags_display = flags
            options.append((flags_display, help_text))
        else:
            # Positional argument; metavar can be a tuple for multiple values.
            raw_meta = action.metavar or action.dest.upper().replace("-", "_")
            placeholder = " ".join(str(m) for m in raw_meta) if isinstance(raw_meta, tuple) else str(raw_meta)
            positional.append((placeholder, help_text))

    # Header / description: print top-level description then subcommand description (if any) before usage
    desc = subparser.description or next(
        (a.help for a in getattr(subparser, "_actions", []) if isinstance(a, argparse._HelpAction)),
        None,
    )
    printed_any = False
    if __description__:
        console.print(__description__)
        printed_any = True
    if desc:
        if printed_any:
            console.print()
        console.print(desc)
        printed_any = True
    if printed_any:
        console.print()

    usage_line = (
        Text("Usage:", style="usage.label")
        .append(" ")
        .append(usage, style="usage.prog")
        .append(" ")
        .append("[OPTIONS]" if options else "", style="usage.meta")
        .append(" ")
        .append("<SUBCOMMAND>" if subcommands else "", style="usage.meta")
    )
    console.print(usage_line)
    console.print()

    if positional:
        console.print(Text("Arguments", style="heading"))
        arg_table = Table(show_header=False, box=None, pad_edge=False)
        arg_table.add_column(no_wrap=True)
        arg_table.add_column()
        width = max(len(n) for n, _ in positional)
        for name_col, help_col in positional:
            pad = f"{name_col:<{width}}"
            arg_table.add_row(f"  [command.bold]{pad}[/]", help_col)
        console.print(arg_table)
        console.print()

    if subcommands:
        console.print(Text("Subcommands", style="heading"))
        sub_table = Table(show_header=False, box=None, pad_edge=False)
        sub_table.add_column(no_wrap=True)
        sub_table.add_column()
        # Preserve desired order: scan, list (fallback to name sort for others)
        order_map = {"scan": 0, "list": 1}
        ordered = sorted(subcommands, key=lambda t: (order_map.get(t[0], 100), t[0]))
        width = max(len(n) for n, _ in ordered)
        for sub_name, sub_desc in ordered:
            pad = f"{sub_name:<{width}}"
            sub_table.add_row(f"  [command.bold]{pad}[/]", sub_desc)
        console.print(sub_table)
        console.print()

    if options:
        console.print(Text("Options", style="heading"))
        opt_table = Table(show_header=False, box=None, pad_edge=False)
        opt_table.add_column(no_wrap=True)
        opt_table.add_column()
        width = max(len(n) for n, _ in options)
        for flags, help_col in options:
            pad = f"{flags:<{width}}"
            opt_table.add_row(f"  [flag]{pad}[/]", help_col)
        console.print(opt_table)


@dataclass(slots=True)
class CommandSpec:
    """Specification for registering a subcommand.

    Attributes:
        name: Subcommand name.
        help: Short help/description.
        register: Callable that receives the subparsers object and returns the created subparser.
    """

    name: str
    help: str
    register: Callable[[argparse._SubParsersAction], argparse.ArgumentParser]


def _build_command_specs(all_versions: list[str]) -> list[CommandSpec]:
    """Create command specs for identify, validate, convert, version.

    Args:
        all_versions: Supported conversion targets.

    Returns:
        List of command specifications (excluding 'help').
    """

    def _register_standards(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'standards' subcommand to list supported schema versions."""
        parser_standards = subparsers.add_parser(
            "standards",
            description="List supported SPIRIT/IP-XACT schema versions",
            help="List supported schema versions",
            add_help=False,
        )
        parser_standards.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_standards.set_defaults(func=_print_standards)
        return parser_standards

    def _register_identify(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'identify' subcommand.

        Args:
            subparsers: Subparsers action to register with.

        Returns:
            The configured subparser.
        """
        # Provide description once; argparse will surface short help (first line of description) automatically if needed
        parser_identity = subparsers.add_parser(
            "identify",
            description="Identify IP-XACT xml files",
            help="Identify IP-XACT xml files",
            add_help=False,
        )
        parser_identity.add_argument(
            "xml-files",
            type=argparse.FileType("r"),
            nargs="+",
            help="IP-XACT xml files to identify",
        )
        parser_identity.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_identity.set_defaults(func=identify_xml)
        return parser_identity

    def _register_validate(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'validate' subcommand.

        Args:
            subparsers: Subparsers action to register with.

        Returns:
            The configured subparser.
        """
        parser_validate = subparsers.add_parser(
            "validate",
            description="Validate IP-XACT xml files",
            help="Validate IP-XACT xml files",
            add_help=False,
        )
        parser_validate.add_argument(
            "xml-files",
            type=argparse.FileType("r"),
            nargs="*",
            help="IP-XACT xml files to validate",
        )
        parser_validate.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_validate.add_argument(
            "--schema-root",
            type=Path,
            help="Local Accellera schema tree containing IPXACT and SPIRIT directories",
        )
        parser_validate.add_argument(
            "--semantic",
            action="store_true",
            help="Also check implemented IEEE 1685-2022 abstraction and component constraint rules",
        )
        # Use a wrapper to show subcommand help if no files are provided.
        parser_validate.set_defaults(func=_run_validate, __validate_parser=parser_validate)
        return parser_validate

    def _register_registry(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'registry' command with subcommands: scan, list."""
        parser_registry = subparsers.add_parser(
            "registry",
            description="Manage the in-memory VLNV registry",
            help="Manage the in-memory VLNV registry",
            add_help=False,
        )
        parser_registry.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        # Default action: if no subcommand is provided, show the registry help.
        parser_registry.set_defaults(func=_run_registry, __registry_parser=parser_registry)
        reg_sub = parser_registry.add_subparsers(dest="registry_cmd")

        # registry scan
        parser_rscan = reg_sub.add_parser(
            "scan",
            description="Scan paths for IP-XACT XML files and update registry",
            help="Scan paths for XML files and update registry",
            add_help=False,
        )
        parser_rscan.add_argument(
            "paths",
            nargs="*",
            metavar="PATH",
            help=(
                "Paths or directories to scan. Multiple may be provided. "
                "Also honors IPXACT_XML_PATHS from the environment."
            ),
        )
        parser_rscan.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_rscan.set_defaults(func=_run_scan, __scan_parser=parser_rscan)

        # registry list (keep after scan in parser creation to show desired order)
        parser_rlist = reg_sub.add_parser(
            "list",
            description=(
                "List the inventory saved by the last scan (tree by default). "
                "Use --flat for single-line Vendor:Library:Name:Version."
            ),
            help="List entries (tree by default)",
            add_help=False,
        )
        parser_rlist.add_argument(
            "pattern",
            nargs="?",
            help=(
                "Optional filter pattern 'vendor:library:name:version'.\n"
                "  - Without --regex: case-insensitive substring per part; use '*' to match anything.\n"
                "  - With --regex: each part is treated as a regular expression.\n"
                "  - Omit a part to match all (e.g., 'vendor::name:*')."
            ),
        )
        parser_rlist.add_argument(
            "-r",
            "--regex",
            action="store_true",
            help="Treat pattern parts as regular expressions",
        )
        parser_rlist.add_argument(
            "-f",
            "--flat",
            action="store_true",
            help="Display results as flat lines: vendor:library:name:version",
        )
        parser_rlist.add_argument(
            "--color",
            choices=["auto", "always", "never"],
            default="auto",
            help="Color output: auto (default), always (including pipes), or never; --plain overrides colors",
        )
        parser_rlist.add_argument(
            "--plain",
            action="store_true",
            help="Use fast plain text without colors or wrapping (automatic for redirected output)",
        )
        parser_rlist.add_argument(
            "-t",
            "--type",
            choices=[
                "busDefinition",
                "abstractionDefinition",
                "typeDefinitions",
                "component",
                "design",
                "abstractor",
                "generatorChain",
                "designConfiguration",
                "catalog",
            ],
            help=(
                "Filter by top-level IP-XACT element type. "
                "Valid types: busDefinition, abstractionDefinition, typeDefinitions, "
                "component, design, abstractor, generatorChain, designConfiguration, catalog"
            ),
        )
        parser_rlist.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_rlist.set_defaults(func=_run_registry_list)

        return parser_registry

    def _register_convert(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'convert' subcommand.

        Args:
            subparsers: Subparsers action to register with.

        Returns:
            The configured subparser.
        """
        parser_convert = subparsers.add_parser(
            "convert",
            description="Convert IP-XACT xml files",
            help="Convert IP-XACT xml files",
            add_help=False,
        )
        parser_convert.add_argument(
            "--to-version",
            type=str,
            choices=all_versions,
            help="Convert IP-XACT file to version (supported: [bright_cyan]"
            + ", ".join(all_versions)
            + "[/bright_cyan])",
        )
        parser_convert.add_argument(
            "xml-files",
            type=argparse.FileType("r"),
            nargs="*",
            help="IP-XACT XML file to convert",
        )
        parser_convert.add_argument(
            "--output-dir",
            "-o",
            type=str,
            default="converted",
            help="Output directory for the converted IP-XACT XML file",
        )
        # parser_convert.add_argument("output-file", type=str, help="Output IP-XACT XML file")
        parser_convert.add_argument(
            "--overwrite", action="store_true", help="Force overwrite of the output file if it exists"
        )
        parser_convert.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        # Use a wrapper to show subcommand help if no files are provided.
        parser_convert.set_defaults(func=_run_convert, __convert_parser=parser_convert)
        return parser_convert

    def _register_web(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'web' subcommand to run the FastAPI app.

        Args:
            subparsers: Subparsers action to register with.

        Returns:
            The configured subparser.
        """
        parser_web = subparsers.add_parser(
            "web",
            description="Run the FastAPI GUI web app",
            help="Run the FastAPI GUI web app",
            add_help=False,
        )
        parser_web.add_argument(
            "--host",
            type=str,
            default="localhost",
            help="Host interface to bind (default: localhost)",
        )
        parser_web.add_argument(
            "--port",
            type=int,
            default=8000,
            help="Port to bind (default: 8000)",
        )
        parser_web.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_web.set_defaults(func=_run_web)
        return parser_web

    def _register_gui(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'gui' subcommand to run the Qt GUI application.

        Args:
            subparsers: Subparsers action to register with.

        Returns:
            The configured subparser.
        """
        parser_gui = subparsers.add_parser(
            "gui",
            description="Run the Qt GUI application",
            help="Run the Qt GUI app",
            add_help=False,
        )
        parser_gui.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_gui.set_defaults(func=_run_gui)
        return parser_gui

    def _register_mcp(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'mcp' subcommand to run the MCP server.

        Args:
            subparsers: Subparsers action to register with.

        Returns:
            The configured subparser.
        """
        parser_mcp = subparsers.add_parser(
            "mcp",
            description="Run the Model Context Protocol (MCP) server for IP-XACT validation",
            help="Run the MCP server",
            add_help=False,
        )
        parser_mcp.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_mcp.set_defaults(func=_run_mcp)
        return parser_mcp

    def _register_version(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """Register the 'version' subcommand (just program version)."""
        parser_version = subparsers.add_parser(
            "version",
            description="Show CLI version",
            help="Show CLI version",
            add_help=False,
        )
        parser_version.add_argument(
            "-h",
            "--help",
            action=_RichSubHelpAction,
            nargs=0,
            help="Show this message and exit",
        )
        parser_version.set_defaults(func=_print_version)
        return parser_version

    return [
        CommandSpec("standards", "List supported schema versions", _register_standards),
        CommandSpec("identify", "Identify IP-XACT xml files", _register_identify),
        CommandSpec("validate", "Validate IP-XACT xml files", _register_validate),
        CommandSpec("registry", "Manage the in-memory VLNV registry", _register_registry),
        CommandSpec("convert", "Convert IP-XACT xml files", _register_convert),
        CommandSpec("web", "Run the FastAPI GUI web app", _register_web),
        CommandSpec("gui", "Run the Qt GUI app", _register_gui),
        CommandSpec("mcp", "Run the MCP server", _register_mcp),
        CommandSpec("version", "Show CLI version", _register_version),
    ]


## Removed legacy _commands_help helper; dynamic argparse introspection supplies command help.


def _print_version(args: argparse.Namespace) -> None:
    """Print CLI version only."""
    console.print(f"ipxact-de v{__version__}")


def _print_standards(args: argparse.Namespace) -> None:
    """Print supported SPIRIT/IP-XACT schema versions."""
    preferred_order = ["spirit", "ipxact"]
    all_versions = [f"{std}/{ver}" for std in preferred_order if std in STANDARDS for ver in STANDARDS[std].versions]
    console.print(Text("Supported standards:", style="heading"))
    for ver in all_versions:
        console.print(f"  {ARROW} [bright_cyan]{ver}[/bright_cyan]")


class _RegistryProgress:
    """Report loader phases on stderr without contaminating streamed registry output."""

    _LABELS = {
        "reading_cache": "Reading cache",
        "loading": "Loading inventory",
        "discovering": "Finding XML",
        "scanning": "Indexing XML",
        "reading_documents": "Reading XML",
        "completed": "Registry ready",
    }

    def __init__(self, label: str, enabled: bool = True, paths: tuple[Path, ...] = (), verbose: bool = False) -> None:
        self.label = label
        self.enabled = enabled
        self.verbose = verbose
        self.paths = tuple(path.expanduser().absolute() for path in paths)
        self.target = Console(stderr=True)
        self.started = monotonic()
        self.last_report = self.started
        self.stage = ""
        self.current = 0
        self.total = 0
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.target,
            transient=True,
            disable=not enabled or not self.target.is_terminal,
            redirect_stdout=False,
            redirect_stderr=False,
        )
        self.task = self.progress.add_task(label, total=None)

    def __enter__(self) -> Self:
        if self.enabled:
            self.progress.start()
            if not self.target.is_terminal:
                self.target.print(self.label + "...")
        return self

    def update(self, stage: str, current: int, total: int) -> None:
        if not self.enabled:
            return
        now = monotonic()
        changed = stage != self.stage
        self.stage, self.current, self.total = stage, current, total
        description = self._LABELS.get(stage, stage)
        live_description = f"{description} {current:,}" if not total and current else description
        self.progress.update(self.task, description=live_description, completed=current, total=total or None)
        if not self.target.is_terminal and (changed or now - self.last_report >= 1):
            count = f": {current:,}/{total:,}" if total else (f": {current:,} found" if current else "...")
            self.target.print(description + count)
            self.last_report = now

    def document(self, path: Path, root: str, standard: str, version: str) -> None:
        """Show the active XML path and one compact result line per parsed document."""
        if not self.enabled:
            return
        display = str(path)
        if not self.verbose:
            for source in self.paths:
                base = source.parent if source.suffix.lower() == ".xml" else source
                if path.is_relative_to(base):
                    display = str(path.relative_to(base))
                    break
        if not root:
            self.progress.update(self.task, description=f"Read {path.name}")
            return
        family = "IP-XACT" if standard.lower() == "ipxact" else standard.upper()
        details = f"{family} {version} {root}"
        if not self.verbose:
            width = max(10, self.target.width - len(details) - 2)
            if len(display) > width:
                display = "..." + display[-(width - 3) :]
        self.target.print(Text.assemble((display, "cyan"), "  ", (details, "dim")), soft_wrap=True)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> None:
        if self.enabled:
            self.progress.stop()
            if exc_type is None:
                count = f" ({self.current:,}/{self.total:,})"
                self.target.print(f"{self.label}{count}: {monotonic() - self.started:.2f}s")


def _run_scan(args: argparse.Namespace) -> None:
    """Execute the 'scan' command.

    Gathers command-level paths (supports colon-separated entries and repeats),
    triggers a registry scan, and prints a short completion message.
    """
    paths: list[str] = list(getattr(args, "paths", []) or [])
    if not paths:
        # No arguments provided: show the scan command help and exit.
        scan_parser: argparse.ArgumentParser = getattr(args, "__scan_parser")  # type: ignore[assignment]
        parts = scan_parser.prog.split()
        parent_prog = parts[0] if parts else "ipxact-de"
        subname = " ".join(parts[1:]) if len(parts) > 1 else "registry scan"
        _print_subcommand_help(parent_prog, subname, scan_parser)
        return
    enabled = not (getattr(args, "quiet", False) or getattr(args, "silent", False))
    with _RegistryProgress(
        "Registry scan", enabled, tuple(Path(path) for path in paths), bool(getattr(args, "verbose", False))
    ) as status:
        load_registry_from_paths(paths, progress=status.update, document_reporter=status.document)
    count = sum(1 for _ in _get_registry().iter_documents())
    console.print(f"Scan completed. {count:,} documents registered.")


def _run_validate(args: argparse.Namespace) -> None:
    """Execute the 'validate' command.

    If invoked without any XML files, display the subcommand help. Otherwise,
    delegate to the existing validate_xml handler.

    Args:
        args: Parsed CLI arguments.
    """
    xml_files = getattr(args, "xml-files", [])
    if not xml_files:
        validate_parser: argparse.ArgumentParser = getattr(args, "__validate_parser")  # type: ignore[assignment]
        parts = validate_parser.prog.split()
        parent_prog = parts[0] if parts else "ipxact-de"
        _print_subcommand_help(parent_prog, "validate", validate_parser)
        return
    # With files provided, run the standard validate flow.
    validate_xml(args)


def _run_convert(args: argparse.Namespace) -> None:
    """Execute the 'convert' command.

    If invoked without any XML files, display the subcommand help. Otherwise,
    delegate to the existing convert_xml handler.

    Args:
        args: Parsed CLI arguments.
    """
    xml_files = getattr(args, "xml-files", [])
    if not xml_files:
        convert_parser: argparse.ArgumentParser = getattr(args, "__convert_parser")  # type: ignore[assignment]
        parts = convert_parser.prog.split()
        parent_prog = parts[0] if parts else "ipxact-de"
        _print_subcommand_help(parent_prog, "convert", convert_parser)
        return
    # With files provided, run the standard convert flow.
    convert_xml(args)


class _RegistryOutput:
    """Write bounded batches of literal styled rows or unwrapped plain text."""

    def __init__(self, target: Console, plain: bool) -> None:
        self.target = target
        self.plain = plain
        self.lines: list[Text] = []

    def write(self, *parts: tuple[str, str] | str) -> None:
        line = Text.assemble(*parts)
        self.lines.append(line)
        if len(self.lines) >= 256:
            self.flush()

    def flush(self) -> None:
        if not self.lines:
            return
        if self.plain:
            self.target.file.write("".join(line.plain + "\n" for line in self.lines))
            self.target.file.flush()
        else:
            self.target.print(Text("\n").join(self.lines), soft_wrap=True)
        self.lines.clear()


def _run_registry_list(args: argparse.Namespace) -> None:
    """List saved registry entries as a Vendor:Library:Name:Version tree.

    registry scan updates the saved inventory; listing reads metadata without checking source files.

    Optional pattern filtering: 'vendor:library:name:version'. Without --regex, uses
    case-insensitive substring matching and allows '*' to match anything for a part.
    With --regex, treats each provided part as a regular expression (empty/omitted matches all).

    Optional type filtering: use --type to show only entries of a specific IP-XACT element type.
    """
    # Listing reads the saved inventory; registry scan updates its source paths.
    if not any(True for _ in _get_registry().iter_documents()):
        enabled = not (getattr(args, "quiet", False) or getattr(args, "silent", False))
        with _RegistryProgress("Registry loading", enabled) as status:
            load_registry_from_cache(validate_files=False, progress=status.update)
    pattern = getattr(args, "pattern", None)
    use_regex = bool(getattr(args, "regex", False))
    type_filter = getattr(args, "type", None)
    vendor_pat = library_pat = name_pat = version_pat = None
    rx_vendor = rx_library = rx_name = rx_version = None
    if pattern:
        parts = pattern.split(":", 3)
        parts += [None] * (4 - len(parts))
        vendor_pat, library_pat, name_pat, version_pat = parts
        # Normalize wildcards / empties
        if use_regex:

            def _compile(p: str | None) -> re.Pattern[str] | None:
                if p is None or p == "":
                    return None
                if p == "*":
                    p = ".*"
                return re.compile(p)

            try:
                rx_vendor = _compile(vendor_pat)
                rx_library = _compile(library_pat)
                rx_name = _compile(name_pat)
                rx_version = _compile(version_pat)
            except re.error as ex:  # pragma: no cover - safety
                console.print(f"Invalid regex in pattern: {ex}")
                return
        else:
            vendor_pat = None if vendor_pat in (None, "*") else vendor_pat.lower()
            library_pat = None if library_pat in (None, "*") else library_pat.lower()
            name_pat = None if name_pat in (None, "*") else name_pat.lower()
            version_pat = None if version_pat in (None, "*") else version_pat.lower()
    # Build nested dict: vendor -> library -> name -> set(versions)
    tree: dict[str, dict[str, dict[str, set[str]]]] = {}
    types_by_key: dict[tuple[str, str, str, str], str] = {}
    editions_by_key: dict[tuple[str, str, str, str], str] = {}
    registry_api = _get_registry()
    for handle in registry_api.iter_documents():
        vlnv = registry_api.get_vlnv(handle)
        if not vlnv:
            continue
        vendor, library, name, version = vlnv
        # Filter by type if specified
        if type_filter:
            element_type = _get_type_for_handle(handle)
            # Convert user-friendly camelCase to PascalCase for comparison
            expected_type = type_filter[0].upper() + type_filter[1:]
            if element_type != expected_type:
                continue
        # Filter if needed
        if pattern:
            if use_regex:

                def ok(rx: re.Pattern[str] | None, val: str) -> bool:
                    return True if rx is None else bool(rx.search(val))

                if not ok(rx_vendor, vendor):
                    continue
                if not ok(rx_library, library):
                    continue
                if not ok(rx_name, name):
                    continue
                if not ok(rx_version, version):
                    continue
            else:

                def ok(p: str | None, val: str) -> bool:
                    return True if p is None else (p in val.lower())

                if not ok(vendor_pat, vendor):
                    continue
                if not ok(library_pat, library):
                    continue
                if not ok(name_pat, name):
                    continue
                if not ok(version_pat, version):
                    continue
        libs = tree.setdefault(vendor, {})
        names = libs.setdefault(library, {})
        versions = names.setdefault(name, set())
        versions.add(version)
        # Capture document type and schema edition for each complete VLNV.
        key = (vendor, library, name, version)
        types_by_key[key] = _get_type_for_handle(handle) or ""
        info = registry_api.get_document_info(handle)
        if info is not None and info.standard and info.schema_version:
            family = "IP-XACT" if info.standard == "ipxact" else info.standard.upper()
            editions_by_key[key] = f"{family} {info.schema_version}"
        else:
            editions_by_key[key] = "Unknown edition"

    max_type_width = max((len(name) for name in types_by_key.values()), default=0)

    # Render
    color = getattr(args, "color", "auto")
    target = console
    if color == "always":
        target = Console(
            file=console.file,
            theme=_CLI_THEME,
            force_terminal=True,
            color_system="standard",
            no_color=False,
            highlight=False,
            width=console.width,
        )
    plain = bool(getattr(args, "plain", False)) or color == "never" or not target.is_terminal
    output = _RegistryOutput(target, plain)
    output.write(("Registry:", "heading"))
    as_flat = bool(getattr(args, "flat", False))
    # Sort case-insensitively by vendor, then by library, then by name
    if as_flat:
        # Precompute max prefix width (vendor:library:name:version) for alignment
        lines: list[tuple[str, str, str, str, str]] = []  # (vendor, library, name, version, type)
        for vendor in sorted(tree, key=lambda s: s.casefold()):
            for library in sorted(tree[vendor], key=lambda s: s.casefold()):
                for name in sorted(tree[vendor][library], key=lambda s: s.casefold()):
                    for version in sorted(tree[vendor][library][name], key=_natural_key):
                        tname = types_by_key.get((vendor, library, name, version), "")
                        lines.append((vendor, library, name, version, tname))

        def _prefix_len(v: str, lib: str, n: str, ver: str) -> int:
            return len(v) + 1 + len(lib) + 1 + len(n) + 1 + len(ver)

        max_prefix = max((_prefix_len(v, lib, n, ver) for v, lib, n, ver, _t in lines), default=0)
        for vendor, library, name, version, tname in lines:
            # Calculate padding so that type starts at same column
            pad_spaces = max_prefix - _prefix_len(vendor, library, name, version) + 1  # at least one space
            pad = " " * pad_spaces
            output.write(
                "  ",
                (vendor, "vlnv.vendor"),
                (":", "vlnv.sep"),
                (library, "vlnv.library"),
                (":", "vlnv.sep"),
                (name, "vlnv.name"),
                (":", "vlnv.sep"),
                (version, "vlnv.version"),
                pad,
                (f"{tname:<{max_type_width}}", "vlnv.type"),
                "  ",
                (editions_by_key[(vendor, library, name, version)], "dim"),
            )
    else:
        # Compute global max name and version lengths to align the type column
        max_ver_len_all = 0
        max_name_len_all = 0
        for vnd in tree:
            for lib in tree[vnd]:
                for nm in tree[vnd][lib]:
                    max_name_len_all = max(max_name_len_all, len(nm))
                    for ver in tree[vnd][lib][nm]:
                        max_ver_len_all = max(max_ver_len_all, len(ver))
        for vendor in sorted(tree, key=lambda s: s.casefold()):
            output.write("  ", (vendor, "vlnv.vendor"))
            for library in sorted(tree[vendor], key=lambda s: s.casefold()):
                output.write("    ", (library, "vlnv.library"))
                for name in sorted(tree[vendor][library], key=lambda s: s.casefold()):
                    output.write("      ", (name, "vlnv.name"))
                    # Align types after versions using a global column to the right of both
                    # the longest name and the longest version to avoid visual overlap
                    versions_sorted = sorted(tree[vendor][library][name], key=_natural_key)
                    name_indent_len = 6  # spaces before name line
                    ver_indent = " " * 8  # spaces before version lines
                    ver_indent_len = 8
                    # The type column starts after the greater of (name column end, version column end)
                    type_col = max(name_indent_len + max_name_len_all + 1, ver_indent_len + max_ver_len_all + 1)
                    for version in versions_sorted:
                        # Pad so ver_indent_len + len(version) + pad == type_col
                        pad_spaces = type_col - (ver_indent_len + len(version))
                        if pad_spaces < 1:
                            pad_spaces = 1
                        pad = " " * pad_spaces
                        tname = types_by_key.get((vendor, library, name, version), "")
                        output.write(
                            ver_indent,
                            (version, "vlnv.version"),
                            pad,
                            (f"{tname:<{max_type_width}}", "vlnv.type"),
                            "  ",
                            (editions_by_key[(vendor, library, name, version)], "dim"),
                        )
    output.flush()


# (Removed legacy registry 'search' subcommand; list now supports filtering and regex.)


def _run_registry(args: argparse.Namespace) -> None:
    """Default registry handler: show 'registry' help when no subcommand is provided.

    Args:
        args: Parsed CLI arguments.
    """
    reg_parser: argparse.ArgumentParser = getattr(args, "__registry_parser")  # type: ignore[assignment]
    parts = reg_parser.prog.split()
    parent_prog = parts[0] if parts else "ipxact-de"
    _print_subcommand_help(parent_prog, "registry", reg_parser)


def _run_web(args: argparse.Namespace) -> None:
    """Run the FastAPI GUI web app via Uvicorn.

    Args:
        args: Parsed CLI arguments containing 'host' and 'port'.
    """
    host: str = getattr(args, "host", "localhost")
    port: int = int(getattr(args, "port", 8000) or 8000)
    try:
        import uvicorn  # type: ignore[import-not-found]
    except Exception:
        console.print("Uvicorn is not installed. Install it via 'uv add uvicorn' or 'pip install uvicorn' and retry.")
        return
    # Use module path to the ASGI app to avoid import cycles.
    uvicorn.run(
        "amal.eda.ipxact_de.web:app",
        host=host,
        port=port,
        reload=True,
    )


def _run_gui(args: argparse.Namespace) -> None:
    """Run the Qt GUI application.

    Args:
        args: Parsed CLI arguments (unused).
    """
    # try:
    #     # Import lazily to avoid importing Qt unless requested
    #     from amal.eda.ipxact_de.gui import main as gui_main  # type: ignore
    # except Exception as ex:  # pragma: no cover - environment dependent
    #     console.print(
    #         "GUI dependencies are not installed. Install extras via 'uv add pyipxact-de[gui]' "
    #         "or 'pip install qtpy pyqt5'."
    #     )
    #     console.print(f"Details: {ex}")
    #     return
    from amal.eda.ipxact_de.gui import main as gui_main  # type: ignore

    gui_main()


def _run_mcp(args: argparse.Namespace) -> None:
    """Run the Model Context Protocol (MCP) server.

    Args:
        args: Parsed CLI arguments (unused).
    """
    try:
        # Import lazily to avoid dependencies unless requested
        from amal.eda.ipxact_de.mcp.server import main as mcp_main  # type: ignore
    except Exception as ex:  # pragma: no cover - environment dependent
        console.print("MCP dependencies are not installed. Install them via 'uv add mcp' or 'pip install mcp'.")
        console.print(f"Details: {ex}")
        return
    mcp_main()


def main() -> None:
    """Run the CLI, exiting quietly with status 130 when interrupted."""
    try:
        _main()
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except BrokenPipeError:
        # Discard buffered output after a downstream consumer closes the pipe.
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        raise SystemExit(0) from None


def _main() -> None:
    """Main entry point for the IP-XACT CLI."""

    # logger.trace("TRACE")
    # logger.debug("DEBUG")
    # logger.info("INFO")
    # logger.success("SUCCESS")
    # logger.warning("WARNING")
    # logger.error("ERROR")
    # try:
    #     1 / 0
    # except ZeroDivisionError:
    #     logger.exception("EXCEPTION")
    # logger.critical("CRITICAL")

    parser = argparse.ArgumentParser(
        prog="ipxact-de",
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Text at the bottom of help",
        add_help=False,
    )
    # Add global & logging options (captured into sections immediately below)
    help_action = parser.add_argument("-h", "--help", action="store_true", help="Show this message and exit")
    verbose_action = parser.add_argument("-v", "--verbose", action="count", default=0, help="Enable verbose logging")
    quiet_action = parser.add_argument("-q", "--quiet", action="store_true", help="Print diagnostics, but nothing else")
    silent_action = parser.add_argument("-s", "--silent", action="store_true", help="Disable all logging")
    # Note: Positional paths are supported for the 'scan' subcommand; no global paths option.
    version_action = parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s v{__version__}",
        help="Show version and exit",
    )
    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    # Build versions list (shared) once
    preferred_order = ["spirit", "ipxact"]
    all_versions = [f"{std}/{ver}" for std in preferred_order if std in STANDARDS for ver in STANDARDS[std].versions]

    # Register primary command specs
    specs = _build_command_specs(all_versions)
    subparser_map: dict[str, argparse.ArgumentParser] = {}
    for spec in specs:
        subparser_map[spec.name] = spec.register(subparsers)

    def _help_handler(args: argparse.Namespace | None = None) -> None:  # noqa: D401 - short internal handler
        """Help handler for 'help' subcommand or top-level help."""
        subcmd = getattr(args, "subcommand_name", None) if args else None
        if not subcmd:
            _print_top_level_help(parser)
            return
        if subcmd in subparser_map:
            _print_subcommand_help(parser.prog, subcmd, subparser_map[subcmd])
        else:
            sys.stderr.write(f"Unknown command '{subcmd}'. Available: {', '.join(sorted(subparser_map))}.\n")
            _print_top_level_help(parser)

    # Help subcommand registration (after others so map is populated)
    # Help command (must be added before building command sections so it shows up)
    parser_help = subparsers.add_parser(
        "help",
        description="Print this message or get help for subcommand",
        help="Print this message or get help for subcommand",
        add_help=False,
    )
    parser_help.add_argument(
        "subcommand_name",
        nargs="?",
        help="Subcommand to show help for (identify, validate, convert, standards, version)",
    )
    parser_help.add_argument("-h", "--help", action=_RichSubHelpAction, nargs=0, help="Show this message and exit")
    parser_help.set_defaults(func=_help_handler)
    # Track help command for section population
    subparser_map["help"] = parser_help

    # Register metadata for global options (id-based registry to avoid mutating Action objects)
    _ACTION_METADATA[id(help_action)] = ("Global options:", 40)
    _ACTION_METADATA[id(version_action)] = ("Global options:", 40)
    #
    _ACTION_METADATA[id(verbose_action)] = ("Log levels:", 20)
    _ACTION_METADATA[id(quiet_action)] = ("Log levels:", 20)
    _ACTION_METADATA[id(silent_action)] = ("Log levels:", 20)

    # Pre-parse guard: if the first non-flag token is not a known command,
    # show styled help and a concise diagnostic instead of argparse's error.
    argv = sys.argv[1:]
    first_non_flag: str | None = next((t for t in argv if not t.startswith("-")), None)
    if first_non_flag is not None and first_non_flag not in subparser_map:
        console.print(f"Invalid command '{first_non_flag}'.")
        console.print()
        _print_top_level_help(parser)
        sys.exit(2)

    # Special-case: unknown registry subcommand -> show styled registry help
    if first_non_flag == "registry":
        # Determine the next non-flag token after 'registry'
        try:
            idx = next(i for i, t in enumerate(argv) if t == "registry")
        except StopIteration:
            idx = -1
        if idx != -1:
            rest = argv[idx + 1 :]
            # Skip flags like -h/--help etc., take the first positional
            second_non_flag = next((t for t in rest if not t.startswith("-")), None)
            if second_non_flag is not None:
                # Discover allowed registry subcommands from the parser to avoid duplication
                reg_parser = subparser_map.get("registry")
                allowed: set[str] = set()
                if reg_parser is not None:
                    for action in reg_parser._actions:  # type: ignore[attr-defined]
                        if isinstance(action, argparse._SubParsersAction):  # type: ignore[attr-defined]
                            allowed.update(action._name_parser_map.keys())  # type: ignore[attr-defined]
                if second_non_flag not in allowed:
                    console.print(f"Invalid subcommand '{second_non_flag}' for 'registry'.")
                    console.print()
                    _print_subcommand_help(parser.prog, "registry", reg_parser)  # type: ignore[arg-type]
                    sys.exit(2)

    args = parser.parse_args()
    # print(vars(args))

    # Explicit scans manage their own paths; listing reads the saved inventory.
    # Other commands discover documents only when search paths are configured.
    is_registry_scan = getattr(args, "subcommand", None) == "registry" and getattr(args, "registry_cmd", None) == "scan"
    is_registry_list = getattr(args, "subcommand", None) == "registry" and getattr(args, "registry_cmd", None) == "list"
    if not is_registry_scan and not is_registry_list and os.environ.get("IPXACT_XML_PATHS", "").strip():
        try:
            load_registry_from_paths([])
        except Exception:  # pragma: no cover - defensive startup
            from amal.utilities import logger

            logger.exception("Registry scan failed")

    # Subcommand help via generic -h on parent (only when subcommand chosen and it's not 'help').
    if getattr(args, "help", False) and getattr(args, "subcommand", None) is not None:
        if args.subcommand == "help":
            # Emulate styled help for the help command itself
            _print_subcommand_help(parser.prog, "help", subparser_map["help"])  # type: ignore[index]
        else:
            _print_subcommand_help(parser.prog, args.subcommand, subparser_map[args.subcommand])  # type: ignore[index]
        return

    # Per-subcommand help flag (from subparser definitions)
    if getattr(args, "help_sub", False):  # type: ignore[attr-defined]
        _print_subcommand_help(parser.prog, args.subcommand, subparser_map[args.subcommand])  # type: ignore[index]
        return

    # Top-level help handling (matches Click styling)
    if getattr(args, "help", False) and getattr(args, "subcommand", None) is None:
        _print_top_level_help(parser)
        return

    # If no subcommand, print styled help instead of error
    if args.subcommand is None:
        _print_top_level_help(parser)
        return

    # (Legacy per-subcommand -h removed) show_help_sub no longer used.

    args.func(args)
