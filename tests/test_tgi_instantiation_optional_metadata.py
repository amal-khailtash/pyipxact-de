"""Optional instantiation metadata preserves XML values and handle lifetimes."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import component, instantiation
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component


def reload(root):
    """Validate generated XML and reload its component root."""
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    return XmlDocument.parser().from_string(xml, Component)


@pytest.mark.parametrize("kind", ["Component", "DesignConfiguration"])
@pytest.mark.parametrize("parsed", [False, True])
def test_language_removal_invalidates_handle(kind, parsed):
    root = Component(vendor="v", library="l", name="c", version="1")
    args = [get_handle(root), "i"] + ([] if kind == "Component" else [("v", "l", "d", "1")])
    handle = getattr(component, f"addComponent{kind}Instantiation")(*args)
    getter = getattr(instantiation, f"get{kind}InstantiationLanguageID")
    remover = getattr(instantiation, f"remove{kind}InstantiationLanguage")
    setter = getattr(instantiation, f"set{kind}InstantiationLanguage")
    assert getattr(api, getter.__name__) is getter
    assert getattr(api, remover.__name__) is remover
    assert getter(handle) is None
    setter(handle, "vhdl")
    resolve_handle(handle).language.strict = True
    if parsed:
        root = reload(root)
        handle = getattr(component, f"getComponent{kind}InstantiationIDs")(get_handle(root))[0]
    child = getter(handle)
    assert getter(handle) == child
    assert resolve_handle(child).strict
    owner = resolve_handle(handle)
    assert remover(handle)
    assert resolve_handle(child) is None
    assert resolve_handle(handle) is owner
    assert getter(handle) is None
    assert remover(handle)
    assert reload(root) == root
    setter(handle, "verilog")
    assert getter(handle) != child
    assert not resolve_handle(getter(handle)).strict
    with pytest.raises(TgiError):
        getter(get_handle(root))
    with pytest.raises(TgiError):
        remover(get_handle(root))


def test_virtual_boolean_source_and_removal():
    root = Component(vendor="v", library="l", name="c", version="1")
    handle = component.addComponentComponentInstantiation(get_handle(root), "i")
    getter = api.getComponentInstantiationIsVirtual
    setter = api.setComponentInstantiationIsVirtual
    remover = api.removeComponentInstantiationIsVirtual
    assert getter(handle) is None
    for value in (True, False):
        assert setter(handle, value)
        parsed = reload(root)
        parsed_id = component.getComponentComponentInstantiationIDs(get_handle(parsed))[0]
        assert getter(parsed_id) is value
    for invalid in (0, 1, None, "false", []):
        with pytest.raises(TgiError):
            setter(handle, invalid)
        assert getter(handle) is False
    assert remover(handle)
    assert remover(handle)
    assert getter(handle) is None
    assert reload(root) == root
    for operation, args in ((getter, ()), (setter, (True,)), (remover, ())):
        with pytest.raises(TgiError):
            operation(get_handle(root), *args)
