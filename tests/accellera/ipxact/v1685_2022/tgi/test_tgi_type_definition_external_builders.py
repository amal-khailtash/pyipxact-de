"""Generated external type-definition and link builder contracts."""

from collections.abc import Iterator
from inspect import getdoc, signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentType,
    ConfigurableElementValue,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    ModeLinks,
    TypeDefinitions,
    ViewLinks,
)
from org.accellera.ipxact.v1685_2022.model import Model
from org.accellera.ipxact.v1685_2022.model_type import ModelType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_VLNV = ("example.org", "types", "shared", "1.0")


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _reference(parts: tuple[str, str, str, str] = _VLNV) -> ConfigurableLibraryRefType:
    return ConfigurableLibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])


def _external(
    name: str = "external_types",
    *,
    parts: tuple[str, str, str, str] = _VLNV,
    mode_links: ModeLinks | None = None,
    view_links: ViewLinks | None = None,
) -> ExternalTypeDefinitions:
    return ExternalTypeDefinitions(
        name=name,
        type_definitions_ref=_reference(parts),
        mode_links=mode_links,
        view_links=view_links,
    )


def _root(**values: object) -> TypeDefinitions:
    return TypeDefinitions(vendor="example.org", library="types", name="definitions", version="1.0", **values)


def _component(**values: object) -> Component:
    return Component(vendor="example.org", library="components", name="device", version="1.0", **values)


def _round_trip(model: object, model_type: type) -> object:
    xml = XmlDocument.serializer().render(model)
    element = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(element), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, model_type)
    assert XmlDocument.serializer().render(parsed) == xml
    return parsed


def _assert_fault(code: str, operation: object, *args: object) -> None:
    with pytest.raises(TgiError) as error:
        operation(*args)  # type: ignore[operator]
    assert error.value.fault_code == code


def _mode_link(external: str = "external_mode", local: str = "local_mode") -> ModeLinks.ModeLink:
    return ModeLinks.ModeLink(
        external_mode_reference=ModeLinks.ModeLink.ExternalModeReference(mode_ref=external),
        mode_reference=ModeLinks.ModeLink.ModeReference(mode_ref=local),
    )


def _view_link(external: str = "external_view", local: str = "local_view") -> ViewLinks.ViewLink:
    return ViewLinks.ViewLink(
        external_view_reference=ViewLinks.ViewLink.ExternalViewReference(view_ref=external),
        view_reference=ViewLinks.ViewLink.ViewReference(view_ref=local),
    )


def test_exact_external_builder_and_remover_signatures_exports_and_sections() -> None:
    operations = (
        (
            "addComponentExternalTypeDefinitions",
            ("componentID", "name", "vlnv"),
            (str, str, tuple[str, str, str, str]),
            str,
            "F.7.82.1",
        ),
        (
            "addExternalTypeDefinitionsModeLink",
            ("externalTypeDefinitionsID", "externalModeRef", "modeReference"),
            (str, str, str),
            str,
            "F.7.82.4",
        ),
        (
            "addExternalTypeDefinitionsViewLink",
            ("externalTypeDefinitionsID", "externalViewRef", "viewReference"),
            (str, str, str),
            str,
            "F.7.82.5",
        ),
        (
            "addTypeDefinitionsExternalTypeDefinitions",
            ("typeDefinitionsID", "name", "vlnv"),
            (str, str, tuple[str, str, str, str]),
            str,
            "F.7.82.11",
        ),
        ("removeComponentExternalTypeDefinitions", ("externalTypeDefinitionsID",), (str,), bool, "F.7.82.23"),
    )
    for name, parameters, annotations, result, section in operations:
        operation = getattr(api, name)
        assert getattr(root_api, name) is operation
        assert name in api.__all__ and name in root_api.__all__
        operation_signature = signature(operation)
        assert tuple(operation_signature.parameters) == parameters
        assert tuple(item.annotation for item in operation_signature.parameters.values()) == annotations
        assert all(item.default is item.empty for item in operation_signature.parameters.values())
        assert operation_signature.return_annotation is result
        doc = getdoc(operation)
        assert doc is not None and f"Section: {section}." in doc
        assert "Args:" in doc and "Returns:" in doc


