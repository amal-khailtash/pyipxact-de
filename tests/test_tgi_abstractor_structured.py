"""Structured abstractor creation preserves required child and type information."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstractor as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Abstractor
from org.accellera.ipxact.v1685_2022.abstractor_sub_port_type import AbstractorPortStructuredType as Structured


@pytest.fixture
def root():
    """Provide a model-free root with independent registry lifetime."""
    registry.clear()
    handle = top_element.createAbstractor(("v", "l", "a", "1"), "direct", ("v", "l", "b", "1"), "a", "b")
    yield handle
    registry.clear()


def create(root, kind, name="port", sub="member", type_name="Packet", direction="in"):
    """Call each operation with the standard argument ordering."""
    if kind == "interface":
        return api.addAbstractorStructuredInterfacePort(root, name, sub, type_name)
    if kind == "struct":
        return api.addAbstractorStructuredStructPort(root, name, sub, type_name, direction)
    return api.addAbstractorStructuredUnionPort(root, name, type_name, sub, direction)


@pytest.mark.parametrize("kind,model", [("interface", Structured.Interface), ("struct", Structured.Struct),
                                       ("union", Structured.UnionType)])
def test_required_children_round_trip_and_removal(root, kind, model):
    """Style, type name, and sub-port survive serialization with correct parents."""
    handle = create(root, kind)
    port = resolve_handle(handle)
    structured = port.wire_or_transactional_or_structured
    assert isinstance(structured.struct_or_union_or_interface, model)
    child = structured.sub_ports.sub_port[0]
    definition = structured.struct_port_type_defs.struct_port_type_def[0]
    assert child.name == "member"
    assert definition.type_name.value == "Packet"
    assert get_parent_info(get_handle(child)).parent_handle == get_handle(structured)
    assert get_parent_info(get_handle(definition)).parent_handle == get_handle(structured)
    assert api.getAbstractorPortIDs(root) == [handle]
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj
    assert api.removeAbstractorPort(handle)
    assert api.getAbstractorPortIDs(root) == []


@pytest.mark.parametrize("kind", ["struct", "union"])
@pytest.mark.parametrize("direction", ["in", "out", "inout", "phantom"])
def test_standard_directions(root, kind, direction):
    """Struct and union directions use the schema enumeration."""
    handle = create(root, kind, direction=direction)
    structured = resolve_handle(handle).wire_or_transactional_or_structured
    assert structured.struct_or_union_or_interface.direction.value == direction


@pytest.mark.parametrize("kind", ["interface", "struct", "union"])
@pytest.mark.parametrize("field", ["name", "sub", "type_name"])
def test_invalid_names_do_not_initialize_model(root, kind, field):
    """Missing required input strings fail before model creation."""
    with pytest.raises(TgiError) as error:
        create(root, kind, **{field: ""})
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(root).model is None


@pytest.mark.parametrize("kind", ["struct", "union"])
@pytest.mark.parametrize("direction", [None, "bad", 2])
def test_invalid_directions_do_not_initialize_model(root, kind, direction):
    """Malformed direction values expose TGI faults with no mutation."""
    with pytest.raises(TgiError) as error:
        create(root, kind, direction=direction)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(root).model is None


@pytest.mark.parametrize("kind", ["interface", "struct", "union"])
def test_invalid_root(kind):
    """Every creator rejects unknown root handles."""
    with pytest.raises(TgiError) as error:
        create("missing", kind)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
