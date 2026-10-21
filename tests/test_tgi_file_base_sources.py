"""BASE file source traversal returns strings and preserves child ownership."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import file_set as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Dependency,
    File,
    FileType,
    IpxactUri,
    NameValuePairType,
    SimpleFileType,
    Value,
)


def source_file():
    """Build multiple ordered source collections with distinct metadata."""
    return File(
        name=IpxactUri(value="${SRC}/source.vhd"),
        file_type=[FileType(value=SimpleFileType.VHDL_SOURCE), FileType(value=SimpleFileType.USER, user="custom")],
        define=[
            NameValuePairType(name="A", value=Value(value="${WIDTH}")),
            NameValuePairType(name="B", value=Value(value="")),
        ],
        dependency=[Dependency(value="${DEP}/one"), Dependency(value="two")],
        exported_name=[File.ExportedName(value="symbol"), File.ExportedName(value="second")],
    )


@pytest.mark.parametrize(
    "name,field",
    [("Define", "define"), ("Dependency", "dependency"), ("ExportedName", "exported_name"), ("FileType", "file_type")],
)
@pytest.mark.parametrize("parsed", [False, True])
def test_base_order_source_and_ownership(name, field, parsed):
    root = source_file()
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    if parsed:
        root = XmlDocument.parser().from_string(xml, File)
    file_id = get_handle(root)
    getter = getattr(api, f"getFile{name}IDs")
    handles = getter(file_id)
    assert handles == getter(file_id)
    assert [resolve_handle(h) for h in handles] == list(getattr(root, field))
    if name == "Define":
        assert [api.getFileDefineSymbolValue(h) for h in handles] == ["${WIDTH}", ""]
    elif name == "ExportedName":
        assert api.getFileExportedNames(file_id) == ["symbol", "second"]
    elif name == "FileType":
        assert api.getFileFileTypes(file_id) == ["vhdlSource", "user"]
        assert resolve_handle(handles[1]).user == "custom"
    before = XmlDocument.serializer().render(root)
    assert getter(file_id) == handles
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(handles[0])
    assert resolve_handle(handles[0]) is None
    assert getter(file_id) == [handles[1]]
    assert resolve_handle(handles[1]) is not None
    with pytest.raises(TgiError):
        getter(get_handle(root.name))


def test_empty_collections_and_invalid_define():
    root = File(name=IpxactUri(value="a"))
    handle = get_handle(root)
    for getter in (
        api.getFileDefineIDs,
        api.getFileDependencyIDs,
        api.getFileExportedNameIDs,
        api.getFileFileTypeIDs,
        api.getFileExportedNames,
        api.getFileFileTypes,
    ):
        assert getter(handle) == []
        with pytest.raises(TgiError):
            getter("missing-file")
    with pytest.raises(TgiError):
        api.getFileDefineSymbolValue(get_handle(root))
