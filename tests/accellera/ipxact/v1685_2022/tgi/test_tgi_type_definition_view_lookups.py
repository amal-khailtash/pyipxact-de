"""Type-definition view links resolve typed references and local targets."""

from collections.abc import Callable, Iterator, Sequence
from inspect import signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import component as component_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.external_type_definitions import ExternalTypeDefinitions
from org.accellera.ipxact.v1685_2022.model import Model
from org.accellera.ipxact.v1685_2022.model_type import ModelType
from org.accellera.ipxact.v1685_2022.type_definitions import TypeDefinitions
from org.accellera.ipxact.v1685_2022.view_links import ViewLinks

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_SOURCE_VLNV = ("acme", "types", "source", "1.0")
_TARGET_VLNV = ("acme", "types", "target", "1.0")


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _library_ref(vlnv: tuple[str, str, str, str] = _TARGET_VLNV) -> ConfigurableLibraryRefType:
    return ConfigurableLibraryRefType(vendor=vlnv[0], library=vlnv[1], name=vlnv[2], version=vlnv[3])


def _link(external_name: str = "external_view", local_name: str = "rtl") -> ViewLinks.ViewLink:
    return ViewLinks.ViewLink(
        external_view_reference=ViewLinks.ViewLink.ExternalViewReference(view_ref=external_name),
        view_reference=ViewLinks.ViewLink.ViewReference(view_ref=local_name),
    )


def _type_definitions(
    name: str,
    *,
    ref_vlnv: tuple[str, str, str, str] = _TARGET_VLNV,
    links: Sequence[ViewLinks.ViewLink] | None = None,
    view_names: Sequence[str] = (),
    include_external: bool = False,
) -> TypeDefinitions:
    return TypeDefinitions(
        vendor="acme",
        library="types",
        name=name,
        version="1.0",
        external_type_definitions=(
            [
                ExternalTypeDefinitions(
                    name="external_types",
                    type_definitions_ref=_library_ref(ref_vlnv),
                    view_links=ViewLinks(view_link=list(links)) if links is not None else None,
                )
            ]
            if include_external or links is not None
            else []
        ),
        views=TypeDefinitions.Views(view=[TypeDefinitions.Views.View(name=view_name) for view_name in view_names])
        if view_names
        else None,
    )


def _validated_round_trip(
    document: Component | TypeDefinitions, root_type: type[Component] | type[TypeDefinitions]
) -> Component | TypeDefinitions:
    xml = XmlDocument.serializer().render(document)
    tree = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(tree), _SCHEMA.error_log
    return XmlDocument.parser().from_string(xml, root_type)


def _register_type_definitions(
    document: TypeDefinitions, vlnv: tuple[str, str, str, str] | None = None
) -> TypeDefinitions:
    loaded = _validated_round_trip(document, TypeDefinitions)
    identity = vlnv or (loaded.vendor, loaded.library, loaded.name, loaded.version)
    registry.register(loaded, identity)
    return loaded


def _source_and_link(
    *,
    target_vlnv: tuple[str, str, str, str] = _TARGET_VLNV,
    local_names: Sequence[str] = ("rtl",),
    external_name: str = "external_view",
) -> tuple[TypeDefinitions, str, TypeDefinitions]:
    source_document = _type_definitions(
        "source",
        ref_vlnv=target_vlnv,
        links=[_link(external_name, "rtl")],
        view_names=local_names,
    )
    if "rtl" in local_names:
        source = _register_type_definitions(source_document, _SOURCE_VLNV)
    else:
        source = source_document
        registry.register(source, _SOURCE_VLNV)
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(source))[0]
    link_id = api.getExternalTypeDefinitionsViewLinkIDs(external_id)[0]
    return source, link_id, source


def _assert_fault(expected_code: str, operation: Callable[..., object], *args: object) -> None:
    with pytest.raises(TgiError) as error:
        operation(*args)
    assert error.value.fault_code == expected_code


