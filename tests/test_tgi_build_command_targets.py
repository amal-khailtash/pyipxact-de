"""Build-command URI and bit-expression metadata retain source identity."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import file_builder as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import File, FileType, IpxactUri, SimpleFileType


@pytest.mark.parametrize(
    "name,field,value",
    [("TargetName", "target_name", "${OUT}/target.o"), ("ReplaceDefaultFlags", "replace_default_flags", "1")],
)
@pytest.mark.parametrize("parsed", [False, True])
def test_target_source_and_container_lifetime(name, field, value, parsed):
    root = File(name=IpxactUri(value="source.vhd"), file_type=[FileType(value=SimpleFileType.VHDL_SOURCE)])
    file_id = get_handle(root)
    assert api.getFileBuildCommandID(file_id) is None
    assert api.setFileBuildCommand(file_id) is True
    command_id = api.getFileBuildCommandID(file_id)
    assert api.setFileBuildCommand(file_id) is True
    assert api.getFileBuildCommandID(file_id) == command_id
    setter = getattr(api, f"setBuildCommand{name}")
    remover = getattr(api, f"removeBuildCommand{name}")
    setter(command_id, value)
    if name == "ReplaceDefaultFlags":
        assert api.getBuildCommandReplaceDefaultFlags(command_id) is True
    child = getattr(root.build_command, field)
    setter(command_id, "")
    assert getattr(root.build_command, field) is child
    for invalid in (None, True, 123):
        with pytest.raises(TgiError):
            setter(command_id, invalid)
        assert child.value == ""
    setter(command_id, value)
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    reloaded = XmlDocument.parser().from_string(xml, File)
    assert reloaded.build_command == root.build_command
    if parsed:
        root = reloaded
        file_id = get_handle(root)
        command_id = api.getFileBuildCommandID(file_id)
    child_id = get_handle(getattr(root.build_command, field))
    if name == "TargetName":
        assert api.getBuildCommandTargetNameExpression(command_id) == value
    else:
        assert api.getBuildCommandReplaceDefaultFlagsID(command_id) == child_id
    assert remover(command_id)
    assert resolve_handle(child_id) is None
    assert not remover(command_id)
    setter(command_id, value)
    new_child_id = get_handle(getattr(root.build_command, field))
    assert detach_child_by_handle(command_id)
    assert root.build_command is None
    assert resolve_handle(new_child_id) is None
    assert resolve_handle(command_id) is None


def test_creation_and_source_reject_unrelated_handles_atomically():
    root = File(name=IpxactUri(value="a"), file_type=[FileType(value=SimpleFileType.VHDL_SOURCE)])
    handle = get_handle(root)
    for setter in (api.setBuildCommandTargetName, api.setBuildCommandReplaceDefaultFlags):
        with pytest.raises(TgiError):
            setter(handle, True)
        assert root.build_command is None
    wrong = get_handle(root.name)
    for operation in (api.getFileBuildCommandID, api.setFileBuildCommand):
        with pytest.raises(TgiError):
            operation(wrong)
    api.setBuildCommandTargetName(handle, "${OUT}/a.o")
    assert api.getBuildCommandTargetNameExpression(handle) == "${OUT}/a.o"
