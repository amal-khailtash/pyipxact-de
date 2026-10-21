"""Function BASE type and reference-source getters return standard values."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import file_set as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import FileSetType, FileType, IpxactUri, ReturnTypeType, SimpleFileType


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("replicate", [False, True])
def test_generated_types_and_source_names(parsed, replicate):
    fn = FileSetType.Function(
        file_ref="source-file",
        replicate=replicate,
        return_type=ReturnTypeType.INT,
        source_file=[
            FileSetType.Function.SourceFile(
                source_name=IpxactUri(value="a.c"), file_type=FileType(value=SimpleFileType.USER, user="custom")
            )
        ],
    )
    if parsed:
        fn = XmlDocument.parser().from_string(XmlDocument.serializer().render(fn), FileSetType.Function)
    handle = get_handle(fn)
    before = XmlDocument.serializer().render(fn)
    assert api.getFunctionReturnType(handle) == "int"
    assert api.getFunctionReplicate(handle) is replicate
    assert api.getFunctionFileRefByName(handle) == "source-file"
    source = get_handle(fn.source_file[0])
    assert api.getFunctionSourceFileType(source) == "user"
    assert api.getSourceFileFileType(source) == "user"
    assert fn.source_file[0].file_type.user == "custom"
    assert XmlDocument.serializer().render(fn) == before


def test_defaults_and_wrong_handles():
    handle = get_handle(FileSetType.Function(file_ref="source"))
    assert api.getFunctionReturnType(handle) is None
    assert api.getFunctionReplicate(handle) is False
    for getter in (
        api.getFunctionReplicate,
        api.getFunctionReturnType,
        api.getFunctionSourceFileType,
        api.getSourceFileFileType,
        api.getFunctionFileRefByName,
    ):
        with pytest.raises(TgiError):
            getter("missing-function-type")
