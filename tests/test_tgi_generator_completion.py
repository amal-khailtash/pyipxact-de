"""Generator edits preserve typed children, source expressions and handle lifetime."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import generator as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractorGenerator, ComponentGenerator, Generator, IpxactUri


@pytest.fixture
def generator():
    return Generator(name="generate", generator_exe=IpxactUri(value="tool"))


def test_phase_source_resolved_values_and_stable_identity(generator):
    handle = get_handle(generator)
    assert api.getGeneratorPhase(handle) is None
    assert api.setGeneratorPhase(handle, "1.5 + 2.0")
    child = api.getGeneratorPhaseID(handle)
    assert api.getGeneratorPhase(handle) == 3.5
    assert api.getGeneratorPhaseExpression(handle) == "1.5 + 2.0"
    assert api.setGeneratorPhase(handle, "PHASE")
    assert api.getGeneratorPhaseID(handle) == child
    assert api.getGeneratorPhase(handle) is None
    with pytest.raises(TgiError):
        api.setGeneratorPhase(handle, None)
    assert generator.phase.value == "PHASE"
    assert api.removeGeneratorPhase(handle)
    assert resolve_handle(child) is None


def test_api_executable_and_transport_schema_roundtrip(generator):
    handle = get_handle(generator)
    assert api.setGeneratorApiService(handle, "SOAP")
    assert api.setGeneratorApiType(handle, "TGI_2022_BASE")
    api_id = api.getGeneratorApiTypeID(handle)
    assert api.setGeneratorApiType(handle, "TGI_2022_EXTENDED")
    assert api.getGeneratorApiTypeID(handle) == api_id
    exe_id = api.getGeneratorGeneratorExe(handle)
    assert api.setGeneratorGeneratorExe(handle, "new-tool")
    assert api.getGeneratorGeneratorExe(handle) == exe_id
    assert api.setGeneratorTransportMethods(handle, "file")
    transport_id = api.getGeneratorTransportMethodsID(handle)
    method_id = api.getTransportMethodsTransportMethodID(transport_id)
    assert api.setTransportMethodsTransportMethod(transport_id, "file")
    assert api.getTransportMethodsTransportMethodID(transport_id) == method_id
    xml = XmlDocument.serializer().render(generator)
    assert XmlDocument.parser().from_string(xml, Generator) == generator
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    # Validate as the generator child of a standard generator-chain document.
    from org.accellera.ipxact.v1685_2022 import GeneratorChain

    chain = GeneratorChain(
        vendor="v",
        library="l",
        name="c",
        version="1",
        generator_chain_selector_or_component_generator_selector_or_generator=[generator],
    )
    schema.assertValid(etree.fromstring(XmlDocument.serializer().render(chain).encode()))
    for operation, value in [
        (api.setGeneratorApiType, "bad"),
        (api.setGeneratorApiService, "bad"),
        (api.setGeneratorTransportMethods, "bad"),
        (api.setGeneratorGeneratorExe, None),
    ]:
        with pytest.raises(TgiError):
            operation(handle, value)
    assert api.removeGeneratorApiType(handle)
    assert resolve_handle(api_id) is None
    assert api.removeGeneratorTransportMethods(handle)
    assert resolve_handle(transport_id) is None
    assert resolve_handle(method_id) is None
    assert api.removeGeneratorApiService(handle)
    assert generator.api_service is None


@pytest.mark.parametrize(
    "cls,add,remove,ids",
    [
        (
            AbstractorGenerator,
            api.addAbstractorGeneratorGroup,
            api.removeAbstractorGeneratorGroup,
            api.getAbstractorGeneratorGroupIDs,
        ),
        (
            ComponentGenerator,
            api.addComponentGeneratorGroup,
            api.removeComponentGeneratorGroup,
            api.getComponentGeneratorGroupIDs,
        ),
    ],
)
def test_groups_scope_identity_and_invalid_arguments(cls, add, remove, ids):
    obj = cls(name="generate", generator_exe=IpxactUri(value="tool"))
    handle = get_handle(obj)
    first = add(handle, "group")
    second = add(handle, "group")
    assert remove(second)
    assert ids(handle) == [first]
    assert not remove("missing")
    with pytest.raises(TgiError):
        add(handle, None)
    assert ids(handle) == [first]
    assert api.setGeneratorScope(handle, "instance")
    with pytest.raises(TgiError):
        api.setGeneratorScope(handle, "bad")


def test_parsed_group_and_transport_removal():
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import registry
    from org.accellera.ipxact.v1685_2022 import Component, ComponentGenerators

    obj = ComponentGenerator(name="generate", generator_exe=IpxactUri(value="tool"))
    api.addComponentGeneratorGroup(get_handle(obj), "group")
    root = Component(vendor="v", library="l", name="c", version="1",
                     component_generators=ComponentGenerators(component_generator=[obj]))
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
    registry.register(parsed, ("v", "l", "c", "1"), replace=True)
    child = parsed.component_generators.component_generator[0]
    group_id = get_handle(child.group[0])
    assert not api.removeAbstractorGeneratorGroup(group_id)
    assert api.removeComponentGeneratorGroup(group_id)
    assert child.group == []
    assert resolve_handle(group_id) is None
    handle = get_handle(child)
    assert api.setGeneratorTransportMethods(handle, "file")
    transport_id = api.getGeneratorTransportMethodsID(handle)
    method_id = api.getTransportMethodsTransportMethodID(transport_id)
    assert api.removeTransportMethodsTransportMethod(transport_id)
    assert resolve_handle(method_id) is None
    assert api.setTransportMethodsTransportMethod(transport_id, "file")
    assert api.removeGeneratorTransportMethods(handle)
    registry.clear()
