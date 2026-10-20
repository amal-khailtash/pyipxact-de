"""Standard abstractor editing preserves model identity and mutation safety."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstractor as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, TgiFaultCode, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Abstractor


@pytest.fixture
def root():
    """Provide a registered standard abstractor and clear global state afterward."""
    registry.clear()
    handle = top_element.createAbstractor(("v", "l", "a", "1"), "direct", ("v", "l", "b", "1"), "a", "b")
    yield handle
    registry.clear()


@pytest.mark.parametrize("mode", ["initiator", "target", "direct", "system"])
def test_set_mode_preserves_handle_and_round_trip(root, mode):
    """Every standard mode remains accessible through the original mode handle."""
    mode_id = api.getAbstractorAbstractorModeID(root)
    assert api.setAbstractorAbstractorMode(root, mode)
    assert api.getAbstractorAbstractorModeID(root) == mode_id
    assert api.getAbstractorAbstractorMode(root) == (mode, None)
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj


@pytest.mark.parametrize("bad", ["", "master", None, 1])
def test_invalid_mode_is_atomic(root, bad):
    """Invalid modes produce a TGI fault without changing the stored mode."""
    with pytest.raises(TgiError) as error:
        api.setAbstractorAbstractorMode(root, bad)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getAbstractorAbstractorMode(root) == ("direct", None)


def test_system_group_survives_standard_mode_setter(root):
    """A standard mode-only update preserves an existing system group."""
    api.setAbstractorAbstractorMode(root, "system", "control")
    api.setAbstractorAbstractorMode(root, "system")
    assert api.getAbstractorAbstractorMode(root) == ("system", "control")


@pytest.mark.parametrize("bad", [("v", "l", "b"), ("v", "", "b", "1"), ("v", "l", 1, "1")])
def test_invalid_bus_reference_is_atomic(root, bad):
    """Malformed references leave the previous bus VLNV unchanged."""
    with pytest.raises(TgiError) as error:
        api.setAbstractorBusType(root, bad)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getAbstractorBusTypeRefByVLNV(root) == ("v", "l", "b", "1")


def test_bus_reference_round_trip(root):
    """Bus references need not already resolve in the registry."""
    value = ("new", "library", "bus", "2")
    assert api.setAbstractorBusType(root, value)
    assert api.getAbstractorBusTypeRefByVLNV(root) == value
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj


def test_file_set_add_list_remove(root):
    """File sets retain insertion order, serialize, and detach from the actual list."""
    assert api.getAbstractorFileSetIDs(root) == []
    first = api.addAbstractorFileSet(root, "rtl")
    second = api.addAbstractorFileSet(root, "simulation")
    assert api.getAbstractorFileSetIDs(root) == [first, second]
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj
    assert api.removeAbstractorFileSet(first)
    assert api.getAbstractorFileSetIDs(root) == [second]
    assert not api.removeAbstractorFileSet(first)
    assert not api.removeAbstractorFileSet("missing")


@pytest.mark.parametrize("bad", ["", None, 2])
def test_invalid_file_set_name_is_atomic(root, bad):
    """Invalid names do not create even an empty fileSets wrapper."""
    with pytest.raises(TgiError) as error:
        api.addAbstractorFileSet(root, bad)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(root).file_sets is None


@pytest.mark.parametrize("call", [
    lambda: api.setAbstractorAbstractorMode("missing", "direct"),
    lambda: api.setAbstractorBusType("missing", ("v", "l", "b", "1")),
    lambda: api.addAbstractorFileSet("missing", "rtl"),
    lambda: api.getAbstractorFileSetIDs("missing"),
])
def test_invalid_root_handles(call):
    """Editing and traversal report invalid root handles consistently."""
    with pytest.raises(TgiError) as error:
        call()
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
