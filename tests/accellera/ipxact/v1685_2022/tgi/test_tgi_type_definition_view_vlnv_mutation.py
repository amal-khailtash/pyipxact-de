"""Mutation contracts for type-definition view references, VLNV refs, and members."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from inspect import getdoc, signature
from typing import Any

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ConfigurableElementValue,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    Description,
    ExternalTypeDefinitions,
    TypeDefinitions,
    ViewLinks,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_VLNV = ("acme", "types", "shared", "1.0")


@dataclass(frozen=True)
class _ViewSetter:
    name: str
    section: str
    parameter: str
    attribute: str
    source_attribute: str
    reference_type: type[Any]
    setter: Callable[[str, str], bool]
    external: bool


_VIEW_SETTERS = (
    _ViewSetter(
        "setViewLinkExternalViewReference",
        "F.7.82.56",
        "viewRef",
        "external_view_reference",
        "view_ref",
        ViewLinks.ViewLink.ExternalViewReference,
        api.setViewLinkExternalViewReference,
        True,
    ),
    _ViewSetter(
        "setViewLinkViewReference",
        "F.7.82.57",
        "viewRef",
        "view_reference",
        "view_ref",
        ViewLinks.ViewLink.ViewReference,
        api.setViewLinkViewReference,
        False,
    ),
)


@dataclass(frozen=True)
class _RootMember:
    name: str
    section: str
    parameter: str
    holder_attribute: str
    member_attribute: str
    holder_type: type[Any]
    member_type: type[Any]
    ids_getter: Callable[[str], list[str]]
    remover: Callable[[str], bool]


_ROOT_MEMBERS = (
    _RootMember(
        "removeTypeDefinitionsMode",
        "F.7.82.41",
        "modeID",
        "modes",
        "mode",
        TypeDefinitions.Modes,
        TypeDefinitions.Modes.Mode,
        api.getTypeDefinitionsModeIDs,
        api.removeTypeDefinitionsMode,
    ),
    _RootMember(
        "removeTypeDefinitionsResetType",
        "F.7.82.44",
        "resetTypeID",
        "reset_types",
        "reset_type",
        TypeDefinitions.ResetTypes,
        TypeDefinitions.ResetTypes.ResetType,
        api.getTypeDefinitionsResetTypeIDs,
        api.removeTypeDefinitionsResetType,
    ),
    _RootMember(
        "removeTypeDefinitionsView",
        "F.7.82.45",
        "viewID",
        "views",
        "view",
        TypeDefinitions.Views,
        TypeDefinitions.Views.View,
        api.getTypeDefinitionsViewIDs,
        api.removeTypeDefinitionsView,
    ),
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _assert_fault(code: str, operation: Callable[..., object], *args: object) -> None:
    with pytest.raises(TgiError) as error:
        operation(*args)
    assert error.value.fault_code == code


def _view_link(external: str = "external_view", local: str = "rtl") -> ViewLinks.ViewLink:
    return ViewLinks.ViewLink(
        external_view_reference=ViewLinks.ViewLink.ExternalViewReference(view_ref=external),
        view_reference=ViewLinks.ViewLink.ViewReference(view_ref=local),
    )


def _external_type_definitions(
    *,
    reference: ConfigurableLibraryRefType | None = None,
    view_links: ViewLinks | None = None,
) -> ExternalTypeDefinitions:
    return ExternalTypeDefinitions(
        name="external_types",
        type_definitions_ref=reference
        or ConfigurableLibraryRefType(vendor=_VLNV[0], library=_VLNV[1], name=_VLNV[2], version=_VLNV[3]),
        view_links=view_links,
    )


def _root(**values: Any) -> TypeDefinitions:
    return TypeDefinitions(vendor="acme", library="types", name="device_types", version="1.0", **values)


def _round_trip(root: TypeDefinitions) -> TypeDefinitions:
    xml = XmlDocument.serializer().render(root)
    element = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(element), _SCHEMA.error_log
    loaded = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert XmlDocument.serializer().render(loaded) == xml
    return loaded


def test_public_mutation_signatures_docs_and_exports() -> None:
    operations = (
        *((case.name, ("viewLinkID", case.parameter), (str, str), case.section) for case in _VIEW_SETTERS),
        (
            "setExternalTypeDefinitionsTypeDefinitionsRef",
            ("externalTypeDefinitionsID", "typeDefinitionsRef"),
            (str, tuple[str, str, str, str]),
            "F.7.82.49",
        ),
        *((case.name, (case.parameter,), (str,), case.section) for case in _ROOT_MEMBERS),
    )
    for name, parameters, annotations, section in operations:
        operation = getattr(api, name)
        assert getattr(root_api, name) is operation
        assert name in api.__all__ and name in root_api.__all__
        operation_signature = signature(operation)
        assert tuple(operation_signature.parameters) == parameters
        assert tuple(item.annotation for item in operation_signature.parameters.values()) == annotations
        assert all(item.default is item.empty for item in operation_signature.parameters.values())
        assert operation_signature.return_annotation is bool
        doc = getdoc(operation)
        assert doc is not None and f"Section: {section}." in doc
        assert "Args:" in doc and "Returns:" in doc


@pytest.mark.parametrize("case", _VIEW_SETTERS, ids=lambda case: case.name)
def test_view_reference_setters_preserve_typed_wrapper_and_allow_xml_names_without_lookup(
    case: _ViewSetter,
) -> None:
    link = _view_link()
    link.id = "kept-link-id"
    wrapper = getattr(link, case.attribute)
    wrapper_id = get_handle(wrapper)
    link_id = get_handle(link)

    assert case.setter(link_id, "prefix:δ_view")
    assert getattr(link, case.attribute) is wrapper
    assert type(wrapper) is case.reference_type
    assert getattr(wrapper, case.source_attribute) == "prefix:δ_view"
    assert resolve_handle(wrapper_id) is wrapper
    # A reference name is XML Name source; target registration is not required.
    assert case.setter(link_id, "missing_target")
    assert getattr(wrapper, case.source_attribute) == "missing_target"


@pytest.mark.parametrize("case", _VIEW_SETTERS, ids=lambda case: case.name)
def test_view_reference_setters_create_missing_wrappers_and_repair_bad_source(case: _ViewSetter) -> None:
    link = _view_link()
    link_id = get_handle(link)
    setattr(link, case.attribute, None)
    assert case.setter(link_id, "created_view")
    wrapper = getattr(link, case.attribute)
    assert type(wrapper) is case.reference_type
    assert getattr(wrapper, case.source_attribute) == "created_view"

    setattr(wrapper, case.source_attribute, object())
    assert case.setter(link_id, "repaired_view")
    assert getattr(link, case.attribute) is wrapper
    assert getattr(wrapper, case.source_attribute) == "repaired_view"


@pytest.mark.parametrize("case", _VIEW_SETTERS, ids=lambda case: case.name)
def test_view_reference_setters_reject_wrong_owners_wrappers_and_bad_names_atomically(case: _ViewSetter) -> None:
    link = _view_link("stable_external", "stable_local")
    link_id = get_handle(link)
    wrapper = getattr(link, case.attribute)
    original_source = getattr(wrapper, case.source_attribute)

    _assert_fault(TgiFaultCode.INVALID_ID, case.setter, get_handle(object()), "valid_name")
    _assert_fault(TgiFaultCode.INVALID_ID, case.setter, get_handle(_root()), "valid_name")
    wrong_owner = TypeDefinitions.Views.View(name="wrong_owner")
    _assert_fault(TgiFaultCode.INVALID_ID, case.setter, get_handle(wrong_owner), "valid_name")

    foreign_type = (
        ViewLinks.ViewLink.ViewReference
        if case.reference_type is ViewLinks.ViewLink.ExternalViewReference
        else ViewLinks.ViewLink.ExternalViewReference
    )
    foreign = foreign_type(view_ref="foreign")
    setattr(link, case.attribute, foreign)
    _assert_fault(TgiFaultCode.INVALID_ID, case.setter, link_id, "valid_name")
    assert getattr(link, case.attribute) is foreign
    setattr(link, case.attribute, wrapper)

    for invalid in (None, 7, "", "   ", "1starts_with_digit", "has space", "bad\x00name"):
        _assert_fault(TgiFaultCode.INVALID_ARGUMENT, case.setter, link_id, invalid)
        assert getattr(link, case.attribute) is wrapper
        assert getattr(wrapper, case.source_attribute) == original_source


def test_internal_view_reference_setter_checks_known_sibling_names_after_normalization() -> None:
    first = _view_link("external_a", " \trtl  ")
    second = _view_link("external_b", "other")
    holder = ViewLinks(view_link=(first, second))
    external = _external_type_definitions(view_links=holder)
    root = _root(external_type_definitions=(external,))
    external_id = get_handle(external)
    api.getExternalTypeDefinitionsViewLinkIDs(external_id)
    second_id = get_handle(second)
    before = second.view_reference.view_ref

    _assert_fault(TgiFaultCode.ALREADY_EXISTS, api.setViewLinkViewReference, second_id, "rtl")
    assert second.view_reference.view_ref == before
    assert root.external_type_definitions == (external,)


def test_internal_view_reference_setter_allows_standalone_reference_without_known_holder() -> None:
    link = _view_link()
    assert api.setViewLinkViewReference(get_handle(link), "local:未登録")
    assert link.view_reference.view_ref == "local:未登録"


def test_view_setters_round_trip_as_schema_valid_references() -> None:
    link = _view_link()
    root = _root(
        external_type_definitions=(_external_type_definitions(view_links=ViewLinks(view_link=(link,))),),
        views=TypeDefinitions.Views(view=(TypeDefinitions.Views.View(name="local:view"),)),
    )
    assert api.setViewLinkExternalViewReference(get_handle(link), "external:target")
    assert api.setViewLinkViewReference(get_handle(link), "local:view")
    reparsed = _round_trip(root)
    parsed_link = reparsed.external_type_definitions[0].view_links.view_link[0]
    assert parsed_link.external_view_reference.view_ref == "external:target"
    assert parsed_link.view_reference.view_ref == "local:view"


@pytest.mark.parametrize(
    "parts",
    [
        (" vendor ", "library name", "target:types", " 1.0 "),
        ["vendor", "library", "target", "2.0"],
    ],
    ids=("tuple-preserves-source", "list-input"),
)
def test_vlnv_setter_accepts_four_raw_xml_strings_and_preserves_reference_metadata(parts: Any) -> None:
    value = ConfigurableElementValue(value="configured", reference_id="CONFIG_ID", id="value-id")
    values = ConfigurableElementValues(configurable_element_value=(value,))
    reference = ConfigurableLibraryRefType(
        vendor="old-vendor",
        library="old-library",
        name="old-name",
        version="old-version",
        configurable_element_values=values,
        id="ref-id",
    )
    external = _external_type_definitions(reference=reference)
    external_id = get_handle(external)
    reference_id = get_handle(reference)
    values_id = get_handle(values)
    value_id = get_handle(value)

    assert api.setExternalTypeDefinitionsTypeDefinitionsRef(external_id, parts)
    assert external.type_definitions_ref is reference
    assert tuple(getattr(reference, item) for item in ("vendor", "library", "name", "version")) == tuple(parts)
    assert reference.id == "ref-id"
    assert reference.configurable_element_values is values
    assert values.configurable_element_value == (value,)
    assert value.value == "configured" and value.reference_id == "CONFIG_ID" and value.id == "value-id"
    assert tuple(resolve_handle(item) for item in (reference_id, values_id, value_id)) == (reference, values, value)
    assert get_parent_info(reference_id).parent_handle == external_id
    assert get_parent_info(values_id).parent_handle == reference_id
    assert get_parent_info(value_id).parent_handle == values_id


@pytest.mark.parametrize(
    "bad_value",
    [
        "vendor:library:name:1.0",
        4,
        ("v", "l", "n"),
        ("v", "l", "n", "1", "extra"),
        ("v", "l", "", "1"),
        ("v", "l", "n", "1\x00"),
        ("v", "l", "n", object()),
        ["v", "l", "n", None],
    ],
    ids=("scalar-string", "scalar-number", "short", "long", "missing-part", "nul", "object-part", "none-part"),
)
def test_vlnv_setter_rejects_invalid_values_before_mutation(bad_value: Any) -> None:
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name="n", version="1")
    external = _external_type_definitions(reference=reference)
    external_id = get_handle(external)
    before = (reference.vendor, reference.library, reference.name, reference.version)

    _assert_fault(
        TgiFaultCode.INVALID_ARGUMENT,
        api.setExternalTypeDefinitionsTypeDefinitionsRef,
        external_id,
        bad_value,
    )
    assert external.type_definitions_ref is reference
    assert (reference.vendor, reference.library, reference.name, reference.version) == before


def test_vlnv_setter_requires_typed_owner_and_current_reference_and_creates_missing_wrapper() -> None:
    _assert_fault(
        TgiFaultCode.INVALID_ID,
        api.setExternalTypeDefinitionsTypeDefinitionsRef,
        get_handle(object()),
        ("v", "l", "n", "1"),
    )
    external = _external_type_definitions()
    external_id = get_handle(external)
    original = external.type_definitions_ref
    external.type_definitions_ref = None
    assert api.setExternalTypeDefinitionsTypeDefinitionsRef(external_id, ("v", "l", "n", "1"))
    assert type(external.type_definitions_ref) is ConfigurableLibraryRefType
    assert (external.type_definitions_ref.vendor, external.type_definitions_ref.version) == ("v", "1")
    assert (original.vendor, original.library, original.name, original.version) == _VLNV

    malformed = object()
    external.type_definitions_ref = malformed
    _assert_fault(
        TgiFaultCode.INVALID_ID,
        api.setExternalTypeDefinitionsTypeDefinitionsRef,
        external_id,
        ("v", "l", "n", "1"),
    )
    assert external.type_definitions_ref is malformed


def test_vlnv_setter_round_trips_schema_valid_external_reference_without_target_lookup() -> None:
    external = _external_type_definitions()
    root = _root(external_type_definitions=(external,))
    assert api.setExternalTypeDefinitionsTypeDefinitionsRef(
        get_handle(external), ("other.example", "library", "unregistered_target", "3.2")
    )
    reparsed = _round_trip(root)
    reference = reparsed.external_type_definitions[0].type_definitions_ref
    assert (reference.vendor, reference.library, reference.name, reference.version) == (
        "other.example",
        "library",
        "unregistered_target",
        "3.2",
    )


def _member_root(case: _RootMember, names: tuple[str, ...] = ("target", "peer")) -> TypeDefinitions:
    members = tuple(case.member_type(name=name, description=Description(value=f"{name} description")) for name in names)
    return _root(
        external_type_definitions=(_external_type_definitions(),),
        **{case.holder_attribute: case.holder_type(**{case.member_attribute: members})},
    )


@pytest.mark.parametrize("case", _ROOT_MEMBERS, ids=lambda case: case.name)
def test_root_member_removers_use_registered_parsed_ownership_and_preserve_peers(case: _RootMember) -> None:
    parsed = _round_trip(_member_root(case))
    holder = getattr(parsed, case.holder_attribute)
    target, peer = getattr(holder, case.member_attribute)
    target_id = get_handle(target)
    peer_id = get_handle(peer)
    description_id = get_handle(target.description)
    root_id = get_handle(parsed)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))

    # The remover must recover ownership from the registered root before a collection getter runs.
    assert case.remover(target_id)
    assert resolve_handle(target_id) is None
    assert resolve_handle(description_id) is None
    assert resolve_handle(peer_id) is peer
    assert case.ids_getter(root_id) == [peer_id]
    assert isinstance(getattr(holder, case.member_attribute), list)
    assert parsed.external_type_definitions
    assert getattr(parsed, case.holder_attribute) is holder

    rendered = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(rendered.encode())), _SCHEMA.error_log
    reparsed = XmlDocument.parser().from_string(rendered, TypeDefinitions)
    assert XmlDocument.serializer().render(reparsed) == rendered


@pytest.mark.parametrize("case", _ROOT_MEMBERS, ids=lambda case: case.name)
def test_root_member_removers_prune_empty_holder_and_leave_other_collections(case: _RootMember) -> None:
    root = _member_root(case, ("only_member",))
    holder = getattr(root, case.holder_attribute)
    member = getattr(holder, case.member_attribute)[0]
    member_id = get_handle(member)
    root_id = get_handle(root)
    other = {
        "modes": TypeDefinitions.Modes(mode=(TypeDefinitions.Modes.Mode(name="keep_mode"),)),
        "reset_types": TypeDefinitions.ResetTypes(
            reset_type=(TypeDefinitions.ResetTypes.ResetType(name="keep_reset"),)
        ),
        "views": TypeDefinitions.Views(view=(TypeDefinitions.Views.View(name="keep_view"),)),
    }
    for key, value in other.items():
        if key != case.holder_attribute:
            setattr(root, key, value)
    external_ref = root.external_type_definitions[0].type_definitions_ref
    registry.register(root, (root.vendor, root.library, root.name, root.version))

    assert case.remover(member_id)
    assert getattr(root, case.holder_attribute) is None
    assert isinstance(getattr(holder, case.member_attribute), list)
    assert getattr(holder, case.member_attribute) == []
    assert case.ids_getter(root_id) == []
    for key, value in other.items():
        if key != case.holder_attribute:
            assert getattr(root, key) is value
    assert root.external_type_definitions[0].type_definitions_ref is external_ref
    assert resolve_handle(member_id) is None


@pytest.mark.parametrize("case", _ROOT_MEMBERS, ids=lambda case: case.name)
def test_root_member_removers_reject_wrong_stale_or_orphan_handles_atomically(case: _RootMember) -> None:
    root = _member_root(case, ("member",))
    holder = getattr(root, case.holder_attribute)
    member = getattr(holder, case.member_attribute)[0]
    member_id = get_handle(member)
    orphan = case.member_type(name="orphan")
    wrong = (
        TypeDefinitions.Views.View(name="wrong")
        if case.member_type is not TypeDefinitions.Views.View
        else TypeDefinitions.Modes.Mode(name="wrong")
    )
    before = XmlDocument.serializer().render(root)

    _assert_fault(TgiFaultCode.INVALID_ID, case.remover, "missing-id")
    _assert_fault(TgiFaultCode.INVALID_ID, case.remover, get_handle(object()))
    _assert_fault(TgiFaultCode.INVALID_ID, case.remover, get_handle(wrong))
    _assert_fault(TgiFaultCode.INVALID_ID, case.remover, get_handle(orphan))
    assert XmlDocument.serializer().render(root) == before

    setattr(holder, case.member_attribute, ())
    empty_before = XmlDocument.serializer().render(root)
    _assert_fault(TgiFaultCode.INVALID_ID, case.remover, member_id)
    assert XmlDocument.serializer().render(root) == empty_before


@pytest.mark.parametrize("case", _ROOT_MEMBERS, ids=lambda case: case.name)
def test_root_member_removers_reject_stale_foreign_root_ownership(case: _RootMember) -> None:
    first = _member_root(case, ("first",))
    second = _member_root(case, ("second",))
    first_holder = getattr(first, case.holder_attribute)
    second_holder = getattr(second, case.holder_attribute)
    member = getattr(first_holder, case.member_attribute)[0]
    member_id = get_handle(member)
    registry.register(first, ("acme", "types", "first_root", "1.0"))
    registry.register(second, ("acme", "types", "second_root", "1.0"))
    # Seed stale parent metadata, then make the child appear only under a foreign root.
    case.ids_getter(get_handle(first))
    setattr(first_holder, case.member_attribute, ())
    setattr(second_holder, case.member_attribute, (member,))
    before_first = XmlDocument.serializer().render(first)
    before_second = XmlDocument.serializer().render(second)

    _assert_fault(TgiFaultCode.INVALID_ID, case.remover, member_id)
    assert XmlDocument.serializer().render(first) == before_first
    assert XmlDocument.serializer().render(second) == before_second


def test_removed_local_view_target_is_no_longer_resolvable_by_view_link() -> None:
    local_view = TypeDefinitions.Views.View(name="rtl")
    link = _view_link("external_rtl", "rtl")
    root = _root(
        external_type_definitions=(_external_type_definitions(view_links=ViewLinks(view_link=(link,))),),
        views=TypeDefinitions.Views(view=(local_view,)),
    )
    loaded = _round_trip(root)
    registry.register(loaded, (loaded.vendor, loaded.library, loaded.name, loaded.version))
    loaded_view = loaded.views.view[0]
    loaded_link = loaded.external_type_definitions[0].view_links.view_link[0]
    view_id = get_handle(loaded_view)
    link_id = get_handle(loaded_link)

    assert api.removeTypeDefinitionsView(view_id)
    _assert_fault(TgiFaultCode.NOT_FOUND, api.getViewLinkViewReferenceRefByID, link_id)
