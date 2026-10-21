"""BASE file-set traversal preserves source order and restores parsed ownership."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import file_set as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Dependency, File, FileSet, FileSetType, FileType, IpxactUri, SimpleFileType


@pytest.mark.parametrize(
    "kind,field", [("Dependency", "dependency"), ("File", "file"), ("Function", "function"), ("Group", "group")]
)
@pytest.mark.parametrize("parsed", [False, True])
def test_fileset_collection_order_and_ownership(kind, field, parsed):
    root = FileSet(
        name="sources",
        dependency=[Dependency(value="first"), Dependency(value="second")],
        file=[
            File(name=IpxactUri(value="a.c"), id="a", file_type=[FileType(value=SimpleFileType.C_SOURCE)]),
            File(name=IpxactUri(value="b.c"), id="b", file_type=[FileType(value=SimpleFileType.C_SOURCE)]),
        ],
        function=[
            FileSetType.Function(file_ref="a", entry_point="first"),
            FileSetType.Function(file_ref="b", entry_point="second"),
        ],
        group=[FileSetType.Group(value="first"), FileSetType.Group(value="second")],
    )
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    if parsed:
        root = XmlDocument.parser().from_string(xml, FileSet)
    handle = get_handle(root)
    getter = getattr(api, f"getFileSet{kind}IDs")
    ids = getter(handle)
    assert getter(handle) == ids
    assert [resolve_handle(h) for h in ids] == list(getattr(root, field))
    before = XmlDocument.serializer().render(root)
    if kind == "Group":
        assert api.getFileSetGroups(handle) == ["first", "second"]
    assert getter(handle) == ids
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(ids[0])
    assert resolve_handle(ids[0]) is None
    assert getter(handle) == [ids[1]]
    with pytest.raises(TgiError):
        getter(get_handle(root.name))


def test_empty_fileset_and_invalid_handles():
    handle = get_handle(FileSet(name="empty"))
    for getter in (
        api.getFileSetDependencyIDs,
        api.getFileSetFileIDs,
        api.getFileSetFunctionIDs,
        api.getFileSetGroupIDs,
        api.getFileSetGroups,
    ):
        assert getter(handle) == []
        with pytest.raises(TgiError):
            getter("missing-fileset")
