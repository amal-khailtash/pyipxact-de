"""Generator and choice contracts initialize generated children and remove them."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstractor as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, TgiFaultCode, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Abstractor


@pytest.fixture
def root():
    """Provide a root with empty optional collections."""
    registry.clear()
    handle = top_element.createAbstractor(("v", "l", "a", "1"), "direct", ("v", "l", "b", "1"), "a", "b")
    yield handle
    registry.clear()


@pytest.mark.parametrize("kind", ["generator", "choice"])
def test_add_list_round_trip_remove(root, kind):
    """Child order and XML values survive serialization and selective removal."""
    if kind == "generator":
        def add(name):
            return api.addAbstractorAbstractorGenerator(root, name, "tools/generate.py")
        getter = api.getAbstractorAbstractorGeneratorIDs
        remove = api.removeAbstractorAbstractorGenerator
    else:
        def add(name):
            return api.addAbstractorChoice(root, name, ["0", "1 + 2"])
        getter = api.getAbstractorChoiceIDs
        remove = api.removeAbstractorChoice
    assert getter(root) == []
    first, second = add("first"), add("second")
    assert getter(root) == [first, second]
    child = resolve_handle(first)
    if kind == "generator":
        assert child.generator_exe.value == "tools/generate.py"
    else:
        assert [item.value for item in child.enumeration] == ["0", "1 + 2"]
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj
    assert remove(first)
    assert not remove(first)
    assert not remove("missing")
    assert getter(root) == [second]
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), Abstractor) == obj


@pytest.mark.parametrize("name,exe", [("", "tool"), (None, "tool"), ("name", ""), ("name", 2)])
def test_generator_validation_is_atomic(root, name, exe):
    """Bad inputs do not create the generator wrapper."""
    with pytest.raises(TgiError) as error:
        api.addAbstractorAbstractorGenerator(root, name, exe)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(root).abstractor_generators is None


@pytest.mark.parametrize("name,values", [("", ["1"]), ("name", []), ("name", "1"),
                                         ("name", [None]), ("name", [""]), ("name", None)])
def test_choice_validation_is_atomic(root, name, values):
    """Bad names and enumeration arrays leave choices absent."""
    with pytest.raises(TgiError) as error:
        api.addAbstractorChoice(root, name, values)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(root).choices is None


@pytest.mark.parametrize("operation", [
    lambda: api.addAbstractorAbstractorGenerator("missing", "name", "tool"),
    lambda: api.addAbstractorChoice("missing", "name", ["1"]),
    lambda: api.getAbstractorAbstractorGeneratorIDs("missing"),
    lambda: api.getAbstractorChoiceIDs("missing"),
])
def test_invalid_handles(operation):
    """Creation and traversal expose consistent invalid-ID faults."""
    with pytest.raises(TgiError) as error:
        operation()
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
