"""IEEE 1685-2022 Annex F root creation contracts."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, TgiFaultCode, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Catalog, Component, Design, DesignConfiguration, TypeDefinitions

CREATORS = [
    ("createCatalog", Catalog), ("createComponent", Component), ("createDesign", Design),
    ("createDesignConfiguration", DesignConfiguration), ("createTypeDefinitions", TypeDefinitions),
]


@pytest.fixture(autouse=True)
def isolated_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("operation,model", CREATORS)
def test_create_generated_root_and_round_trip(operation, model):
    vlnv = ("vendor", "library", operation, "1.0")
    handle = getattr(top_element, operation)(vlnv)
    obj = resolve_handle(handle)
    assert isinstance(obj, model)
    assert registry.get_id(vlnv) == handle
    assert top_element.getVLNV(handle) == vlnv
    xml = XmlDocument.serializer().render(obj)
    assert XmlDocument.parser().from_string(xml, model) == obj


@pytest.mark.parametrize("operation,model", CREATORS)
def test_duplicate_returns_null_without_replacing_root(operation, model):
    vlnv = ("vendor", "library", "existing", "1.0")
    create = getattr(top_element, operation)
    first = create(vlnv)
    assert create(vlnv) is None
    assert registry.get_id(vlnv) == first
    assert isinstance(resolve_handle(first), model)


@pytest.mark.parametrize("operation,model", CREATORS)
@pytest.mark.parametrize("vlnv", [("v", "l", "n"), ("v", "", "n", "1"), ("v", "l", 42, "1")])
def test_invalid_vlnv_does_not_register(operation, model, vlnv):
    with pytest.raises(TgiError) as error:
        getattr(top_element, operation)(vlnv)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
