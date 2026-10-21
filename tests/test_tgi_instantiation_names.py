"""Instantiation source names retain the unrestricted XML string domain."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact import v1685_2022 as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component, instantiation
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component

NAMES = ("Architecture", "Configuration", "Library", "Module", "Package")


@pytest.mark.parametrize("name", NAMES)
def test_name_source_domain_and_atomicity(name):
    root = Component(vendor="v", library="l", name="c", version="1")
    handle = component.addComponentComponentInstantiation(get_handle(root), "i")
    getter = getattr(instantiation, f"getComponentInstantiation{name}Name")
    setter = getattr(instantiation, f"setComponentInstantiation{name}Name")
    assert getattr(api, getter.__name__) is getter
    assert getattr(api, setter.__name__) is setter
    assert getter(handle) is None
    for value in ("rtl", "", "  work \t\n", "model<&é"):
        assert setter(handle, value)
        assert getter(handle) == value
        xml = XmlDocument.serializer().render(root)
        schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
        assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
        parsed = XmlDocument.parser().from_string(xml, Component)
        parsed_id = component.getComponentComponentInstantiationIDs(get_handle(parsed))[0]
        assert getter(parsed_id) == value
    for value in (None, True, 42, [], b"rtl"):
        with pytest.raises(TgiError):
            setter(handle, value)
        assert getter(handle) == "model<&é"
    for invalid in (get_handle(root), "missing-name-handle"):
        with pytest.raises(TgiError):
            getter(invalid)
        with pytest.raises(TgiError):
            setter(invalid, "changed")
    assert resolve_handle(handle).name == "i"