def test_public_signatures_docs_and_exports() -> None:
    contracts = {
        "getViewLinkExternalViewReferenceRefByName": ("viewLinkID", str, "F.7.81.43"),
        "getViewLinkExternalViewReferenceID": ("viewLinkID", str, "F.7.81.44"),
        "getViewLinkViewReferenceRefByID": ("viewLinkID", str, "F.7.81.45"),
        "getViewLinkViewReferenceRefByName": ("viewLinkID", str, "F.7.81.46"),
        "getViewLinkViewReferenceID": ("viewLinkID", str, "F.7.81.47"),
        "getExternalTypeDefinitionsTypeDefinitionsRefByVLNV": (
            "externalTypeDefinitionsID",
            tuple[str, str, str, str],
            "F.7.81.14",
        ),
        "getExternalTypeDefinitionsTypeDefinitionsRefByID": (
            "externalTypeDefinitionsID",
            str,
            "F.7.81.13",
        ),
    }

    for name, (parameter, return_type, section) in contracts.items():
        operation = getattr(api, name)
        assert name in api.__all__
        assert tuple(signature(operation).parameters) == (parameter,)
        assert signature(operation).parameters[parameter].annotation is str
        assert signature(operation).return_annotation == return_type
        assert f"Section: {section}." in operation.__doc__


def test_view_link_getters_return_typed_reference_handles_and_normalized_names() -> None:
    link = _link("  λ_external\t", "\nrtl_β  ")
    link_id = get_handle(link)

    external_id = api.getViewLinkExternalViewReferenceID(link_id)
    local_id = api.getViewLinkViewReferenceID(link_id)
    assert resolve_handle(external_id) is link.external_view_reference
    assert resolve_handle(local_id) is link.view_reference
    assert api.getViewLinkExternalViewReferenceRefByName(link_id) == "λ_external"
    assert api.getViewLinkViewReferenceRefByName(link_id) == "rtl_β"
    assert link.external_view_reference.view_ref == "  λ_external\t"
    assert link.view_reference.view_ref == "\nrtl_β  "


@pytest.mark.parametrize(
    "operation",
    [
        api.getViewLinkExternalViewReferenceRefByName,
        api.getViewLinkExternalViewReferenceID,
        api.getViewLinkViewReferenceRefByID,
        api.getViewLinkViewReferenceRefByName,
        api.getViewLinkViewReferenceID,
    ],
)
def test_view_link_getters_reject_untyped_or_missing_source_handles(operation: Callable[[str], str]) -> None:
    _assert_fault(TgiFaultCode.INVALID_ID, operation, get_handle(object()))
    _assert_fault(TgiFaultCode.INVALID_ID, operation, "missing")


@pytest.mark.parametrize(
    ("getter", "attribute", "reference_type"),
    [
        (
            api.getViewLinkExternalViewReferenceID,
            "external_view_reference",
            ViewLinks.ViewLink.ExternalViewReference,
        ),
        (api.getViewLinkViewReferenceID, "view_reference", ViewLinks.ViewLink.ViewReference),
    ],
)
def test_view_link_reference_ids_reject_bad_or_missing_required_typed_children(
    getter: Callable[[str], str],
    attribute: str,
    reference_type: type[ViewLinks.ViewLink.ExternalViewReference] | type[ViewLinks.ViewLink.ViewReference],
) -> None:
    link = _link()
    link_id = get_handle(link)
    setattr(link, attribute, object())
    _assert_fault(TgiFaultCode.INVALID_ID, getter, link_id)
    setattr(link, attribute, None)
    _assert_fault(TgiFaultCode.INVALID_ID, getter, link_id)

    setattr(link, attribute, reference_type(view_ref="valid_name"))
    assert resolve_handle(getter(link_id)) is getattr(link, attribute)


@pytest.mark.parametrize(
    ("getter", "attribute"),
    [
        (api.getViewLinkExternalViewReferenceRefByName, "external_view_reference"),
        (api.getViewLinkViewReferenceRefByName, "view_reference"),
    ],
)
@pytest.mark.parametrize("bad_name", ["", "   ", "1starts_with_digit", "has space"])
def test_view_link_name_getters_reject_invalid_xml_names_and_keep_typed_source_reachable(
    getter: Callable[[str], str], attribute: str, bad_name: str
) -> None:
    link = _link()
    reference = getattr(link, attribute)
    reference.view_ref = bad_name
    link_id = get_handle(link)

    _assert_fault(TgiFaultCode.INVALID_ID, getter, link_id)
    reference_id_getter = (
        api.getViewLinkExternalViewReferenceID
        if attribute == "external_view_reference"
        else api.getViewLinkViewReferenceID
    )
    assert resolve_handle(reference_id_getter(link_id)) is reference
    assert reference.view_ref == bad_name


