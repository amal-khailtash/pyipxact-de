"""Logical port creation and parsed traversal preserve standard model choices."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition


@pytest.fixture
def root():
    """Create a registered abstraction with an initial logical port."""
    registry.clear()
    handle = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "initial", "wire")
    yield handle
    registry.clear()


@pytest.mark.parametrize("style", ["wire", "transactional"])
@pytest.mark.parametrize("match", [None, False, True])
def test_port_contracts_and_parsed_ownership(root, style, match):
    """Creation, listing, name, style, match and removal agree after XML parsing."""
    first = api.getAbstractionDefPortIDs(root)[0]
    added = api.addAbstractionDefPort(root, "data", style)
    assert api.getAbstractionDefPortIDs(root) == [first, added]
    assert api.getAbstractionDefPortLogicalName(added) == "data"
    assert api.getAbstractionDefPortStyle(added) == style
    resolve_handle(added).match = match
    assert api.getAbstractionDefPortMatch(added) is match
    obj = resolve_handle(root)
    loaded = XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), AbstractionDefinition)
    assert loaded == obj
    parsed_root = get_handle(loaded)
    parsed = api.getAbstractionDefPortIDs(parsed_root)
    assert api.getAbstractionDefPortStyle(parsed[1]) == style
    assert api.getAbstractionDefPortMatch(parsed[1]) is match
    assert api.removeAbstractionDefPort(parsed[1])
    assert len(api.getAbstractionDefPortIDs(parsed_root)) == 1
    assert api.removeAbstractionDefPort(added)
    assert not api.removeAbstractionDefPort(added)
    assert not api.removeAbstractionDefPort("missing")
    assert api.getAbstractionDefPortIDs(root) == [first]


@pytest.mark.parametrize("name,style", [("", "wire"), (None, "wire"), (2, "wire"),
                                       ("data", "packet"), ("data", "WIRE"), ("data", None)])
def test_invalid_creation_is_atomic(root, name, style):
    """Invalid input leaves the original collection unchanged."""
    obj = resolve_handle(root)
    before = list(obj.ports.port)
    with pytest.raises(TgiError) as error:
        api.addAbstractionDefPort(root, name, style)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert obj.ports.port == before


@pytest.mark.parametrize("operation", [
    lambda: api.addAbstractionDefPort("missing", "data", "wire"),
    lambda: api.getAbstractionDefPortIDs("missing"),
    lambda: api.getAbstractionDefPortLogicalName("missing"),
    lambda: api.getAbstractionDefPortStyle("missing"),
    lambda: api.getAbstractionDefPortMatch("missing"),
])
def test_invalid_handles(operation):
    """Creation and getter contracts expose invalid-ID faults."""
    with pytest.raises(TgiError) as error:
        operation()
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
