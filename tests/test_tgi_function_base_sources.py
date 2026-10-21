"""BASE function source strings and child handles survive generated XML reload."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import file_set as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    DataTypeType,
    FileSetType,
    FileType,
    IpxactUri,
    SimpleFileType,
    UnsignedBitExpression,
    Value,
)


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("datatype", [DataTypeType.INT, DataTypeType.CHAR])
def test_source_metadata_and_ownership(parsed, datatype):
    fn = FileSetType.Function(
        file_ref="source",
        entry_point="entry",
        disabled=UnsignedBitExpression(value="${OFF}"),
        argument=[FileSetType.Function.Argument(name="arg", value=Value(value="1"), data_type=datatype)],
        source_file=[
            FileSetType.Function.SourceFile(
                source_name=IpxactUri(value="${SRC}/a.c"), file_type=FileType(value=SimpleFileType.C_SOURCE)
            )
        ],
    )
    xml = XmlDocument.serializer().render(fn)
    if parsed:
        fn = XmlDocument.parser().from_string(xml, FileSetType.Function)
    handle = get_handle(fn)
    before = XmlDocument.serializer().render(fn)
    assert api.getFunctionEntryPoint(handle) == "entry"
    assert api.getFunctionDisabledExpression(handle) == "${OFF}"
    disabled = api.getFunctionDisabledID(handle)
    args = api.getFunctionArgumentIDs(handle)
    sources = api.getFunctionSourceFileIDs(handle)
    assert api.getFunctionArgumentDataType(args[0]) == datatype.value
    assert api.getFunctionSourceFileName(sources[0]) == "${SRC}/a.c"
    assert api.getFunctionArgumentIDs(handle) == args
    assert XmlDocument.serializer().render(fn) == before
    for child in (disabled, args[0], sources[0]):
        assert detach_child_by_handle(child)
        assert resolve_handle(child) is None
    assert api.getFunctionDisabledID(handle) is None
    assert api.getFunctionDisabledExpression(handle) is None
    assert api.getFunctionArgumentIDs(handle) == []
    assert api.getFunctionSourceFileIDs(handle) == []


def test_absent_sources_and_wrong_handles():
    fn = FileSetType.Function(file_ref="source")
    handle = get_handle(fn)
    assert api.getFunctionEntryPoint(handle) is None
    assert api.getFunctionDisabledID(handle) is None
    assert api.getFunctionDisabledExpression(handle) is None
    for operation in (
        api.getFunctionArgumentIDs,
        api.getFunctionDisabledExpression,
        api.getFunctionDisabledID,
        api.getFunctionEntryPoint,
        api.getFunctionSourceFileIDs,
        api.getFunctionArgumentDataType,
        api.getFunctionSourceFileName,
    ):
        with pytest.raises(TgiError):
            operation("missing-function-source")