def test_view_reference_by_id_resolves_the_exact_local_type_definition_view() -> None:
    _, link_id, target = _source_and_link()

    target_view_id = api.getViewLinkViewReferenceRefByID(link_id)
    assert resolve_handle(target_view_id) is target.views.view[0]
    assert target_view_id != api.getViewLinkViewReferenceID(link_id)


def test_view_reference_lookup_normalizes_source_and_candidate_names_without_rewriting_source() -> None:
    raw_name = " \tλ_view  "
    source = _type_definitions("source", links=[_link(local_name=raw_name)], view_names=(raw_name,))
    registry.register(source, _SOURCE_VLNV)
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(source))[0]
    link_id = api.getExternalTypeDefinitionsViewLinkIDs(external_id)[0]

    assert api.getViewLinkViewReferenceRefByName(link_id) == "λ_view"
    target_view_id = api.getViewLinkViewReferenceRefByID(link_id)
    assert resolve_handle(target_view_id) is source.views.view[0]
    assert source.external_type_definitions[0].view_links.view_link[0].view_reference.view_ref == raw_name
    assert source.views.view[0].name == raw_name


def test_view_reference_by_id_accepts_component_model_views() -> None:
    component_type = ComponentType(
        vendor="acme",
        library="devices",
        name="component_target",
        version="1.0",
        model=Model(views=ModelType.Views(view=[ModelType.Views.View(name="rtl")])),
        type_definitions=ComponentType.TypeDefinitions(
            external_type_definitions=[
                ExternalTypeDefinitions(
                    name="external_types",
                    type_definitions_ref=_library_ref(),
                    view_links=ViewLinks(view_link=[_link()]),
                )
            ]
        ),
    )
    registry.register(component_type, ("acme", "devices", "component_target", "1.0"))
    external_id = component_api.getComponentExternalTypeDefinitionsIDs(get_handle(component_type))
    assert external_id
    external_id = external_id[0]
    link_id = api.getExternalTypeDefinitionsViewLinkIDs(external_id)[0]

    target_view_id = api.getViewLinkViewReferenceRefByID(link_id)
    assert resolve_handle(target_view_id) is component_type.model.views.view[0]


def test_view_reference_target_lookup_uses_registered_ownership_and_reports_missing_or_duplicate_matches() -> None:
    _, link_id, _ = _source_and_link(local_names=())
    _register_type_definitions(_type_definitions("other", view_names=("rtl",)), ("acme", "types", "other", "1.0"))
    _assert_fault(TgiFaultCode.NOT_FOUND, api.getViewLinkViewReferenceRefByID, link_id)

    duplicate_source = _type_definitions(
        "duplicate_link_source",
        ref_vlnv=("acme", "types", "duplicate", "1.0"),
        links=[_link()],
        view_names=("rtl", "rtl"),
    )
    registry.register(duplicate_source, ("acme", "types", "duplicate_link_source", "1.0"))
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(duplicate_source))[0]
    duplicate_link_id = api.getExternalTypeDefinitionsViewLinkIDs(external_id)[0]
    _assert_fault(TgiFaultCode.INVALID_ARGUMENT, api.getViewLinkViewReferenceRefByID, duplicate_link_id)


def test_cross_root_same_name_does_not_satisfy_unregistered_source_target() -> None:
    _, link_id, _ = _source_and_link(local_names=())
    unrelated = _register_type_definitions(_type_definitions("unrelated", view_names=("rtl",)))

    assert unrelated.views.view[0].name == "rtl"
    _assert_fault(TgiFaultCode.NOT_FOUND, api.getViewLinkViewReferenceRefByID, link_id)


def test_parsed_schema_valid_type_definition_link_keeps_target_ownership_after_registry_registration() -> None:
    source, link_id, target = _source_and_link()

    rendered = XmlDocument.serializer().render(source)
    reloaded = XmlDocument.parser().from_string(rendered, TypeDefinitions)
    registry.register(reloaded, _SOURCE_VLNV, replace=True)
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(reloaded))[0]
    parsed_link_id = api.getExternalTypeDefinitionsViewLinkIDs(external_id)[0]
    parsed_target_id = api.getViewLinkViewReferenceRefByID(parsed_link_id)

    assert resolve_handle(parsed_target_id) is reloaded.views.view[0]
    rendered_root = etree.fromstring(rendered.encode())
    assert rendered_root.find(".//{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}viewLink") is not None
    assert link_id != parsed_link_id


