"""Generator BASE metadata handles preserve generated source and parsed ownership."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import generator as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AbstractorGenerator,
    ApiType,
    ComponentGenerator,
    Generator,
    GeneratorType,
    GeneratorTypeApiService,
    IpxactUri,
    Phase,
)


@pytest.mark.parametrize("cls", [Generator, ComponentGenerator, AbstractorGenerator])
@pytest.mark.parametrize("parsed", [False, True])
def test_metadata_source_and_lifetime(cls, parsed):
    obj = cls(
        name="gen",
        generator_exe=IpxactUri(value="${BIN}/generator"),
        api_service=GeneratorTypeApiService.REST,
        api_type=GeneratorType.ApiType(value=ApiType.TGI_2022_BASE),
        phase=Phase(value="2.5"),
    )
    xml = XmlDocument.serializer().render(obj)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    # Generated generator types have valid global elements in the standard schema.
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    if parsed:
        obj = XmlDocument.parser().from_string(xml, cls)
    handle = get_handle(obj)
    before = XmlDocument.serializer().render(obj)
    assert api.getGeneratorApiService(handle) == "REST"
    assert api.getGeneratorExecutable(handle) == "${BIN}/generator"
    children = [
        api.getGeneratorApiTypeID(handle),
        api.getGeneratorGeneratorExe(handle),
        api.getGeneratorPhaseID(handle),
    ]
    assert resolve_handle(children[0]).value is ApiType.TGI_2022_BASE
    assert resolve_handle(children[2]).value == "2.5"
    assert api.getGeneratorGeneratorExe(handle) == children[1]
    assert XmlDocument.serializer().render(obj) == before
    for child in children:
        assert detach_child_by_handle(child)
        assert resolve_handle(child) is None
    assert api.getGeneratorApiTypeID(handle) is None
    assert api.getGeneratorPhaseID(handle) is None
    assert api.getGeneratorGeneratorExe(handle) is None


def test_optional_absence_and_invalid_handles():
    handle = get_handle(Generator(name="gen", generator_exe=IpxactUri(value="")))
    assert api.getGeneratorApiService(handle) is None
    assert api.getGeneratorApiTypeID(handle) is None
    assert api.getGeneratorPhaseID(handle) is None
    assert api.getGeneratorExecutable(handle) == ""
    for operation in [
        api.getGeneratorApiService,
        api.getGeneratorApiTypeID,
        api.getGeneratorExecutable,
        api.getGeneratorGeneratorExe,
        api.getGeneratorPhaseID,
    ]:
        with pytest.raises(TgiError):
            operation("missing-generator-metadata")
