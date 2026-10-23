import argparse
import os
import tempfile
from pathlib import Path

from rich import print

from amal.eda.ipxact_de.xml_document import XmlDocument
from amal.utilities import ARROW, XmlTranslator
from org.accellera import TRANSFORMATIONS


def identify_xml(args: argparse.Namespace) -> None:
    print("=" * 120)

    xml_files = getattr(args, "xml-files")
    for xml_file in xml_files:
        print(f"{ARROW} Identifying XML file: {xml_file.name} ...")
        _doc = XmlDocument(Path(xml_file.name))
        print("  " + "-" * 80)

    print("=" * 120)


def validate_xml(args: argparse.Namespace) -> None:
    """Validate every input and exit unsuccessfully if any document fails."""
    from rich.console import Console

    from amal.eda.ipxact_de.xml_validation import validate_ipxact_xml

    console = Console()
    failed = False
    for xml_file in getattr(args, "xml-files"):
        result = validate_ipxact_xml(
            Path(xml_file.name), schema_root=getattr(args, "schema_root", None),
            semantic=getattr(args, "semantic", False),
        )
        console.print(f"{xml_file.name}: {'valid' if result.ok else 'invalid'}", markup=False)
        if result.checked_semantic_rules:
            console.print("Checked semantic rules: " + ", ".join(result.checked_semantic_rules), markup=False)
        for issue in result.issues:
            location = f"line {issue.line}: " if issue.line is not None else ""
            rule = f"{issue.rule_id}: " if issue.rule_id else ""
            path = f" ({issue.path})" if issue.path else ""
            console.print(f"  {location}{rule}{issue.message}{path}", markup=False)
        failed |= not result.ok
    if failed:
        raise SystemExit(1)


def get_transformations_paths(from_version: str, to_version: str) -> list[tuple[str, str, str]]:
    print(f"{ARROW} Getting transformation paths from '{from_version}' to '{to_version}' ...")
    paths: list[tuple[str, str, str]] = []
    for start, end, xsls in TRANSFORMATIONS:
        # print(f"  {ARROW} {start:10} ➜ {end:20} : {xsls}")
        if start == from_version:
            for xsl in xsls:
                paths.append((start, end, xsl))

            from_version = end  # .removesuffix("_abstractionDef")
            if end == to_version:
                break
    return paths


def run_transformation(input_file: str, output_file: str, xsl_file: str) -> None:
    # import lxml.etree as ET
    # dom = ET.parse(xml_filename)
    # xslt = ET.parse(xsl_filename)
    # transform = ET.XSLT(xslt)
    # newdom = transform(dom)
    # print(ET.tostring(newdom, pretty_print=True))

    xml_translator = XmlTranslator(xsl_file, use_lxml=False)

    xml_translator.transform(input_file, output_file, xsl_file)

    # env = dict(os.environ)
    # env.pop("LD_LIBRARY_PATH", None)

    # # env = {k: v for k, v in os.environ.items() if k != "LD_LIBRARY_PATH"}

    # command = ["xsltproc", "--output", output_file, xsl_file, input_file]
    # # print(f"  {ARROW} Running command: {" ".join(command)} ...")

    # try:
    #     subprocess.check_output(command, text=True, env=env)
    # except subprocess.CalledProcessError:
    #     pass

    # subprocess.run(
    #     command,
    #     stdout=open(output_file, "w"),
    #     env=env
    # )


def convert_xml(args: argparse.Namespace) -> None:
    print("=" * 120)

    # Support both legacy plain version (e.g. "1685-2022") and new
    # "standard/version" form; normalize to just the version string for
    # transformation path lookup (which expects bare versions).
    to_arg = args.to_version
    if to_arg and "/" in to_arg:
        _, version_to = to_arg.split("/", 1)
    else:
        version_to = to_arg
    xml_files = getattr(args, "xml-files")
    # xml_filename_out = getattr(args, "output-file")
    # output_dir = getattr(args, "output-dir")

    output_dir_path = Path(args.output_dir)
    if not output_dir_path.exists():
        output_dir_path.mkdir(parents=True, exist_ok=True)
    elif not args.overwrite:
        print(f"Error: Output directory '{args.output_dir}' exists!  Use --overwrite to overwrite.")
        return

    for xml_file in xml_files:
        xml_filename_in = xml_file.name
        xml_filename_out = output_dir_path / Path(xml_filename_in).name
        print("{ARROW} Converting XML file ...")
        print(f"    : '{xml_filename_in}'")
        print(f"    ➜ '{xml_filename_out}'")
        doc = XmlDocument(Path(xml_filename_in))
        # doc.version holds bare version (e.g. "1685-2022") after parsing
        version_from = doc.version or ""
        print(f"{ARROW} To Version: '{version_to}'")
        # version_from is already bare; no split needed. Earlier code attempted
        # to split a string like "1685-2022" causing IndexError; fixed.
        xsl_files = get_transformations_paths(version_from, version_to)
        if xsl_files:
            with tempfile.NamedTemporaryFile(delete=False, dir=output_dir_path, suffix=".xml") as temp_file:
                xml_filename_temp = temp_file.name
            xml_filename = xml_filename_in
            for v_from, v_to, xsl_file in xsl_files:
                print(f"  {ARROW} Transform: '{v_from}' ➜ '{v_to}' ...")
                run_transformation(xml_filename, xml_filename_temp, xsl_file)
                xml_filename = xml_filename_temp
            os.rename(xml_filename_temp, xml_filename_out)
        else:
            print(f"  {ARROW} Cannot transform '{version_from}' to '{version_to}'")
        print("  " + "-" * 80)

    print("=" * 120)