def test_external_type_definitions_vlnv_returns_native_tuple_and_validates_source() -> None:
    source_parts = (" acme ", "type library", "target", " 1.0 ")
    source = _type_definitions("source", ref_vlnv=source_parts, include_external=True)
    external = source.external_type_definitions[0]
    external_id = get_handle(external)

    vlnv = api.getExternalTypeDefinitionsTypeDefinitionsRefByVLNV(external_id)
    assert type(vlnv) is tuple
    assert vlnv == source_parts

    external.type_definitions_ref = None
    _assert_fault(TgiFaultCode.INVALID_ID, api.getExternalTypeDefinitionsTypeDefinitionsRefByVLNV, external_id)
    external.type_definitions_ref = object()
    _assert_fault(TgiFaultCode.INVALID_ID, api.getExternalTypeDefinitionsTypeDefinitionsRefByVLNV, external_id)
    external.type_definitions_ref = _library_ref(("acme", "bad\x00library", "target", "1.0"))
    _assert_fault(TgiFaultCode.INVALID_ID, api.getExternalTypeDefinitionsTypeDefinitionsRefByVLNV, external_id)
    _assert_fault(TgiFaultCode.INVALID_ID, api.getExternalTypeDefinitionsTypeDefinitionsRefByVLNV, get_handle(source))


def test_external_type_definitions_vlnv_is_available_even_when_target_is_not_registered() -> None:
    source = _register_type_definitions(
        _type_definitions("source", ref_vlnv=("acme", "types", "absent", "9.0"), include_external=True),
        _SOURCE_VLNV,
    )
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(source))[0]

    assert api.getExternalTypeDefinitionsTypeDefinitionsRefByVLNV(external_id) == (
        "acme",
        "types",
        "absent",
        "9.0",
    )
    assert registry.get_id(("acme", "types", "absent", "9.0")) is None
    _assert_fault(TgiFaultCode.NOT_FOUND, api.getExternalTypeDefinitionsTypeDefinitionsRefByID, external_id)
    assert registry.get_id(("acme", "types", "absent", "9.0")) is None


def test_external_type_definitions_target_id_requires_registered_2022_type_definitions() -> None:
    source, _, _ = _source_and_link()
    target = _register_type_definitions(_type_definitions("target"), _TARGET_VLNV)
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(source))[0]

    target_id = api.getExternalTypeDefinitionsTypeDefinitionsRefByID(external_id)
    assert resolve_handle(target_id) is target
    assert isinstance(resolve_handle(target_id), TypeDefinitions)
    _assert_fault(TgiFaultCode.INVALID_ID, api.getExternalTypeDefinitionsTypeDefinitionsRefByID, get_handle(source))

    _assert_fault(TgiFaultCode.INVALID_ID, api.getExternalTypeDefinitionsTypeDefinitionsRefByID, "missing")

    registry.clear()
    source = _register_type_definitions(_type_definitions("source", include_external=True), _SOURCE_VLNV)
    wrong_target = Component(vendor="acme", library="types", name="target", version="1.0")
    registry.register(wrong_target, _TARGET_VLNV)
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(source))[0]
    _assert_fault(TgiFaultCode.NOT_FOUND, api.getExternalTypeDefinitionsTypeDefinitionsRefByID, external_id)

    registry.clear()
    source = _register_type_definitions(
        _type_definitions("source", include_external=True),
        _SOURCE_VLNV,
    )
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(source))[0]
    old_target = _type_definitions("target")
    registry.register(old_target, _TARGET_VLNV, standard="ipxact", schema_version="1685-2014")
    _assert_fault(TgiFaultCode.NOT_FOUND, api.getExternalTypeDefinitionsTypeDefinitionsRefByID, external_id)


def test_external_type_definitions_target_id_returns_source_vlnv_when_target_is_absent() -> None:
    source = _register_type_definitions(
        _type_definitions(
            "source",
            ref_vlnv=("acme", "types", "unavailable", "2.0"),
            links=[_link()],
            view_names=("rtl",),
        ),
        _SOURCE_VLNV,
    )
    external_id = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(source))[0]

    _assert_fault(TgiFaultCode.NOT_FOUND, api.getExternalTypeDefinitionsTypeDefinitionsRefByID, external_id)
    assert api.getExternalTypeDefinitionsTypeDefinitionsRefByVLNV(external_id) == (
        "acme",
        "types",
        "unavailable",
        "2.0",
    )
