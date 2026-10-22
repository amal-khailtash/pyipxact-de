"""Abstractor removal contracts preserve ownership and invalidate descendants."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_handle, register_parent, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Abstractor, BusInterfaceType, ExecutableImage, FileSetRef


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def test_parsed_interface_removal_invalidates_children():
    root_id = tgi.createAbstractor(("v", "l", "a", "1"), "direct", ("v", "l", "b", "1"), "a", "b")
    root = resolve_handle(root_id)
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Abstractor)
    registry.clear()
    registry.register(parsed, ("v", "l", "a", "1"))
    first, second = parsed.abstractor_interfaces.abstractor_interface
    first_id = get_handle(first)
    descendant = tgi.addAbstractorInterfaceAbstractionType(first_id, ("v", "l", "wire", "1"))
    assert tgi.removeAbstractorAbstractorInterface(first_id)
    assert parsed.abstractor_interfaces.abstractor_interface == [second]
    assert resolve_handle(first_id) is None
    assert resolve_handle(descendant) is None
    assert not tgi.removeAbstractorAbstractorInterface(first_id)
    assert not tgi.removeAbstractorAbstractorInterface(get_handle(parsed))


@pytest.mark.parametrize("group_type", [BusInterfaceType.Target.FileSetRefGroup, ExecutableImage.FileSetRefGroup])
def test_file_set_group_removal_preserves_sibling(group_type):
    first = FileSetRef(local_name="rtl")
    second = FileSetRef(local_name="sim")
    group = group_type(file_set_ref=[first, second])
    register_parent(first, group, ("file_set_ref",), "list")
    first_id = get_handle(first)
    assert tgi.removeFileSetRefGroupFileSetRef(first_id)
    assert group.file_set_ref == [second]
    assert resolve_handle(first_id) is None
    assert not tgi.removeFileSetRefGroupFileSetRef(first_id)


def test_file_set_ref_in_other_container_is_preserved():
    from org.accellera.ipxact.v1685_2022 import ComponentInstantiationType

    child = FileSetRef(local_name="rtl")
    parent = ComponentInstantiationType(name="rtl", file_set_ref=[child])
    register_parent(child, parent, ("file_set_ref",), "list")
    assert not tgi.removeFileSetRefGroupFileSetRef(get_handle(child))
    assert parent.file_set_ref == [child]
    assert not tgi.removeFileSetRefGroupFileSetRef("missing")


def test_public_exports():
    for name in ["removeAbstractorAbstractorInterface", "removeFileSetRefGroupFileSetRef"]:
        assert name in tgi.__all__
        assert callable(getattr(tgi, name))


def test_registered_document_group_ownership_is_discovered():
    from org.accellera.ipxact.v1685_2022 import BusInterfaces, Component, ConfigurableLibraryRefType

    group = BusInterfaceType.Target.FileSetRefGroup(file_set_ref=[FileSetRef(local_name="rtl")])
    interface = BusInterfaceType(
        name="target",
        bus_type=ConfigurableLibraryRefType(vendor="v", library="l", name="b", version="1"),
        choice=BusInterfaceType.Target(file_set_ref_group=[group]),
    )
    root = Component(
        vendor="v", library="l", name="c", version="1", bus_interfaces=BusInterfaces(bus_interface=[interface])
    )
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
    registry.register(parsed, ("v", "l", "c", "1"))
    parsed_group = parsed.bus_interfaces.bus_interface[0].choice.file_set_ref_group[0]
    child_id = get_handle(parsed_group.file_set_ref[0])
    assert tgi.removeFileSetRefGroupFileSetRef(child_id)
    assert parsed_group.file_set_ref == []
    assert resolve_handle(child_id) is None
