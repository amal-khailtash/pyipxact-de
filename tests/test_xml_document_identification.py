"""Document identity comes from namespace URIs, not chosen XML prefixes."""

import pytest

from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.standard import STANDARDS, Standard


@pytest.mark.parametrize("standard,version", [
    (meta.name, version) for meta in STANDARDS.values() for version in meta.versions
])
@pytest.mark.parametrize("prefix", [None, "custom", "ipxact", "spirit"])
def test_prefix_independent_identification(tmp_path, standard, version, prefix):
    namespace = Standard.ns_url_for(standard, version)
    tag = "component" if prefix is None else f"{prefix}:component"
    declaration = "xmlns" if prefix is None else f"xmlns:{prefix}"
    path = tmp_path / "component.xml"
    path.write_text(f'<{tag} {declaration}="{namespace}"/>')
    document = XmlDocument(path)
    assert document.root_name == "component"
    assert document.standard == standard.upper()
    assert document.version == version
    assert document.schema == namespace + "/index.xsd"
    assert document.is_ipxact is (standard == "ipxact")
    assert document.is_spirit is (standard == "spirit")


@pytest.mark.parametrize("root", ["busDefinition", "abstractionDefinition", "component", "abstractor",
                                   "design", "designConfiguration", "catalog", "generatorChain", "typeDefinitions"])
def test_root_namespace_wins_over_unused_declarations(tmp_path, root):
    path = tmp_path / "document.xml"
    path.write_text(f'<x:{root} xmlns:x="http://www.accellera.org/XMLSchema/IPXACT/1685-2022" '
                    'xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5" '
                    'xmlns:ipxact="urn:vendor:extension"/>')
    document = XmlDocument(path)
    assert document.standard == "IPXACT"
    assert document.version == "1685-2022"
    assert document.root_name == root


@pytest.mark.parametrize("namespace", ["urn:vendor:extension", "http://www.accellera.org/XMLSchema/IPXACT/2099",
                                       "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.3"])
def test_unsupported_namespace_leaves_retryable_state(tmp_path, namespace):
    path = tmp_path / "document.xml"
    path.write_text(f'<component xmlns="{namespace}"/>')
    document = XmlDocument(path, auto_parse=False)
    with pytest.raises(ValueError):
        document.parse()
    assert document.tree is None
    assert document.schema == ""
    path.write_text('<component xmlns="http://www.accellera.org/XMLSchema/IPXACT/1685-2022"/>')
    document.parse()
    assert document.version == "1685-2022"


def test_unused_known_prefix_cannot_identify_foreign_root(tmp_path):
    path = tmp_path / "foreign.xml"
    path.write_text('<foreign xmlns="urn:other" xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2022"/>')
    with pytest.raises(ValueError):
        XmlDocument(path)
