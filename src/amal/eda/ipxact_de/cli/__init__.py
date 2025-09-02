import argparse
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from amal.utilities import ARROW, logger
from org.accellera.standard import STANDARDS

from .commands import convert_xml, identify_xml, validate_xml
from .. import __description__, __version__
from ..loader import load_registry_from_cache, load_registry_from_paths
from ..tgi.ipxact.v1685_2022.core import registry

# Global Rich console (single theme) reused for all help rendering.
console = Console(
    theme=Theme(
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
    ),
    highlight=False,
)


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
    t = registry.get_element_type(handle)
    return t or ""


class _RichSubHelpAction(argparse.Action):
    """Custom help action for subcommands to show Rich-styled help and exit early.

    This avoids argparse enforcing required positionals before displaying help.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values=None,
        option_string: str | None = None,
    ) -> None:  # type: ignore[override]
        parts = parser.prog.split()
        parent_prog = parts[0] if parts else 'ipxact'
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
                and not isinstance(
                    action, argparse._StoreTrueAction | argparse._StoreFalseAction
                )
            )
            if not action.option_strings or isinstance(
                action, argparse._StoreTrueAction | argparse._StoreFalseAction
            ):
                needs_value = False
            if needs_value:
                placeholder = action.metavar or action.dest.upper().replace('-', '_')
                flags_display = f"{flags} {placeholder}"
            else:
                flags_display = flags
            options.append((flags_display, help_text))
        else:
            # Positional argument; metavar can be a tuple for multiple values.
            raw_meta = action.metavar or action.dest.upper().replace('-', '_')
            placeholder = " ".join(str(m) for m in raw_meta) if isinstance(raw_meta, tuple) else str(raw_meta)
            positional.append((placeholder, help_text))

    # Header / description: print top-level description then subcommand description (if any) before usage
    desc = subparser.description or next(
        (
            a.help
            for a in getattr(subparser, "_actions", [])
            if isinstance(a, argparse._HelpAction)
        ),
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
                "List registry entries (tree by default). "
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
            "--overwrite",
            action="store_true",
            help="Force overwrite of the output file if it exists"
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
        CommandSpec("version", "Show CLI version", _register_version),
    ]


## Removed legacy _commands_help helper; dynamic argparse introspection supplies command help.


def _print_version(args: argparse.Namespace) -> None:
    """Print CLI version only."""
    console.print(f"ipxact v{__version__}")


def _print_standards(args: argparse.Namespace) -> None:
    """Print supported SPIRIT/IP-XACT schema versions."""
    preferred_order = ["spirit", "ipxact"]
    all_versions = [
        f"{std}/{ver}"
        for std in preferred_order
        if std in STANDARDS
        for ver in STANDARDS[std].versions
    ]
    console.print(Text("Supported standards:", style="heading"))
    for ver in all_versions:
        console.print(f"  {ARROW} [bright_cyan]{ver}[/bright_cyan]")


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
        parent_prog = parts[0] if parts else "ipxact"
        subname = " ".join(parts[1:]) if len(parts) > 1 else "registry scan"
        _print_subcommand_help(parent_prog, subname, scan_parser)
        return
    load_registry_from_paths(paths)
    console.print("Scan completed.")


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
        parent_prog = parts[0] if parts else "ipxact"
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
        parent_prog = parts[0] if parts else "ipxact"
        _print_subcommand_help(parent_prog, "convert", convert_parser)
        return
    # With files provided, run the standard convert flow.
    convert_xml(args)


def _run_registry_list(args: argparse.Namespace) -> None:
    """List registry entries as a Vendor:Library:Name:Version tree.

    Optional pattern filtering: 'vendor:library:name:version'. Without --regex, uses
    case-insensitive substring matching and allows '*' to match anything for a part.
    With --regex, treats each provided part as a regular expression (empty/omitted matches all).
    """
    # If registry is empty, attempt to load from local cache.
    any_entries = any(True for _ in registry.iter_by_predicate(lambda _r: True))
    if not any_entries:
        load_registry_from_cache()
    pattern = getattr(args, "pattern", None)
    use_regex = bool(getattr(args, "regex", False))
    vendor_pat = library_pat = name_pat = version_pat = None
    rx_vendor = rx_library = rx_name = rx_version = None
    if pattern:
        parts = pattern.split(":", 3)
        parts += [None] * (4 - len(parts))
        vendor_pat, library_pat, name_pat, version_pat = parts
        # Normalize wildcards / empties
        if use_regex:
            def _compile(p: str | None):
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
    types_by_key: dict[tuple[str, str, str], str] = {}
    for handle in registry.iter_by_predicate(lambda _r: True):
        vlnv = registry.get_vlnv(handle)
        if not vlnv:
            continue
        vendor, library, name, version = vlnv
        # Filter if needed
        if pattern:
            if use_regex:
                def ok(rx, val: str) -> bool:
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
        # Capture element type per (vendor, library, name)
        key = (vendor, library, name)
        if key not in types_by_key:
            types_by_key[key] = _get_type_for_handle(handle) or ""

    # Render
    console.print(Text("Registry:", style="heading"))
    as_flat = bool(getattr(args, "flat", False))
    # Sort case-insensitively by vendor, then by library, then by name
    if as_flat:
        # Precompute max prefix width (vendor:library:name:version) for alignment
        lines: list[tuple[str, str, str, str, str]] = []  # (vendor, library, name, version, type)
        for vendor in sorted(tree, key=lambda s: s.casefold()):
            for library in sorted(tree[vendor], key=lambda s: s.casefold()):
                for name in sorted(tree[vendor][library], key=lambda s: s.casefold()):
                    for version in sorted(tree[vendor][library][name], key=_natural_key):
                        tname = types_by_key.get((vendor, library, name), "")
                        lines.append((vendor, library, name, version, tname))
        def _prefix_len(v: str, lib: str, n: str, ver: str) -> int:
            return len(v) + 1 + len(lib) + 1 + len(n) + 1 + len(ver)
        max_prefix = max((_prefix_len(v, lib, n, ver) for v, lib, n, ver, _t in lines), default=0)
        for vendor, library, name, version, tname in lines:
            # Calculate padding so that type starts at same column
            pad_spaces = max_prefix - _prefix_len(vendor, library, name, version) + 1  # at least one space
            pad = " " * pad_spaces
            console.print(
                "  "
                f"[vlnv.vendor]{vendor}[/]"
                f"[vlnv.sep]:[/]"
                f"[vlnv.library]{library}[/]"
                f"[vlnv.sep]:[/]"
                f"[vlnv.name]{name}[/]"
                f"[vlnv.sep]:[/]"
                f"[vlnv.version]{version}[/]"
                f"{pad}[vlnv.type]{tname}[/]"
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
            console.print(f"  [vlnv.vendor]{vendor}[/]")
            for library in sorted(tree[vendor], key=lambda s: s.casefold()):
                console.print(f"    [vlnv.library]{library}[/]")
                for name in sorted(tree[vendor][library], key=lambda s: s.casefold()):
                    console.print(f"      [vlnv.name]{name}[/]")
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
                        tname = types_by_key.get((vendor, library, name), "")
                        console.print(
                            f"{ver_indent}[vlnv.version]{version}[/]{pad}[vlnv.type]{tname}[/]"
                        )


# (Removed legacy registry 'search' subcommand; list now supports filtering and regex.)


def _run_registry(args: argparse.Namespace) -> None:
    """Default registry handler: show 'registry' help when no subcommand is provided.

    Args:
        args: Parsed CLI arguments.
    """
    reg_parser: argparse.ArgumentParser = getattr(args, "__registry_parser")  # type: ignore[assignment]
    parts = reg_parser.prog.split()
    parent_prog = parts[0] if parts else "ipxact"
    _print_subcommand_help(parent_prog, "registry", reg_parser)


def main() -> None:
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
        prog="ipxact",
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
    all_versions = [
        f"{std}/{ver}"
        for std in preferred_order
        if std in STANDARDS
        for ver in STANDARDS[std].versions
    ]

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

    args = parser.parse_args()
    # print(vars(args))

    # Trigger repository scan early for all commands except 'registry scan'.
    # For 'registry scan', the handler will manage scanning and help behavior.
    is_registry_scan = getattr(args, "subcommand", None) == "registry" and getattr(args, "registry_cmd", None) == "scan"
    if not is_registry_scan:
        try:
            load_registry_from_paths([])
        except Exception:  # pragma: no cover - defensive startup
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
