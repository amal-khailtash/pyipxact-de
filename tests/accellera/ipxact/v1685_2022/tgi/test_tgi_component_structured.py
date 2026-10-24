"""Structured component factories follow WSDL signatures and generated choices."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import component as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, get_parent_info, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component


@pytest.fixture
def root():
    return get_handle(Component(vendor="v", library="l", name="c", version="1"))


@pytest.mark.parametrize("kind", ["interface", "struct", "union"])
@pytest.mark.parametrize("parsed", [False, True])
def test_structured_xml_ownership_and_removal(root, kind, parsed):
    first = api.addComponentWirePort(root, "sibling", "in")
    if kind == "interface":
        port_id = api.addComponentStructuredInterfacePort(root, "p", "TYPE")
    elif kind == "struct":
        port_id = api.addComponentStructuredStructPort(root, "p", "TYPE", "out")
    else:
        port_id = api.addComponentStructuredUnionPort(root, "p", "TYPE", "member", "inout")
    assert api.getComponentPortIDs(root) == [first, port_id]
    structured = resolve_handle(port_id).wire_or_transactional_or_structured
    definition = structured.struct_port_type_defs.struct_port_type_def[0]
    assert definition.type_name.value == "TYPE"
    assert get_parent_info(get_handle(definition)).parent_handle == get_handle(structured)
    assert (structured.sub_ports is not None) is (kind == "union")
    if kind == "union":
        assert structured.sub_ports.sub_port[0].name == "member"
    xml = XmlDocument.serializer().render(resolve_handle(root))
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    loaded = XmlDocument.parser().from_string(xml, Component)
    assert loaded == resolve_handle(root)
    if parsed:
        root = get_handle(loaded)
        first, port_id = api.getComponentPortIDs(root)
        structured = resolve_handle(port_id).wire_or_transactional_or_structured
        definition = structured.struct_port_type_defs.struct_port_type_def[0]
    descendant_id = get_handle(definition.type_name)
    assert api.removeComponentPort(port_id)
    assert resolve_handle(descendant_id) is None
    assert resolve_handle(first) is not None


@pytest.mark.parametrize("operation", [
    lambda root: api.addComponentStructuredInterfacePort(root, "", "T"),
    lambda root: api.addComponentStructuredInterfacePort(root, "p", None),
    lambda root: api.addComponentStructuredStructPort(root, "p", "T", "bad"),
    lambda root: api.addComponentStructuredUnionPort(root, "p", "T", "", "in"),
    lambda root: api.addComponentStructuredUnionPort(root, "p", "T", "s", "bad"),
])
def test_invalid_arguments_are_atomic(root, operation):
    with pytest.raises(TgiError):
        operation(root)
    assert resolve_handle(root).model is None


@pytest.mark.parametrize("direction", ["in", "out", "inout", "phantom"])
def test_struct_and_union_directions(root, direction):
    first = api.addComponentStructuredStructPort(root, "s", "T", direction)
    second = api.addComponentStructuredUnionPort(root, "u", "T", "member", direction)
    for handle in (first, second):
        choice = resolve_handle(handle).wire_or_transactional_or_structured.struct_or_union_or_interface
        assert choice.direction.value == direction
