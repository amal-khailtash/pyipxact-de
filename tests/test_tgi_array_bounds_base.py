"""Bounded array BASE traversal preserves source order and XML ownership."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import array as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Arrays,
    ConfigurableArrays,
    Left,
    ModuleParameterArrays,
    Parameter,
    Right,
)


@pytest.mark.parametrize("kind", [Arrays, ConfigurableArrays, ModuleParameterArrays])
@pytest.mark.parametrize("parsed", [False, True])
def test_bounded_array(kind, parsed):
    wrapper = kind(array=[kind.Array(left=Left(value="07"), right=Right(value="${LOW}")),
                         kind.Array(left=Left(value="3"), right=Right(value="0"))])
    if parsed:
        wrapper = XmlDocument.parser().from_string(XmlDocument.serializer().render(wrapper), kind)
    parent = Parameter(name="P", value="0", arrays=wrapper)
    ids = api.getArrayIDs(get_handle(parent))
    assert ids == api.getArrayIDs(get_handle(parent))
    assert [resolve_handle(i) for i in ids] == list(wrapper.array)
    before = XmlDocument.serializer().render(wrapper)
    assert api.getArrayRange(ids[0]) == [7, None]
    assert api.getArrayRangeExpression(ids[0]) == ["07", "${LOW}"]
    assert api.getArrayRange(ids[1]) == [3, 0]
    for side in ("Left", "Right"):
        getter = getattr(api, f"getArray{side}ID")
        child = getter(ids[0])
        assert child == getter(ids[0])
        assert resolve_handle(child) is getattr(wrapper.array[0], side.lower())
    assert XmlDocument.serializer().render(wrapper) == before
    assert detach_child_by_handle(api.getArrayLeftID(ids[0]))
    assert api.getArrayLeftID(ids[0]) is None
    assert api.getArrayRangeExpression(ids[0]) == [None, "${LOW}"]
    assert detach_child_by_handle(ids[1])
    assert list(wrapper.array) == [resolve_handle(ids[0])]


def test_empty_and_invalid():
    assert api.getArrayIDs(get_handle(Parameter(name="P", value="0"))) == []
    for name in ("getArrayIDs", "getArrayLeftID", "getArrayRightID", "getArrayRange", "getArrayRangeExpression"):
        with pytest.raises(TgiError):
            getattr(api, name)("missing")
