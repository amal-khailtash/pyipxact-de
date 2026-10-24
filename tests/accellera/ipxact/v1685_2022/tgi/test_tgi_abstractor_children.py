"""Standard abstractor child contracts use interface handles and detach safely."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstractor as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Abstractor


@pytest.fixture
def root():
    """Register an abstractor with two independent interfaces."""
    registry.clear()
    handle = top_element.createAbstractor(("v", "l", "a", "1"), "direct", ("v", "l", "b", "1"), "a", "b")
    yield handle
    registry.clear()


def round_trip(root):
    """Verify generated XML preserves the complete model."""
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj


def test_interface_abstractions_are_scoped_and_removable(root):
    """Interface handles scope traversal and removal without affecting siblings."""
    left, right = api.getAbstractorAbstractorInterfaceIDs(root)
    assert api.getAbstractorInterfaceAbstractionTypeIDs(left) == []
    first = api.addAbstractorInterfaceAbstractionType(left, ("v", "l", "wire", "1"))
    second = api.addAbstractorInterfaceAbstractionType(left, ("v", "l", "transaction", "1"))
    other = api.addAbstractorInterfaceAbstractionType(right, ("v", "l", "wire", "2"))
    assert api.getAbstractorInterfaceAbstractionTypeIDs(left) == [first, second]
    assert api.getAbstractorInterfaceAbstractionTypeIDs(right) == [other]
    assert resolve_handle(first).abstraction_ref.name == "wire"
    round_trip(root)
    assert api.removeAbstractorInterfaceAbstractionType(first)
    assert not api.removeAbstractorInterfaceAbstractionType(first)
    assert not api.removeAbstractorInterfaceAbstractionType("missing")
    assert api.getAbstractorInterfaceAbstractionTypeIDs(left) == [second]
    assert api.getAbstractorInterfaceAbstractionTypeIDs(right) == [other]
    round_trip(root)


@pytest.mark.parametrize("bad", [("v", "l", "n"), ("v", "", "n", "1"), ("v", "l", 2, "1")])
def test_invalid_reference_does_not_create_wrapper(root, bad):
    """Validation precedes mutation of interface abstraction types."""
    interface = api.getAbstractorAbstractorInterfaceIDs(root)[0]
    with pytest.raises(TgiError) as error:
        api.addAbstractorInterfaceAbstractionType(interface, bad)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(interface).abstraction_types is None


@pytest.mark.parametrize("operation", ["get", "add"])
def test_root_handle_is_not_an_interface(root, operation):
    """The standard interface APIs reject root handles and missing handles."""
    for handle in [root, "missing"]:
        with pytest.raises(TgiError) as error:
            if operation == "get":
                api.getAbstractorInterfaceAbstractionTypeIDs(handle)
            else:
                api.addAbstractorInterfaceAbstractionType(handle, ("v", "l", "n", "1"))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_instantiation_add_list_remove(root):
    """Instantiations preserve insertion order and detach from the nested list."""
    assert api.getAbstractorComponentInstantiationIDs(root) == []
    first = api.addAbstractorComponentInstantiation(root, "rtl")
    second = api.addAbstractorComponentInstantiation(root, "behavioral")
    assert api.getAbstractorComponentInstantiationIDs(root) == [first, second]
    assert resolve_handle(first).name == "rtl"
    round_trip(root)
    assert api.removeAbstractorComponentInstantiation(first)
    assert not api.removeAbstractorComponentInstantiation(first)
    assert not api.removeAbstractorComponentInstantiation("missing")
    assert api.getAbstractorComponentInstantiationIDs(root) == [second]
    round_trip(root)


@pytest.mark.parametrize("bad", ["", None, 2])
def test_instantiation_invalid_name_is_atomic(root, bad):
    """Invalid names do not initialize an empty model."""
    with pytest.raises(TgiError) as error:
        api.addAbstractorComponentInstantiation(root, bad)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(root).model is None


def test_instantiation_invalid_root():
    """Creation and traversal consistently reject unknown root handles."""
    for operation in [lambda: api.addAbstractorComponentInstantiation("missing", "rtl"),
                      lambda: api.getAbstractorComponentInstantiationIDs("missing")]:
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
