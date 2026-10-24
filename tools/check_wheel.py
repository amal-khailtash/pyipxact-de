"""Check an installed pyipxact-de wheel without importing the source checkout."""

import argparse
import subprocess
import sys
from importlib import metadata, resources


def check_wheel(version: str) -> None:
    """Verify version, CLI, XML bindings, TGI access and bundled conversions.

    Args:
        version: Expected version of the installed release distribution.

    Raises:
        AssertionError: Installed behavior or package contents differ from the release.
        subprocess.CalledProcessError: The installed command-line entry point fails.
    """
    from amal.eda.accellera.ipxact.v1685_2022 import tgi
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_handle, registry
    from amal.eda.ipxact_de.xml_document import XmlDocument
    from amal.eda.systemverilog.expression_parser import SvExpressionParser
    from org.accellera.ipxact.v1685_2022 import Component

    assert metadata.version("pyipxact-de") == version
    result = subprocess.run(
        [sys.executable, "-m", "amal.eda.ipxact_de.cli", "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert version in result.stdout, result.stdout
    component = Component(vendor="release", library="test", name="wheel", version="1.0")
    xml = XmlDocument.serializer().render(component)
    loaded = XmlDocument.parser().from_string(xml, Component)
    assert (loaded.vendor, loaded.library, loaded.name, loaded.version) == ("release", "test", "wheel", "1.0")
    registry.clear()
    assert tgi.getName(get_handle(loaded)) == "wheel"
    assert tgi.getComponentPortIDs(get_handle(loaded)) == []
    registry.clear()
    assert SvExpressionParser().evaluate("8'hff + 1") == 256
    stylesheet = resources.files("org.accellera").joinpath("xsl", "from1685_2014_to_1685_2022.xsl")
    assert stylesheet.is_file(), "Released wheel must include standard conversion stylesheets"
    print(f"Installed pyipxact-de {version}: CLI, XML, TGI, expressions and conversions verified")


def main() -> None:
    """Run wheel-consumer validation using the version provided by publication."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    check_wheel(parser.parse_args().version)


if __name__ == "__main__":
    main()