@pytest.mark.parametrize(
    "parts",
    [
        (" vendor ", "library name", "shared:types", " 1.0 "),
        ("vendor", "library", "unregistered_target", "2.0"),
    ],
    ids=("preserves-vlnv-source", "does-not-resolve-target"),
)
def test_component_external_builder_uses_component_type_definitions_and_reusable_ref_setter(
    parts: tuple[str, str, str, str],
) -> None:
    component = _component()
    component_id = get_handle(component)

    external_id = api.addComponentExternalTypeDefinitions(component_id, "  external_types  ", parts)
    external = resolve_handle(external_id)
    assert isinstance(external, ExternalTypeDefinitions)
    assert external.name == "external_types"
    assert isinstance(component.type_definitions, ComponentType.TypeDefinitions)
    assert component.type_definitions.external_type_definitions == [external]
    assert (
        tuple(
            getattr(external.type_definitions_ref, attribute) for attribute in ("vendor", "library", "name", "version")
        )
        == parts
    )

    reference = external.type_definitions_ref
    reference_id = get_handle(reference)
    replacement = ("next.vendor", "next_library", "next_types", "3.0")
    assert api.setExternalTypeDefinitionsTypeDefinitionsRef(external_id, replacement)
    assert external.type_definitions_ref is reference
    assert resolve_handle(reference_id) is reference
    assert tuple(getattr(reference, attribute) for attribute in ("vendor", "library", "name", "version")) == replacement


def test_component_external_builder_normalizes_names_checks_unique_names_and_preserves_tuple_on_rejection() -> None:
    first = _external("existing")
    values = (first,)
    component = _component(type_definitions=ComponentType.TypeDefinitions(external_type_definitions=values))
    component_id = get_handle(component)

    _assert_fault(
        TgiFaultCode.ALREADY_EXISTS,
        api.addComponentExternalTypeDefinitions,
        component_id,
        "  existing  ",
        _VLNV,
    )
    assert component.type_definitions.external_type_definitions is values
    assert first.name == "existing"

    second_id = api.addComponentExternalTypeDefinitions(component_id, " second ", _VLNV)
    assert component.type_definitions.external_type_definitions == [first, resolve_handle(second_id)]
    assert resolve_handle(second_id).name == "second"


@pytest.mark.parametrize("bad_name", ["", "two words", "2starts_with_digit", None, 5])
def test_component_external_builder_rejects_bad_names_atomically(bad_name: object) -> None:
    component = _component()
    component_id = get_handle(component)
    _assert_fault(TgiFaultCode.INVALID_ARGUMENT, api.addComponentExternalTypeDefinitions, component_id, bad_name, _VLNV)
    assert component.type_definitions is None


@pytest.mark.parametrize(
    "bad_vlnv",
    [
        "vendor:library:name:1.0",
        ("vendor", "library", "name"),
        ("vendor", "library", "name", "1", "extra"),
        ("vendor", "library", "", "1.0"),
        ("vendor", "library", "name", "bad\x00version"),
        ("vendor", "library", "name", None),
    ],
)
def test_component_external_builder_rejects_invalid_vlnv_before_creating_optional_holder(bad_vlnv: object) -> None:
    component = _component()
    _assert_fault(
        TgiFaultCode.INVALID_ARGUMENT,
        api.addComponentExternalTypeDefinitions,
        get_handle(component),
        "external",
        bad_vlnv,
    )
    assert component.type_definitions is None


def test_component_external_builder_rejects_wrong_owner_and_malformed_holder_atomically() -> None:
    for handle in ("stale", get_handle(_root())):
        _assert_fault(TgiFaultCode.INVALID_ID, api.addComponentExternalTypeDefinitions, handle, "external", _VLNV)

    component = _component(type_definitions=object())
    holder = component.type_definitions
    _assert_fault(
        TgiFaultCode.INVALID_ID,
        api.addComponentExternalTypeDefinitions,
        get_handle(component),
        "external",
        _VLNV,
    )
    assert component.type_definitions is holder


