"""View source references preserve strings and sibling loci through XML reload."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import view as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.model_type import ModelType


@pytest.mark.parametrize("kind", ["Component", "DesignConfiguration", "Design"])
@pytest.mark.parametrize("parsed", [False, True])
def test_reference_lifecycle(kind, parsed):
    view = ModelType.Views.View(name="rtl")
    if parsed:
        view = XmlDocument.parser().from_string(XmlDocument.serializer().render(view), type(view))
    handle = get_handle(view)
    get = getattr(api, f"getView{kind}InstantiationRefByName")
    set_ref = getattr(api, f"setView{kind}InstantiationRef")
    remove = getattr(api, f"removeView{kind}InstantiationRef")
    assert get(handle) is None
    assert not remove(handle)
    assert set_ref(handle, "first")
    assert get(handle) == "first"
    assert set_ref(handle, "second")
    assert get(handle) == "second"
    before = XmlDocument.serializer().render(view)
    loaded = XmlDocument.parser().from_string(before, type(view))
    assert loaded == view
    assert get(get_handle(loaded)) == "second"
    assert remove(handle)
    assert get(handle) is None
    assert not remove(handle)
    assert view.name == "rtl"


@pytest.mark.parametrize("kind", ["Component", "DesignConfiguration", "Design"])
@pytest.mark.parametrize("value", [None, "", " ", 3])
def test_invalid_values_are_atomic(kind, value):
    view = ModelType.Views.View(name="rtl", component_instantiation_ref="keep")
    before = XmlDocument.serializer().render(view)
    with pytest.raises(TgiError):
        getattr(api, f"setView{kind}InstantiationRef")(get_handle(view), value)
    assert XmlDocument.serializer().render(view) == before


@pytest.mark.parametrize("kind", ["Component", "DesignConfiguration", "Design"])
@pytest.mark.parametrize("prefix,suffix", [("get", "ByName"), ("remove", ""), ("set", "")])
def test_invalid_handles(kind, prefix, suffix):
    operation = getattr(api, f"{prefix}View{kind}InstantiationRef{suffix}")
    with pytest.raises(TgiError):
        operation("missing", "name") if prefix == "set" else operation("missing")
