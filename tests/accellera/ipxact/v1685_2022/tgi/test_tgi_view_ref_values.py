"""Generated viewRef source edits preserve metadata and typed identity."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi as package
from amal.eda.accellera.ipxact.v1685_2022.tgi import view
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.domain_type_def import DomainTypeDef
from org.accellera.ipxact.v1685_2022.driver_type import DriverType
from org.accellera.ipxact.v1685_2022.signal_type_def import SignalTypeDef
from org.accellera.ipxact.v1685_2022.struct_port_type_defs import StructPortTypeDefs
from org.accellera.ipxact.v1685_2022.trans_type_def import TransTypeDef
from org.accellera.ipxact.v1685_2022.wire_type_def import WireTypeDef


@pytest.mark.parametrize("cls", [DriverType.ViewRef, WireTypeDef.ViewRef,
                                 StructPortTypeDefs.StructPortTypeDef.ViewRef, DomainTypeDef.ViewRef,
                                 TransTypeDef.ViewRef, SignalTypeDef.ViewRef])
def test_source_edit_and_xml_reload(cls):
    ref = cls(value="rtl", id="reference")
    handle = get_handle(ref)
    assert view.getViewRefByName(handle) == "rtl"
    assert view.setViewRefValue(handle, "gate")
    assert get_handle(ref) == handle
    assert ref.id == "reference"
    assert view.getViewRefByName(handle) == "gate"
    loaded = XmlDocument.parser().from_string(XmlDocument.serializer().render(ref), cls)
    assert loaded == ref


@pytest.mark.parametrize("value", ["", " ", None, 3])
def test_bad_names_are_atomic(value):
    ref = DriverType.ViewRef(value="keep")
    with pytest.raises(TgiError):
        view.setViewRefValue(get_handle(ref), value)
    assert ref.value == "keep"


def test_package_exports_and_wrong_handles():
    assert package.getViewRefByName is view.getViewRefByName
    assert package.setViewRefValue is view.setViewRefValue
    for handle in ("missing", get_handle("rtl")):
        with pytest.raises(TgiError):
            view.getViewRefByName(handle)
        with pytest.raises(TgiError):
            view.setViewRefValue(handle, "next")
