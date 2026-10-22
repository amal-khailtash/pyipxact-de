"""Reference getters resolve generated IP-XACT targets in their owning roots."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstractor, clearbox, component, instantiation, top_element, view
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Abstractor,
    ClearboxElementRefType,
    ClearboxElementType,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    DesignConfiguration,
    SimpleClearboxType,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Keep registered top-level elements isolated between cases."""
    registry.clear()
    yield
    registry.clear()


def make_component(name: str, clearbox_names: list[str]) -> Component:
    """Build a component with locally named clearbox elements."""
    elements = [
        ClearboxElementType(name=element_name, clearbox_type=SimpleClearboxType.SIGNAL)
        for element_name in clearbox_names
    ]
    return Component(
        vendor="v",
        library="l",
        name=name,
        version="1",
        clearbox_elements=ComponentType.ClearboxElements(clearbox_element=elements) if elements else None,
    )


def make_clearbox_ref(root: Component, name: str) -> tuple[str, str]:
    """Create an owning component instantiation and clearbox reference."""
    instance_id = component.addComponentComponentInstantiation(get_handle(root), "u")
    ref_id = instantiation.addComponentInstantiationClearboxElementRef(instance_id, name, "top")
    return instance_id, ref_id


@pytest.mark.parametrize("parsed", [False, True])
def test_clearbox_reference_resolves_inside_owning_component(parsed):
    root = make_component("owner", ["internal"])
    _, ref_id = make_clearbox_ref(root, "internal")
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
        registry.register(root, ("v", "l", "owner", "1"))
        model = root.model
        instantiations = model.instantiations
        instances = instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation
        ref = instances[0].clearbox_element_refs.clearbox_element_ref[0]
        ref_id = get_handle(ref)
    target = root.clearbox_elements.clearbox_element[0]

    assert clearbox.getClearboxElementRefByID(ref_id) == get_handle(target)


def test_parsed_clearbox_owner_scan_skips_other_instantiation_kinds():
    root = make_component("owner", ["internal"])
    component.addComponentDesignInstantiation(get_handle(root), "design", ("v", "l", "d", "1"))
    make_clearbox_ref(root, "internal")
    root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
    registry.register(root, ("v", "l", "owner", "1"))
    instances = (
        root.model.instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation
    )
    ref_id = get_handle(instances[1].clearbox_element_refs.clearbox_element_ref[0])

    assert clearbox.getClearboxElementRefByID(ref_id) == get_handle(root.clearbox_elements.clearbox_element[0])


def test_clearbox_reference_does_not_resolve_a_different_component_target():
    owner = make_component("owner", [])
    _, ref_id = make_clearbox_ref(owner, "internal")
    decoy = make_component("decoy", ["internal"])
    registry.register(owner, ("v", "l", "owner", "1"))
    registry.register(decoy, ("v", "l", "decoy", "1"))

    with pytest.raises(TgiError) as error:
        clearbox.getClearboxElementRefByID(ref_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize("names", [[], ["other"], ["internal", "internal"]])
def test_clearbox_missing_or_ambiguous_local_target(names):
    root = make_component("owner", names)
    _, ref_id = make_clearbox_ref(root, "internal")

    with pytest.raises(TgiError) as error:
        clearbox.getClearboxElementRefByID(ref_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize("bad_handle", ["missing-clearbox-ref", None])
def test_clearbox_reference_rejects_absent_and_wrong_handles(bad_handle):
    bad = bad_handle if isinstance(bad_handle, str) else get_handle(ClearboxElementType(
        name="wrong", clearbox_type=SimpleClearboxType.SIGNAL
    ))
    with pytest.raises(TgiError) as error:
        clearbox.getClearboxElementRefByID(bad)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_clearbox_reference_requires_component_ownership():
    _, ref_id = make_clearbox_ref(make_component("owner", ["internal"]), "internal")
    # A separate standalone reference has no parent ownership path to resolve through.
    standalone = get_handle(ClearboxElementRefType(name="internal"))

    with pytest.raises(TgiError) as error:
        clearbox.getClearboxElementRefByID(standalone)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def make_abstractor(vlnv: tuple[str, str, str, str], view_names: list[str]) -> str:
    """Create and register an abstractor with the requested model views."""
    root_id = top_element.createAbstractor(vlnv, "direct", ("bus", "lib", "bus", "1"), "a", "b")
    assert root_id is not None
    for name in view_names:
        abstractor.addAbstractorView(root_id, name)
    return root_id


def make_abstractor_instance(vlnv: tuple[str, str, str, str], view_name: str) -> str:
    instance_type = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance
    instance = instance_type(
        instance_name="bridge",
        abstractor_ref=ConfigurableLibraryRefType(
            vendor=vlnv[0], library=vlnv[1], name=vlnv[2], version=vlnv[3]
        ),
        view_name=view_name,
    )
    return get_handle(instance)


@pytest.mark.parametrize("parsed", [False, True])
def test_abstractor_instance_view_reference_resolves_from_abstractor_vlnv(parsed):
    registry.clear()
    vlnv = ("v", "l", "abstractor", "1")
    root_id = make_abstractor(vlnv, ["rtl"])
    if parsed:
        root = resolve_handle(root_id)
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Abstractor)
        registry.clear()
        registry.register(root, vlnv, element_type="Abstractor")
    target_root = resolve_handle(registry.get_id(vlnv))
    instance_id = make_abstractor_instance(vlnv, "rtl")
    target = target_root.model.views.view[0]

    assert view.getAbstractorInstanceViewNameRefByID(instance_id) == get_handle(target)


def test_abstractor_instance_view_reference_is_scoped_to_referenced_abstractor():
    registry.clear()
    referenced = ("v", "l", "referenced", "1")
    decoy = ("v", "l", "decoy", "1")
    make_abstractor(referenced, [])
    make_abstractor(decoy, ["rtl"])
    instance_id = make_abstractor_instance(referenced, "rtl")

    with pytest.raises(TgiError) as error:
        view.getAbstractorInstanceViewNameRefByID(instance_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize("view_names", [[], ["other"], ["rtl", "rtl"]])
def test_abstractor_instance_view_missing_or_ambiguous(view_names):
    registry.clear()
    vlnv = ("v", "l", "abstractor", "1")
    make_abstractor(vlnv, view_names)
    instance_id = make_abstractor_instance(vlnv, "rtl")

    with pytest.raises(TgiError) as error:
        view.getAbstractorInstanceViewNameRefByID(instance_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


def test_abstractor_instance_view_rejects_missing_abstractor_and_wrong_handles():
    registry.clear()
    instance_id = make_abstractor_instance(("v", "l", "missing", "1"), "rtl")
    with pytest.raises(TgiError) as missing:
        view.getAbstractorInstanceViewNameRefByID(instance_id)
    assert missing.value.fault_code == TgiFaultCode.NOT_FOUND

    for bad_handle in ("missing-abstractor-instance", get_handle("wrong")):
        with pytest.raises(TgiError) as error:
            view.getAbstractorInstanceViewNameRefByID(bad_handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
