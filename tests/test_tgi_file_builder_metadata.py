"""Generated file-builder source updates retain identity and XML metadata."""

import inspect

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact import v1685_2022 as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component, file_builder, instantiation
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, FileBuilderType, FileType, SimpleFileType


@pytest.mark.parametrize("name,field", [("Command", "command"), ("Flags", "flags"),
                                        ("ReplaceDefaultFlags", "replace_default_flags")])
@pytest.mark.parametrize("parsed", [False, True])
def test_builder_expression_identity_and_removal(name, field, parsed):
    root = Component(vendor="v", library="l", name="c", version="1")
    owner = component.addComponentComponentInstantiation(get_handle(root), "i")
    fb = FileBuilderType(file_type=FileType(value=SimpleFileType.VHDL_SOURCE))
    resolve_handle(owner).default_file_builder.append(fb)
    handle = get_handle(fb)
    setter = getattr(file_builder, f"setFileBuilder{name}")
    remover = getattr(file_builder, f"removeFileBuilder{name}")
    assert getattr(api, setter.__name__) is setter
    assert getattr(api, remover.__name__) is remover
    assert not remover(handle)
    assert setter(handle, "${SOURCE}")
    child = getattr(fb, field)
    child.other_attributes["{urn:test}source"] = "expression-source"
    child_handle = get_handle(child)
    assert setter(handle, "")
    assert getattr(fb, field) is child
    assert child.other_attributes["{urn:test}source"] == "expression-source"
    for invalid in (None, True, 12):
        with pytest.raises(TgiError):
            setter(handle, invalid)
        assert child.value == ""
    setter(handle, "1" if name == "ReplaceDefaultFlags" else "cc -c ${SOURCE}")
    if name == "Command":
        assert file_builder.getFileBuilderCommand(handle) == child.value
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    reloaded = XmlDocument.parser().from_string(xml, Component)
    assert reloaded == root
    if parsed:
        owner = component.getComponentComponentInstantiationIDs(get_handle(reloaded))[0]
        handle = instantiation.getComponentInstantiationDefaultFileBuilderIDs(owner)[0]
        fb = resolve_handle(handle)
        child_handle = get_handle(getattr(fb, field))
    assert remover(handle)
    assert resolve_handle(child_handle) is None
    assert getattr(fb, field) is None
    assert not remover(handle)
    assert fb.file_type.value == SimpleFileType.VHDL_SOURCE
    with pytest.raises(TgiError):
        setter(get_handle(root), "bad")


def test_file_type_identity_and_standard_signature():
    fb = FileBuilderType(file_type=FileType(value=SimpleFileType.USER, user="custom", libext=".hdl"))
    handle = get_handle(fb)
    child = fb.file_type
    assert file_builder.setFileBuilderFileType(handle, fileTypeValue="vhdlSource")
    assert fb.file_type is child
    assert child.value == SimpleFileType.VHDL_SOURCE
    assert child.user == "custom"
    assert child.libext == ".hdl"
    for invalid in ("invalidFileType", None, 12):
        with pytest.raises(TgiError):
            file_builder.setFileBuilderFileType(handle, invalid)
        assert child.value == SimpleFileType.VHDL_SOURCE
    assert "valueExpression" in inspect.signature(file_builder.setFileBuilderReplaceDefaultFlags).parameters