@pytest.mark.parametrize(
    ("holder_attribute", "member_attribute"),
    [
        ("mode_links", "mode_link"),
        ("view_links", "view_link"),
    ],
    ids=("mode", "view"),
)
def test_external_links_build_typed_required_references_and_support_the_reference_setters(
    holder_attribute: str,
    member_attribute: str,
) -> None:
    external = _external()
    external_id = get_handle(external)
    if holder_attribute == "mode_links":
        link_id = api.addExternalTypeDefinitionsModeLink(external_id, " external_mode ", " local_mode ")
        link = resolve_handle(link_id)
        assert isinstance(link, ModeLinks.ModeLink)
        external_ref = link.external_mode_reference
        local_ref = link.mode_reference
        assert external_ref.mode_ref == "external_mode"
        assert local_ref.mode_ref == "local_mode"
        api.setModeLinkExternalModeReference(link_id, "target_not_registered")
        api.setModeLinkModeReference(link_id, "local_not_registered")
        assert link.external_mode_reference is external_ref and external_ref.mode_ref == "target_not_registered"
        assert link.mode_reference is local_ref and local_ref.mode_ref == "local_not_registered"
    else:
        link_id = api.addExternalTypeDefinitionsViewLink(external_id, " external_view ", " local_view ")
        link = resolve_handle(link_id)
        assert isinstance(link, ViewLinks.ViewLink)
        external_ref = link.external_view_reference
        local_ref = link.view_reference
        assert external_ref.view_ref == "external_view"
        assert local_ref.view_ref == "local_view"
        api.setViewLinkExternalViewReference(link_id, "target_not_registered")
        api.setViewLinkViewReference(link_id, "local_not_registered")
        assert link.external_view_reference is external_ref and external_ref.view_ref == "target_not_registered"
        assert link.view_reference is local_ref and local_ref.view_ref == "local_not_registered"

    holder = getattr(external, holder_attribute)
    assert isinstance(holder, ModeLinks | ViewLinks)
    assert getattr(holder, member_attribute) == [link]
    holder_id = get_handle(holder)
    assert get_parent_info(holder_id).parent_handle == external_id
    assert get_parent_info(link_id).parent_handle == holder_id
    assert get_parent_info(get_handle(external_ref)).parent_handle == link_id
    assert get_parent_info(get_handle(local_ref)).parent_handle == link_id


def test_external_mode_and_view_link_adders_reject_duplicate_local_references_without_tuple_normalization() -> None:
    mode = _mode_link("external_a", "active")
    mode_values = (mode,)
    external = _external(mode_links=ModeLinks(mode_link=mode_values), view_links=ViewLinks(view_link=(_view_link(),)))
    external_id = get_handle(external)

    _assert_fault(
        TgiFaultCode.ALREADY_EXISTS,
        api.addExternalTypeDefinitionsModeLink,
        external_id,
        " external_a ",
        "other",
    )
    _assert_fault(
        TgiFaultCode.ALREADY_EXISTS,
        api.addExternalTypeDefinitionsModeLink,
        external_id,
        "external_b",
        " active ",
    )
    assert external.mode_links.mode_link is mode_values

    view = _view_link("external_a", "rtl")
    view_values = (view,)
    external.view_links.view_link = view_values
    _assert_fault(
        TgiFaultCode.ALREADY_EXISTS,
        api.addExternalTypeDefinitionsViewLink,
        external_id,
        " external_a ",
        "other",
    )
    _assert_fault(
        TgiFaultCode.ALREADY_EXISTS,
        api.addExternalTypeDefinitionsViewLink,
        external_id,
        "external_b",
        "rtl",
    )
    assert external.view_links.view_link is view_values


