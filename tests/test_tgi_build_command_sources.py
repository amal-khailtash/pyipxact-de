"""Build command source fields preserve metadata and standard child handles."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import file_builder as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import File, FileType, IpxactUri, SimpleFileType


@pytest.mark.parametrize("name", ["Command", "Flags"])
@pytest.mark.parametrize("parsed", [False, True])
def test_build_source_roundtrip_and_lifetime(name, parsed):
    root = File(name=IpxactUri(value="source.vhd"), file_type=[FileType(value=SimpleFileType.VHDL_SOURCE)],
                build_command=File.BuildCommand())
    handle = get_handle(root.build_command)
    setter = getattr(api, f"setBuildCommand{name}")
    getter = getattr(api, f"getBuildCommand{name}Expression")
    ids = getattr(api, f"getBuildCommand{name}ID")
    remover = getattr(api, f"removeBuildCommand{name}")
    assert ids(handle) is None
    setter(handle, "cc ${SOURCE}")
    child = resolve_handle(ids(handle))
    child.other_attributes["{urn:test}source"] = "original"
    if name == "Flags":
        child.append = True
    setter(handle, "")
    assert resolve_handle(ids(handle)) is child
    assert getter(handle) == ""
    assert child.other_attributes["{urn:test}source"] == "original"
    if name == "Flags":
        assert child.append
    setter(handle, "updated")
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    reloaded = XmlDocument.parser().from_string(xml, File)
    assert reloaded.build_command == root.build_command
    assert reloaded.name == root.name
    if parsed:
        handle = get_handle(reloaded.build_command)
    child_id = ids(handle)
    assert remover(handle)
    assert resolve_handle(child_id) is None
    assert getter(handle) is None
    assert not remover(handle)


def test_atomic_legacy_file_and_wrong_handle_inputs():
    root = File(name=IpxactUri(value="a"), file_type=[FileType(value=SimpleFileType.VHDL_SOURCE)])
    handle = get_handle(root)
    for setter in (api.setBuildCommandCommand, api.setBuildCommandFlags):
        for invalid in (None, True, 123):
            with pytest.raises(TgiError):
                setter(handle, invalid)
            assert root.build_command is None
        with pytest.raises(TgiError):
            setter(get_handle(root.name), "bad")
    api.setBuildCommandFlags(handle, "-O2")
    assert api.getBuildCommandFlagsExpression(handle) == "-O2"
    assert api.removeBuildCommandFlags(handle)
