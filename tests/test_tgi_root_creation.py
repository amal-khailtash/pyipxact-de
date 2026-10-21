"""IEEE 1685-2022 Annex F root creation contracts."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, registry, resolve_handle
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


@pytest.mark.parametrize("direct,addressable", [(False, False), (False, True), (True, False), (True, True)])
def test_create_bus_definition_capabilities(direct, addressable):
    from org.accellera.ipxact.v1685_2022 import BusDefinition
    vlnv = ("v", "l", "bus", "1")
    handle = top_element.createBusDefinition(vlnv, direct, addressable)
    obj = resolve_handle(handle)
    assert isinstance(obj, BusDefinition)
    assert obj.direct_connection is direct
    assert obj.is_addressable is addressable
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), BusDefinition) == obj
    assert top_element.createBusDefinition(vlnv, direct, addressable) is None


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_bus_creation_rejects_nonboolean(value):
    with pytest.raises(TgiError) as error:
        top_element.createBusDefinition(("v", "l", "bus", "1"), value, True)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_generator_chain_initial_generator_round_trip():
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_handle, get_parent_info
    from org.accellera.ipxact.v1685_2022 import GeneratorChain
    vlnv = ("v", "l", "chain", "1")
    handle = top_element.createGeneratorChain(vlnv, "generate", "scripts/generate.py")
    obj = resolve_handle(handle)
    assert isinstance(obj, GeneratorChain)
    generator = obj.generator_chain_selector_or_component_generator_selector_or_generator[0]
    assert generator.name == "generate"
    assert generator.generator_exe.value == "scripts/generate.py"
    assert get_parent_info(get_handle(generator)).parent_handle == handle
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), GeneratorChain) == obj
    assert top_element.createGeneratorChain(vlnv, "generate", "scripts/generate.py") is None


@pytest.mark.parametrize("name,exe", [("", "tool"), ("generator", ""), (None, "tool"), ("generator", 42)])
def test_generator_chain_invalid_arguments(name, exe):
    with pytest.raises(TgiError) as error:
        top_element.createGeneratorChain(("v", "l", "chain", "1"), name, exe)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("member", ["DirectConnection", "Broadcast", "IsAddressable"])
def test_bus_boolean_setters_preserve_false_and_reject_coercion(member):
    from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_definition
    handle = top_element.createBusDefinition(("v", "l", "bus", "1"), True, True)
    setter = getattr(bus_definition, "setBusDefinition" + member)
    getter = getattr(bus_definition, "getBusDefinition" + member)
    assert setter(handle, False)
    assert getter(handle) is False
    for invalid in [0, 1, "false", None]:
        with pytest.raises(TgiError) as error:
            setter(handle, invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert getter(handle) is False
    with pytest.raises(TgiError) as error:
        setter("missing", True)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