@pytest.mark.parametrize(
    ("operation", "arguments"),
    [
        (api.addExternalTypeDefinitionsModeLink, ("missing", "ext", "local")),
        (api.addExternalTypeDefinitionsViewLink, ("missing", "ext", "local")),
    ],
)
def test_external_link_adders_reject_wrong_owners_bad_names_and_malformed_holders_atomically(
    operation: object, arguments: tuple[str, str, str]
) -> None:
    external = _external()
    valid_id = get_handle(external)
    for handle in ("stale", get_handle(_root())):
        _assert_fault(TgiFaultCode.INVALID_ID, operation, handle, *arguments[1:])

    for bad_name in ("", "bad name", "1bad", None, object()):
        _assert_fault(TgiFaultCode.INVALID_ARGUMENT, operation, valid_id, bad_name, "valid_local")
        _assert_fault(TgiFaultCode.INVALID_ARGUMENT, operation, valid_id, "valid_external", bad_name)
        assert external.mode_links is None and external.view_links is None

    external.mode_links = object()
    malformed = external.mode_links
    _assert_fault(TgiFaultCode.INVALID_ID, api.addExternalTypeDefinitionsModeLink, valid_id, "ext", "local")
    assert external.mode_links is malformed and external.view_links is None


def test_root_external_builder_uses_generated_direct_list_and_checks_names_atomically() -> None:
    existing = _external("present")
    values = (existing,)
    root = _root(external_type_definitions=values)
    root_id = get_handle(root)

    _assert_fault(
        TgiFaultCode.ALREADY_EXISTS,
        api.addTypeDefinitionsExternalTypeDefinitions,
        root_id,
        " present ",
        _VLNV,
    )
    assert root.external_type_definitions is values

    child_id = api.addTypeDefinitionsExternalTypeDefinitions(root_id, "  next  ", _VLNV)
    child = resolve_handle(child_id)
    assert isinstance(child, ExternalTypeDefinitions) and child.name == "next"
    assert isinstance(child.type_definitions_ref, ConfigurableLibraryRefType)
    assert root.external_type_definitions == [existing, child]
    assert get_parent_info(child_id).parent_handle == root_id


@pytest.mark.parametrize("bad_vlnv", [("v", "l", "n"), ("v", "l", "", "1"), ("v", "l", "n", "\x00"), 7])
def test_root_external_builder_rejects_invalid_vlnv_and_bad_names_without_normalizing_tuple(bad_vlnv: object) -> None:
    existing = _external()
    values = (existing,)
    root = _root(external_type_definitions=values)
    root_id = get_handle(root)

    _assert_fault(
        TgiFaultCode.INVALID_ARGUMENT,
        api.addTypeDefinitionsExternalTypeDefinitions,
        root_id,
        "next",
        bad_vlnv,
    )
    _assert_fault(
        TgiFaultCode.INVALID_ARGUMENT,
        api.addTypeDefinitionsExternalTypeDefinitions,
        root_id,
        "bad name",
        _VLNV,
    )
    assert root.external_type_definitions is values


def test_component_external_remover_uses_parsed_ownership_invalidates_descendants_and_prunes_last_holder() -> None:
    configured = ConfigurableElementValue(value="configured", reference_id="PARAM", id="value-id")
    values = ConfigurableElementValues(configurable_element_value=(configured,))
    reference = ConfigurableLibraryRefType(
        vendor="vendor",
        library="library",
        name="external",
        version="1.0",
        configurable_element_values=values,
        id="ref-id",
    )
    target = _external("target", parts=("vendor", "library", "external", "1.0"))
    target.type_definitions_ref = reference
    peer = _external("peer")
    component = _component(type_definitions=ComponentType.TypeDefinitions(external_type_definitions=(target, peer)))
    parsed = _round_trip(component, Component)
    assert isinstance(parsed, Component)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))

    target = parsed.type_definitions.external_type_definitions[0]
    peer = parsed.type_definitions.external_type_definitions[1]
    target_id = get_handle(target)
    peer_id = get_handle(peer)
    reference_id = get_handle(target.type_definitions_ref)
    values_id = get_handle(target.type_definitions_ref.configurable_element_values)
    value_id = get_handle(target.type_definitions_ref.configurable_element_values.configurable_element_value[0])
    holder = parsed.type_definitions
    holder_id = get_handle(holder)

    assert api.removeComponentExternalTypeDefinitions(target_id)
    assert resolve_handle(target_id) is None
    assert resolve_handle(reference_id) is None
    assert resolve_handle(values_id) is None
    assert resolve_handle(value_id) is None
    assert resolve_handle(peer_id) is peer
    assert parsed.type_definitions is holder
    assert holder.external_type_definitions == [peer]
    assert resolve_handle(holder_id) is holder

    assert api.removeComponentExternalTypeDefinitions(peer_id)
    assert parsed.type_definitions is None
    assert resolve_handle(peer_id) is None
    assert resolve_handle(holder_id) is None


