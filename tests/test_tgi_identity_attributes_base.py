"""BASE XML identity attributes remain source IDs rather than TGI handles."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ConfigurableElementValue,
    Dim,
    ExtendedVectorsType,
    File,
    IpxactUri,
    Left,
    Parameter,
    Right,
)


@pytest.mark.parametrize(
    "name,obj,field,expected",
    [
        ("getIdAttribute", Dim(value="2", id="xml-id"), "id", "xml-id"),
        ("getFileIdAttribute", File(name=IpxactUri(value="source.sv"), file_id="file-id"), "file_id", "file-id"),
        (
            "getParameterIdAttribute",
            Parameter(name="P", value="1", parameter_id="parameter-id"),
            "parameter_id",
            "parameter-id",
        ),
        (
            "getReferenceIdAttribute",
            ConfigurableElementValue(value="1", reference_id="parameter-id"),
            "reference_id",
            "parameter-id",
        ),
        (
            "getVectorIdAttribute",
            ExtendedVectorsType.Vector(left=Left(value="7"), right=Right(value="0"), vector_id="vector-id"),
            "vector_id",
            "vector-id",
        ),
    ],
)
def test_identity_attribute(name, obj, field, expected):
    getter = getattr(api, name)
    handle = get_handle(obj)
    before = XmlDocument.serializer().render(obj)
    assert getter(handle) == expected
    assert getter(handle) != handle
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == expected
    assert XmlDocument.serializer().render(obj) == before
    assert getattr(tgi, name) is getter
    setattr(obj, field, None)
    assert getter(handle) is None
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")
