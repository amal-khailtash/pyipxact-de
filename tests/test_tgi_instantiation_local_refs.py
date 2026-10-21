"""Local instantiation references validate names and preserve selective lifetime."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact import v1685_2022 as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component, instantiation
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, register_parent, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, ConstraintSetRef, FileSetRef


@pytest.mark.parametrize("kind", ["ConstraintSetRef", "FileSetRef"])
@pytest.mark.parametrize("parsed", [False, True])
def test_selective_reference_lifecycle(kind, parsed):
    root = Component(vendor="v", library="l", name="c", version="1")
    owner_id = component.addComponentComponentInstantiation(get_handle(root), "i")
    creator = getattr(instantiation, f"addComponentInstantiation{kind}")
    getter = getattr(instantiation, f"getComponentInstantiation{kind}IDs")
    remover = getattr(instantiation, f"removeComponentInstantiation{kind}")
    for operation in (creator, getter, remover):
        assert getattr(api, operation.__name__) is operation
    first = creator(owner_id, "é:one")
    second = creator(owner_id, "second")
    resolve_handle(first).id = "source-ref"
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    ref_xml = XmlDocument.serializer().render(resolve_handle(first))
    assert schema.validate(etree.fromstring(ref_xml.encode())), schema.error_log
    if parsed:
        xml = XmlDocument.serializer().render(root)
        root = XmlDocument.parser().from_string(xml, Component)
        owner_id = component.getComponentComponentInstantiationIDs(get_handle(root))[0]
        first, second = getter(owner_id)
    assert getter(owner_id) == [first, second]
    assert resolve_handle(first).id == "source-ref"
    assert remover(first)
    assert resolve_handle(first) is None
    assert resolve_handle(second).local_name == "second"
    assert getter(owner_id) == [second]
    xml = XmlDocument.serializer().render(root)
    reloaded = XmlDocument.parser().from_string(xml, Component)
    child_id = component.getComponentComponentInstantiationIDs(get_handle(reloaded))[0]
    assert [resolve_handle(h).local_name for h in getter(child_id)] == ["second"]
    with pytest.raises(TgiError):
        remover(first)
    with pytest.raises(TgiError):
        remover(get_handle(root))
    cls = ConstraintSetRef if kind == "ConstraintSetRef" else FileSetRef
    assert not remover(get_handle(cls(local_name="unowned")))
    unrelated = cls(local_name="foreign")
    register_parent(unrelated, root, ("foreign_refs",), "list")
    with pytest.raises(TgiError):
        remover(get_handle(unrelated))
    assert resolve_handle(get_handle(unrelated)) is unrelated
    assert component.removeComponentComponentInstantiation(owner_id)
    assert resolve_handle(second) is None


@pytest.mark.parametrize("kind", ["ConstraintSetRef", "FileSetRef"])
def test_reference_lexical_validation_atomicity(kind):
    root = Component(vendor="v", library="l", name="c", version="1")
    owner_id = component.addComponentComponentInstantiation(get_handle(root), "i")
    creator = getattr(instantiation, f"addComponentInstantiation{kind}")
    getter = getattr(instantiation, f"getComponentInstantiation{kind}IDs")
    for value in ("", "two words", "a/b", "\x00", None, 123):
        with pytest.raises(TgiError):
            creator(owner_id, value)
        assert getter(owner_id) == []
    if kind == "ConstraintSetRef":
        assert resolve_handle(creator(owner_id, "123")).local_name == "123"
    else:
        with pytest.raises(TgiError):
            creator(owner_id, "123")
        assert getter(owner_id) == []
    with pytest.raises(TgiError):
        creator(get_handle(root), "valid")
