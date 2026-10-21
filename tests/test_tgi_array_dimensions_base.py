"""Register/field array BASE getters preserve typed children and ownership."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import array as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockType,
    Array,
    BitStride,
    Dim,
    FieldType,
    RegisterFile,
    Stride,
    UnsignedLongintExpression,
)


@pytest.mark.parametrize("kind", [AddressBlockType.Register, RegisterFile.Register, FieldType])
@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("source,expected", [("0016", 16), ("0x20", 32), ("${STEP}", None)])
def test_dimension_array(kind, parsed, source, expected):
    field = kind is FieldType
    dims = [Dim(value="03", index_var="i"), Dim(value="${N}")]
    arr = FieldType.Array(dim=dims, bit_stride=BitStride(value=source)) if field else Array(
        dim=dims, stride=Stride(value=source)
    )
    parent = kind(name="item", array=arr, **(
        {"bit_offset": UnsignedLongintExpression(value="0")} if field else
        {"address_offset": UnsignedLongintExpression(value="0")}
    ))
    if parsed:
        parent = XmlDocument.parser().from_string(XmlDocument.serializer().render(parent), kind)
    getter = api.getRegisterFieldArrayID if field else api.getRegisterArrayID
    handle = get_handle(parent)
    arr_id = getter(handle)
    assert getter(handle) == arr_id
    assert api.getArrayIDs(handle) == [arr_id]
    assert resolve_handle(arr_id) is parent.array
    before = XmlDocument.serializer().render(parent)
    dim_ids = api.getArrayDimIDs(arr_id)
    assert dim_ids == api.getArrayDimIDs(arr_id)
    assert [api.getDimExpression(i) for i in dim_ids] == ["03", "${N}"]
    assert [api.getDimValue(i) for i in dim_ids] == [3, None]
    assert [api.getDimIndexVar(i) for i in dim_ids] == ["i", None]
    assert api.getArrayStride(arr_id) == expected
    assert api.getArrayStrideExpression(arr_id) == source
    stride_id = api.getArrayStrideID(arr_id)
    assert api.getArrayStrideID(arr_id) == stride_id
    assert resolve_handle(stride_id).value == source
    assert XmlDocument.serializer().render(parent) == before
    assert detach_child_by_handle(stride_id)
    assert api.getArrayStride(arr_id) is None
    assert api.getArrayStrideExpression(arr_id) is None
    assert api.getArrayStrideID(arr_id) is None
    assert detach_child_by_handle(dim_ids[0])
    assert api.getArrayDimIDs(arr_id) == [dim_ids[1]]
    assert detach_child_by_handle(arr_id)
    assert getter(handle) is None
    assert resolve_handle(dim_ids[1]) is None


def test_invalid_dimension_and_parent_types():
    wrong = get_handle(Stride(value="1"))
    for name in ("getDimExpression", "getDimValue", "getDimIndexVar", "getRegisterArrayID", "getRegisterFieldArrayID"):
        for handle in (wrong, "missing"):
            with pytest.raises(TgiError):
                getattr(api, name)(handle)