def test_component_external_remover_rejects_stale_or_non_component_ownership() -> None:
    for handle in ("stale", get_handle(_component())):
        _assert_fault(TgiFaultCode.INVALID_ID, api.removeComponentExternalTypeDefinitions, handle)

    standalone = _external()
    _assert_fault(TgiFaultCode.INVALID_ID, api.removeComponentExternalTypeDefinitions, get_handle(standalone))

    root_external = _external()
    root = _root(external_type_definitions=(root_external,))
    _assert_fault(
        TgiFaultCode.INVALID_ID,
        api.removeComponentExternalTypeDefinitions,
        get_handle(root_external),
    )
    assert root.external_type_definitions == (root_external,)


def test_component_external_remover_rejects_misleading_owner_and_malformed_membership_atomically() -> None:
    child = _external()
    component = _component(type_definitions=ComponentType.TypeDefinitions(external_type_definitions=()))
    child_id = get_handle(child)
    register_parent(child, component.type_definitions, ("external_type_definitions",), "list")
    _assert_fault(TgiFaultCode.INVALID_ID, api.removeComponentExternalTypeDefinitions, child_id)
    assert component.type_definitions.external_type_definitions == ()

    malformed = _external()
    bad_values = (malformed, object())
    bad_component = _component(type_definitions=ComponentType.TypeDefinitions(external_type_definitions=bad_values))
    registry.register(
        bad_component, (bad_component.vendor, bad_component.library, bad_component.name, bad_component.version)
    )
    malformed_id = get_handle(malformed)
    _assert_fault(TgiFaultCode.INVALID_ID, api.removeComponentExternalTypeDefinitions, malformed_id)
    assert bad_component.type_definitions.external_type_definitions is bad_values
    assert resolve_handle(malformed_id) is malformed


def test_external_builders_round_trip_component_and_type_definition_references() -> None:
    component = _component(
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")]),
        model=Model(views=ModelType.Views(view=[ModelType.Views.View(name="rtl")])),
    )
    target_id = api.addComponentExternalTypeDefinitions(get_handle(component), "ext_types", _VLNV)
    assert isinstance(resolve_handle(target_id), ExternalTypeDefinitions)
    assert api.addExternalTypeDefinitionsModeLink(target_id, "power", "active")
    assert api.addExternalTypeDefinitionsViewLink(target_id, "rtl_view", "rtl")
    parsed_component = _round_trip(component, Component)
    component_external = parsed_component.type_definitions.external_type_definitions[0]
    assert component_external.mode_links.mode_link[0].external_mode_reference.mode_ref == "power"
    assert component_external.mode_links.mode_link[0].mode_reference.mode_ref == "active"
    assert component_external.view_links.view_link[0].external_view_reference.view_ref == "rtl_view"
    assert component_external.view_links.view_link[0].view_reference.view_ref == "rtl"
    assert component_external.type_definitions_ref.name == "shared"

    root = _root()
    root_external_id = api.addTypeDefinitionsExternalTypeDefinitions(get_handle(root), "ext_types", _VLNV)
    assert resolve_handle(root_external_id).type_definitions_ref.name == "shared"
    parsed_root = _round_trip(root, TypeDefinitions)
    assert parsed_root.external_type_definitions[0].type_definitions_ref.name == "shared"
