"""Optional name removal preserves sibling source metadata and owner lifetime."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import component, instantiation
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component

NAMES = ("Architecture", "Configuration", "Library", "Module", "Package")


@pytest.mark.parametrize("name", NAMES)
def test_selective_parsed_removal_and_lifetime(name):
    root = Component(vendor="v", library="l", name="c", version="1")
    root_id = get_handle(root)
    handle = component.addComponentComponentInstantiation(root_id, "i")
    for sibling in NAMES:
        getattr(instantiation, f"setComponentInstantiation{sibling}Name")(handle, sibling)
    instantiation.setComponentInstantiationLanguage(handle, "vhdl")
    xml = XmlDocument.serializer().render(root)
    root = XmlDocument.parser().from_string(xml, Component)
    root_id = get_handle(root)
    handle = component.getComponentComponentInstantiationIDs(root_id)[0]
    owner = resolve_handle(handle)
    language = instantiation.getComponentInstantiationLanguageID(handle)
    remover = getattr(instantiation, f"removeComponentInstantiation{name}Name")
    assert getattr(api, remover.__name__) is remover
    for _ in range(2):
        assert remover(handle)
        assert resolve_handle(handle) is owner
        assert resolve_handle(language) is owner.language
        for sibling in NAMES:
            expected = None if sibling == name else sibling
            assert getattr(instantiation, f"getComponentInstantiation{sibling}Name")(handle) == expected
    xml = XmlDocument.serializer().render(root)
    tree = etree.fromstring(xml.encode())
    ns = {"i": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"}
    assert not tree.xpath(f"//i:{name.lower()}Name", namespaces=ns)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(tree), schema.error_log
    reloaded = XmlDocument.parser().from_string(xml, Component)
    reloaded_id = component.getComponentComponentInstantiationIDs(get_handle(reloaded))[0]
    assert getattr(instantiation, f"getComponentInstantiation{name}Name")(reloaded_id) is None
    with pytest.raises(TgiError):
        remover(root_id)
    assert component.removeComponentComponentInstantiation(handle)
    assert resolve_handle(language) is None
    with pytest.raises(TgiError):
        remover(handle)
