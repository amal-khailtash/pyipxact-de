"""BASE file metadata preserves lexical source, optional states and ownership."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import file_set as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import File, FileType, IpxactUri, SimpleFileType


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("state", [False, True])
def test_base_identity_xml_and_child_ownership(parsed, state):
    root = File(
        name=IpxactUri(value="${SRC}/source.vhd"),
        file_type=[FileType(value=SimpleFileType.VHDL_SOURCE)],
        image_type=[File.ImageType(value="first"), File.ImageType(value="second")],
        is_include_file=File.IsIncludeFile(value=state, external_declarations=True),
        is_structural=state,
        logical_name=File.LogicalName(value="library", default=True),
    )
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    if parsed:
        root = XmlDocument.parser().from_string(xml, File)
    handle = get_handle(root)
    before = XmlDocument.serializer().render(root)
    assert api.getFileName(handle) == "${SRC}/source.vhd"
    assert api.getFileLogicalName(handle) == "library"
    assert api.getFileIsIncludeFile(handle) is state
    assert api.getFileIsStructural(handle) is state
    assert api.getFileImageTypes(handle) == ["first", "second"]
    images = api.getFileImageTypeIDs(handle)
    assert images == api.getFileImageTypeIDs(handle)
    include = api.getFileIsIncludeFileID(handle)
    logical = api.getFileLogicalNameID(handle)
    assert resolve_handle(include).external_declarations
    assert resolve_handle(logical).default
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(images[0])
    assert api.getFileImageTypeIDs(handle) == [images[1]]
    assert api.getFileImageTypes(handle) == ["second"]
    assert detach_child_by_handle(include)
    assert resolve_handle(include) is None
    assert api.getFileIsIncludeFileID(handle) is None
    assert api.getFileIsIncludeFile(handle) is False
    assert detach_child_by_handle(logical)
    assert api.getFileLogicalName(handle) is None
    assert api.getFileLogicalNameID(handle) is None
    assert api.getFileName(handle) == "${SRC}/source.vhd"


def test_absent_optional_values_and_invalid_handles():
    root = File(name=IpxactUri(value="a"))
    handle = get_handle(root)
    getters = (
        api.getFileImageTypeIDs,
        api.getFileImageTypes,
        api.getFileIsIncludeFile,
        api.getFileIsIncludeFileID,
        api.getFileIsStructural,
        api.getFileLogicalName,
        api.getFileLogicalNameID,
        api.getFileName,
    )
    assert [getter(handle) for getter in getters] == [[], [], False, None, False, None, None, "a"]
    for getter in getters:
        for invalid in (get_handle(root.name), "missing-file-metadata"):
            with pytest.raises(TgiError):
                getter(invalid)
