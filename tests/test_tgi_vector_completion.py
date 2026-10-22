"""Vector contracts retain generated endpoints, source text and ownership."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import vector as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentPortDirectionType,
    ConstraintSet,
    ExtendedVectorsType,
    Left,
    Model,
    ModuleParameterType,
    Port,
    PortWireType,
    Right,
    Vector,
    Vectors,
)


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("container,cls", [(Vectors, Vector), (ExtendedVectorsType, ExtendedVectorsType.Vector),
                                          (ModuleParameterType.Vectors, ModuleParameterType.Vectors.Vector)])
def test_wrapper_lifecycle_and_expression_evaluation(container, cls):
    wrapper = container()
    handle = get_handle(wrapper)
    first = api.addVector(handle, ["8'h0f + 1", "0"])
    second = api.addVector(handle, ["WIDTH-1", "1"])
    assert isinstance(resolve_handle(first), cls)
    assert api.getVectorIDs(handle) == [first, second]
    assert api.getVectorRange(first) == [16, 0]
    assert api.getVectorRange(second) == [None, 1]
    assert api.getVectorRangeExpression(first) == ["8'h0f + 1", "0"]
    left = api.getVectorLeftID(first)
    right = api.getVectorRightID(first)
    assert isinstance(resolve_handle(left), Left)
    assert isinstance(resolve_handle(right), Right)
    assert api.setVector(first, "3", "1")
    assert api.getVectorLeftID(first) == left
    assert api.getVectorRange(first) == [3, 1]
    assert api.removeVector(first)
    assert resolve_handle(left) is None
    assert resolve_handle(right) is None
    assert api.getVectorIDs(handle) == [second]
    assert not api.removeVector(first)


def test_parsed_port_removal_and_schema_valid_roundtrip():
    wire = PortWireType(direction=ComponentPortDirectionType.IN)
    root = Component(vendor="v", library="l", name="c", version="1", model=Model(ports=Model.Ports(port=[
        Port(name="data", wire_or_transactional_or_structured=wire),
    ])))
    vector_id = api.addVector(get_handle(wire), ["7", "0"])
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    schema.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, ("v", "l", "c", "1"))
    parsed_wire = parsed.model.ports.port[0].wire_or_transactional_or_structured
    parsed_vector = parsed_wire.vectors.vector[0]
    parsed_id = get_handle(parsed_vector)
    left = api.getVectorLeftID(parsed_id)
    assert api.removeVector(parsed_id)
    assert parsed_wire.vectors is None
    assert resolve_handle(left) is None
    schema.assertValid(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))
    assert resolve_handle(vector_id) is wire.vectors.vector[0]


def test_constraint_vector_and_atomic_invalid_range():
    constraint = ConstraintSet()
    parent_id = get_handle(constraint)
    handle = api.addVector(parent_id, ["2", "0"])
    assert api.getVectorIDs(parent_id) == [handle]
    assert api.getVectorRange(handle) == [2, 0]
    before = constraint.vector
    with pytest.raises(tgi.TgiError):
        api.addVector(parent_id, ["3", "0"])
    assert constraint.vector is before
    with pytest.raises(tgi.TgiError):
        api.setVector(handle, "5", None)
    assert api.getVectorRange(handle) == [2, 0]
    assert api.removeVector(handle)
    assert constraint.vector is None


@pytest.mark.parametrize("value", [[], ["1"], "10", [None, "0"], [True, "0"]])
def test_bad_creation_does_not_create_wrapper(value):
    wire = PortWireType(direction=ComponentPortDirectionType.IN)
    with pytest.raises(tgi.TgiError):
        api.addVector(get_handle(wire), value)
    assert wire.vectors is None


def test_public_exports_and_wrong_handles():
    for name in api.__all__:
        assert callable(getattr(tgi, name))
    assert not api.removeVector("missing")
    assert api.getVectorLeftID("missing") is None
    assert api.getVectorRange("missing") is None
    assert api.getVectorRangeExpression("missing") is None
    assert api.getVectorRightID("missing") is None


def test_equal_vectors_remove_the_selected_identity():
    wrapper = Vectors()
    first = api.addVector(get_handle(wrapper), ["7", "0"])
    second = api.addVector(get_handle(wrapper), ["7", "0"])
    first_object = resolve_handle(first)
    assert api.removeVector(second)
    assert wrapper.vector[0] is first_object
    assert api.getVectorIDs(get_handle(wrapper)) == [first]
    assert resolve_handle(second) is None
