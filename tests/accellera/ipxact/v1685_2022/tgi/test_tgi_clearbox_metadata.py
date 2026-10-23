"""Clearbox generated enum and optional Boolean edits remain schema valid."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import clearbox as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import ClearboxElementType, SimpleClearboxType


def check_xml(element):
    """Validate the generated type as a temporary global element and reload it."""
    schema_doc = etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")
    schema_doc.getroot().append(etree.Element("{http://www.w3.org/2001/XMLSchema}element",
                                            name="testClearbox", type="ipxact:clearboxElementType"))
    xml = XmlDocument.serializer().render(element)
    tree = etree.fromstring(xml.encode())
    tree.tag = "{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}testClearbox"
    schema = etree.XMLSchema(schema_doc)
    assert schema.validate(tree), schema.error_log
    assert XmlDocument.parser().from_string(xml, ClearboxElementType) == element


@pytest.mark.parametrize("kind", ["signal", "pin", "interface"])
def test_enum_and_driveable_roundtrip(kind):
    element = ClearboxElementType(name="internal", clearbox_type=SimpleClearboxType.SIGNAL)
    handle = get_handle(element)
    assert api.setClearboxElementClearboxType(handle, kind)
    assert element.clearbox_type is SimpleClearboxType(kind)
    assert api.getClearboxElementClearboxType(handle) == kind
    assert api.getClearboxElementDriveable(handle) is None
    for value in (False, True):
        api.setClearboxElementDriveable(handle, value)
        assert api.getClearboxElementDriveable(handle) is value
        check_xml(element)
    assert api.removeClearboxElementDriveable(handle)
    assert api.getClearboxElementDriveable(handle) is None
    assert not api.removeClearboxElementDriveable(handle)
    assert element.name == "internal"
    check_xml(element)


def test_invalid_metadata_is_atomic():
    element = ClearboxElementType(name="internal", clearbox_type=SimpleClearboxType.PIN, driveable=False)
    handle = get_handle(element)
    for value in (None, True, 12, "invalid"):
        with pytest.raises(TgiError):
            api.setClearboxElementClearboxType(handle, value)
        assert element.clearbox_type is SimpleClearboxType.PIN
    for value in (None, 0, 1, "false"):
        with pytest.raises(TgiError):
            api.setClearboxElementDriveable(handle, value)
        assert element.driveable is False


def test_unrelated_and_stale_handles():
    for handle in ("missing-clearbox", get_handle(SimpleClearboxType.PIN)):
        for operation, args in [(api.getClearboxElementClearboxType, ()), (api.getClearboxElementDriveable, ()),
                                (api.removeClearboxElementDriveable, ()),
                                (api.setClearboxElementClearboxType, ("pin",)),
                                (api.setClearboxElementDriveable, (True,))]:
            with pytest.raises(TgiError):
                operation(handle, *args)
