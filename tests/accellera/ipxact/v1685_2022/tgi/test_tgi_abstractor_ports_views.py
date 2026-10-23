"""Abstractor physical port and view creation contracts."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstractor as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Abstractor


@pytest.fixture
def root():
    """Provide a root with no model children."""
    registry.clear()
    handle = top_element.createAbstractor(("v", "l", "a", "1"), "direct", ("v", "l", "b", "1"), "a", "b")
    yield handle
    registry.clear()


def round_trip(root):
    """Verify generated models survive XML serialization."""
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj


@pytest.mark.parametrize("value", ["in", "out", "inout", "phantom"])
def test_wire_directions(root, value):
    """Every standard wire direction is stored as its schema enumeration."""
    handle = api.addAbstractorWirePort(root, "wire", value)
    assert resolve_handle(handle).wire_or_transactional_or_structured.direction.value == value
    round_trip(root)


@pytest.mark.parametrize("value", ["requires", "provides", "both", "phantom"])
def test_transactional_initiatives(root, value):
    """Every standard initiative uses the generated initiative wrapper."""
    handle = api.addAbstractorTransactionalPort(root, "transaction", value)
    assert resolve_handle(handle).wire_or_transactional_or_structured.initiative.value.value == value
    round_trip(root)


def test_mixed_ports_traversal_removal(root):
    """Mixed styles preserve order and removal does not disturb siblings."""
    assert api.getAbstractorPortIDs(root) == []
    wire = api.addAbstractorWirePort(root, "wire", "in")
    transaction = api.addAbstractorTransactionalPort(root, "transaction", "requires")
    assert api.getAbstractorPortIDs(root) == [wire, transaction]
    assert api.removeAbstractorPort(wire)
    assert not api.removeAbstractorPort(wire)
    assert not api.removeAbstractorPort("missing")
    assert api.getAbstractorPortIDs(root) == [transaction]
    round_trip(root)


def test_views_traversal_removal(root):
    """Views round trip and detach from the nested view list."""
    assert api.getAbstractorViewIDs(root) == []
    first = api.addAbstractorView(root, "rtl")
    second = api.addAbstractorView(root, "behavioral")
    assert api.getAbstractorViewIDs(root) == [first, second]
    round_trip(root)
    assert api.removeAbstractorView(first)
    assert not api.removeAbstractorView(first)
    assert not api.removeAbstractorView("missing")
    assert api.getAbstractorViewIDs(root) == [second]
    round_trip(root)


@pytest.mark.parametrize("operation", [api.addAbstractorWirePort, api.addAbstractorTransactionalPort])
@pytest.mark.parametrize("bad", [None, "", "invalid", 1])
def test_bad_style_value_is_atomic(root, operation, bad):
    """Invalid direction or initiative does not initialize a model."""
    with pytest.raises(TgiError) as error:
        operation(root, "port", bad)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(root).model is None


@pytest.mark.parametrize("bad", [None, "", 1])
def test_bad_child_names_are_atomic(root, bad):
    """All three creators validate names before initializing wrappers."""
    for operation in [lambda: api.addAbstractorWirePort(root, bad, "in"),
                      lambda: api.addAbstractorTransactionalPort(root, bad, "both"),
                      lambda: api.addAbstractorView(root, bad)]:
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert resolve_handle(root).model is None


def test_invalid_handles():
    """Creation and traversal consistently reject missing root handles."""
    for operation in [lambda: api.addAbstractorWirePort("missing", "port", "in"),
                      lambda: api.addAbstractorTransactionalPort("missing", "port", "both"),
                      lambda: api.addAbstractorView("missing", "view"),
                      lambda: api.getAbstractorPortIDs("missing"), lambda: api.getAbstractorViewIDs("missing")]:
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
