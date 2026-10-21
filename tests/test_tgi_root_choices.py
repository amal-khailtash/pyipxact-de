"""Bus and abstraction choices honor enumeration inputs and loaded ownership."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as ad
from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_definition as bus
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition, BusDefinition


@pytest.fixture(params=["bus", "abstraction"])
def root(request):
    """Provide matching creation, traversal, and removal operations."""
    registry.clear()
    vlnv = ("v", "l", "root", "1")
    if request.param == "bus":
        handle = top_element.createBusDefinition(vlnv, True, False)
        operations = (bus.addBusDefinitionChoice, bus.getBusDefinitionChoiceIDs, bus.removeBusDefinitionChoice)
        model = BusDefinition
    else:
        handle = top_element.createAbstractionDef(vlnv, ("v", "l", "bus", "1"), "data", "wire")
        operations = (ad.addAbstractionDefChoice, ad.getAbstractionDefChoiceIDs, ad.removeAbstractionDefChoice)
        model = AbstractionDefinition
    yield handle, operations, model
    registry.clear()


def test_add_traverse_loaded_remove(root):
    """Supplied values survive XML and traversal restores ownership for removal."""
    handle, (add, getter, remove), model = root
    assert getter(handle) == []
    first = add(handle, "width", ["8", "WIDTH + 1"])
    second = add(handle, "mode", ["0", "1"])
    assert getter(handle) == [first, second]
    assert [item.value for item in resolve_handle(first).enumeration] == ["8", "WIDTH + 1"]
    obj = resolve_handle(handle)
    loaded = XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), model)
    assert loaded == obj
    loaded_ids = getter(get_handle(loaded))
    assert remove(loaded_ids[0])
    assert [resolve_handle(item).name for item in getter(get_handle(loaded))] == ["mode"]
    assert remove(first)
    assert getter(handle) == [second]


@pytest.mark.parametrize("name,values", [("", ["1"]), (None, ["1"]), ("name", []),
                                         ("name", "12"), ("name", [None]), ("name", [""]), ("name", None)])
def test_invalid_choice_is_atomic(root, name, values):
    """Invalid inputs leave the optional choices wrapper absent."""
    handle, (add, _, _), _ = root
    with pytest.raises(TgiError) as error:
        add(handle, name, values)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(handle).choices is None


def test_invalid_root_handles(root):
    """Choice creation and traversal reject unknown owners."""
    _, (add, getter, _), _ = root
    for operation in [lambda: add("missing", "name", ["1"]), lambda: getter("missing")]:
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
