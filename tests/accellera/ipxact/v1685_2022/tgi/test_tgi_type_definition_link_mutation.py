"""Mutation contracts for the mode, reset-type, and view link TGI operations."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from inspect import getdoc, signature
from types import SimpleNamespace
from typing import Any

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    ModeLinks,
    ResetTypeLinks,
    TypeDefinitions,
    ViewLinks,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@dataclass(frozen=True)
class _SetterCase:
    name: str
    section: str
    owner_parameter: str
    value_parameter: str
    owner_type: type[Any]
    wrapper_attribute: str
    source_attribute: str
    reference_type: type[Any]
    setter: Callable[[str, str], bool]
    factory: Callable[[str], Any]
    external: bool


def _mode_link(value: str = "mode_name") -> ModeLinks.ModeLink:
    return ModeLinks.ModeLink(
        external_mode_reference=ModeLinks.ModeLink.ExternalModeReference(mode_ref=f"external_{value}"),
        mode_reference=ModeLinks.ModeLink.ModeReference(mode_ref=value),
    )


def _reset_link(value: str = "reset_name") -> ResetTypeLinks.ResetTypeLink:
    return ResetTypeLinks.ResetTypeLink(
        external_reset_type_reference=ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference(
            reset_type_ref=f"external_{value}"
        ),
        reset_type_reference=ResetTypeLinks.ResetTypeLink.ResetTypeReference(reset_type_ref=value),
    )


def _view_link(value: str = "view_name") -> ViewLinks.ViewLink:
    return ViewLinks.ViewLink(
        external_view_reference=ViewLinks.ViewLink.ExternalViewReference(view_ref=f"external_{value}"),
        view_reference=ViewLinks.ViewLink.ViewReference(view_ref=value),
    )


_SETTERS = (
    _SetterCase(
        "setModeLinkExternalModeReference",
        "F.7.82.51",
        "modeLinkID",
        "modeRef",
        ModeLinks.ModeLink,
        "external_mode_reference",
        "mode_ref",
        ModeLinks.ModeLink.ExternalModeReference,
        api.setModeLinkExternalModeReference,
        _mode_link,
        True,
    ),
    _SetterCase(
        "setModeLinkModeReference",
        "F.7.82.52",
        "modeLinkID",
        "modeRef",
        ModeLinks.ModeLink,
        "mode_reference",
        "mode_ref",
        ModeLinks.ModeLink.ModeReference,
        api.setModeLinkModeReference,
        _mode_link,
        False,
    ),
    _SetterCase(
        "setResetTypeLinkExternalResetTypeReference",
        "F.7.82.54",
        "resetTypeLinkID",
        "resetTypeRef",
        ResetTypeLinks.ResetTypeLink,
        "external_reset_type_reference",
        "reset_type_ref",
        ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference,
        api.setResetTypeLinkExternalResetTypeReference,
        _reset_link,
        True,
    ),
    _SetterCase(
        "setResetTypeLinkResetTypeReference",
        "F.7.82.55",
        "resetTypeLinkID",
        "resetTypeRef",
        ResetTypeLinks.ResetTypeLink,
        "reset_type_reference",
        "reset_type_ref",
        ResetTypeLinks.ResetTypeLink.ResetTypeReference,
        api.setResetTypeLinkResetTypeReference,
        _reset_link,
        False,
    ),
)


@dataclass(frozen=True)
class _RemovalCase:
    name: str
    section: str
    parameter: str
    owner_type: type[Any]
    holder_attribute: str
    member_attribute: str
    getter: Callable[[str], list[str]]
    remover: Callable[[str], bool]
    factory: Callable[[str], Any]


_REMOVERS = (
    _RemovalCase(
        "removeExternalTypeDefinitionsModeLink",
        "F.7.82.25",
        "modeLinkID",
        ModeLinks.ModeLink,
        "mode_links",
        "mode_link",
        api.getExternalTypeDefinitionsModeLinksIDs,
        api.removeExternalTypeDefinitionsModeLink,
        _mode_link,
    ),
    _RemovalCase(
        "removeExternalTypeDefinitionsResetTypeLink",
        "F.7.82.26",
        "resetTypeLinkID",
        ResetTypeLinks.ResetTypeLink,
        "reset_type_links",
        "reset_type_link",
        api.getExternalTypeDefinitionsResetTypeLinkIDs,
        api.removeExternalTypeDefinitionsResetTypeLink,
        _reset_link,
    ),
    _RemovalCase(
        "removeExternalTypeDefinitionsViewLink",
        "F.7.82.27",
        "viewLinkID",
        ViewLinks.ViewLink,
        "view_links",
        "view_link",
        api.getExternalTypeDefinitionsViewLinkIDs,
        api.removeExternalTypeDefinitionsViewLink,
        _view_link,
    ),
)


def _external(**holders: Any) -> ExternalTypeDefinitions:
    return ExternalTypeDefinitions(
        name="external_types",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor="example.org", library="types", name="shared_types", version="1.0"
        ),
        **holders,
    )


def _root(external: ExternalTypeDefinitions) -> TypeDefinitions:
    return TypeDefinitions(
        vendor="example.org",
        library="types",
        name="device_types",
        version="1.0",
        external_type_definitions=(external,),
    )


def _external_reference_attribute(case: _RemovalCase) -> str:
    return {
        ModeLinks.ModeLink: "external_mode_reference",
        ResetTypeLinks.ResetTypeLink: "external_reset_type_reference",
        ViewLinks.ViewLink: "external_view_reference",
    }[case.owner_type]


def _reference_source_attribute(case: _RemovalCase) -> str:
    return {
        ModeLinks.ModeLink: "mode_ref",
        ResetTypeLinks.ResetTypeLink: "reset_type_ref",
        ViewLinks.ViewLink: "view_ref",
    }[case.owner_type]


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _assert_fault(action: Callable[[], object], code: str) -> None:
    with pytest.raises(TgiError) as error:
        action()
    assert error.value.fault_code == code


def test_mutation_operations_expose_native_signatures_annex_sections_and_exports() -> None:
    for case in _SETTERS:
        operation = getattr(api, case.name)
        assert getattr(root_api, case.name) is operation
        assert case.name in api.__all__ and case.name in root_api.__all__
        operation_signature = signature(operation)
        assert tuple(operation_signature.parameters) == (case.owner_parameter, case.value_parameter)
        assert tuple(parameter.annotation for parameter in operation_signature.parameters.values()) == (str, str)
        assert all(parameter.default is parameter.empty for parameter in operation_signature.parameters.values())
        assert operation_signature.return_annotation is bool
        docstring = getdoc(operation)
        assert docstring is not None and f"Section: {case.section}." in docstring
        assert "Args:" in docstring and "Returns:" in docstring

    for case in _REMOVERS:
        operation = getattr(api, case.name)
        assert getattr(root_api, case.name) is operation
        assert case.name in api.__all__ and case.name in root_api.__all__
        operation_signature = signature(operation)
        assert tuple(operation_signature.parameters) == (case.parameter,)
        parameter = operation_signature.parameters[case.parameter]
        assert parameter.annotation is str and parameter.default is parameter.empty
        assert operation_signature.return_annotation is bool
        docstring = getdoc(operation)
        assert docstring is not None and f"Section: {case.section}." in docstring
        assert "Args:" in docstring and "Returns:" in docstring


@pytest.mark.parametrize("case", _SETTERS, ids=lambda case: case.name)
def test_setters_mutate_typed_wrappers_in_place_and_accept_xml_names_without_lookup(case: _SetterCase) -> None:
    link = case.factory("old_name")
    link.id = "link_id"
    wrapper = getattr(link, case.wrapper_attribute)
    link_id = get_handle(link)

    assert case.setter(link_id, "prefix:δ_mode")

    assert type(link) is case.owner_type
    assert link.id == "link_id"
    assert getattr(link, case.wrapper_attribute) is wrapper
    assert type(wrapper) is case.reference_type
    assert getattr(wrapper, case.source_attribute) == "prefix:δ_mode"
    # A link may point to a name that is absent from this document or from any registered target.
    assert case.setter(link_id, "missing_target")
    assert getattr(link, case.wrapper_attribute) is wrapper
    assert getattr(wrapper, case.source_attribute) == "missing_target"


@pytest.mark.parametrize("case", _SETTERS, ids=lambda case: case.name)
def test_setters_create_missing_generated_wrappers_and_repair_bad_raw_sources(case: _SetterCase) -> None:
    link = case.factory("old_name")
    link_id = get_handle(link)
    setattr(link, case.wrapper_attribute, None)
    assert case.setter(link_id, "created_name")
    created = getattr(link, case.wrapper_attribute)
    assert type(created) is case.reference_type
    assert getattr(created, case.source_attribute) == "created_name"

    setattr(created, case.source_attribute, object())
    assert case.setter(link_id, "repaired_name")
    assert getattr(link, case.wrapper_attribute) is created
    assert getattr(created, case.source_attribute) == "repaired_name"


@pytest.mark.parametrize("case", _SETTERS, ids=lambda case: case.name)
def test_setters_reject_foreign_owners_and_invalid_names_atomically(case: _SetterCase) -> None:
    link = case.factory("stable_name")
    link_id = get_handle(link)
    wrapper = getattr(link, case.wrapper_attribute)
    initial_source = getattr(wrapper, case.source_attribute)
    wrong_link = _reset_link() if case.owner_type is ModeLinks.ModeLink else _mode_link()
    _assert_fault(lambda: case.setter(get_handle(wrong_link), "valid_name"), TgiFaultCode.INVALID_ID)

    foreign_reference_type = {
        (ModeLinks.ModeLink, "external_mode_reference"): ModeLinks.ModeLink.ModeReference,
        (ModeLinks.ModeLink, "mode_reference"): ModeLinks.ModeLink.ExternalModeReference,
        (
            ResetTypeLinks.ResetTypeLink,
            "external_reset_type_reference",
        ): ResetTypeLinks.ResetTypeLink.ResetTypeReference,
        (
            ResetTypeLinks.ResetTypeLink,
            "reset_type_reference",
        ): ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference,
    }[(case.owner_type, case.wrapper_attribute)]
    foreign_wrapper = foreign_reference_type(**{case.source_attribute: "foreign_name"})
    setattr(link, case.wrapper_attribute, foreign_wrapper)
    _assert_fault(lambda: case.setter(link_id, "valid_name"), TgiFaultCode.INVALID_ID)
    assert getattr(link, case.wrapper_attribute) is foreign_wrapper
    setattr(link, case.wrapper_attribute, wrapper)

    for invalid_name in (None, 7, "", "two words", "1starts_with_digit", "expr + 1", "bad\x00name"):
        _assert_fault(
            lambda invalid_name=invalid_name: case.setter(link_id, invalid_name), TgiFaultCode.INVALID_ARGUMENT
        )
        assert getattr(link, case.wrapper_attribute) is wrapper
        assert getattr(wrapper, case.source_attribute) == initial_source


@pytest.mark.parametrize("case", [case for case in _SETTERS if not case.external], ids=lambda case: case.name)
def test_internal_setters_enforce_unique_typed_holder_siblings(case: _SetterCase) -> None:
    first = case.factory("shared")
    second = case.factory("other")
    setattr(getattr(first, case.wrapper_attribute), case.source_attribute, "shared")
    if case.owner_type is ModeLinks.ModeLink:
        holder: Any = ModeLinks(mode_link=(first, second))
        external = _external(mode_links=holder)
    else:
        holder = ResetTypeLinks(reset_type_link=(first, second))
        external = _external(reset_type_links=holder)
    root = _root(external)
    (
        api.getExternalTypeDefinitionsModeLinksIDs
        if case.owner_type is ModeLinks.ModeLink
        else api.getExternalTypeDefinitionsResetTypeLinkIDs
    )(get_handle(external))
    second_id = get_handle(second)

    assert case.setter(second_id, "unique_target")
    assert getattr(getattr(second, case.wrapper_attribute), case.source_attribute) == "unique_target"
    _assert_fault(lambda: case.setter(second_id, "shared"), TgiFaultCode.ALREADY_EXISTS)
    assert getattr(getattr(second, case.wrapper_attribute), case.source_attribute) == "unique_target"
    assert first in getattr(holder, "mode_link" if case.owner_type is ModeLinks.ModeLink else "reset_type_link")
    assert root.external_type_definitions == (external,)


@pytest.mark.parametrize("case", [case for case in _SETTERS if not case.external], ids=lambda case: case.name)
def test_internal_setters_allow_standalone_links_without_known_holder(case: _SetterCase) -> None:
    link = case.factory("old_name")
    assert case.setter(get_handle(link), "new_name")
    assert getattr(getattr(link, case.wrapper_attribute), case.source_attribute) == "new_name"


@pytest.mark.parametrize("case", _REMOVERS, ids=lambda case: case.name)
def test_removers_delete_exact_owned_links_and_invalidate_their_subtrees(
    case: _RemovalCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = case.factory("target")
    peer = case.factory("peer")
    member_attribute = case.member_attribute
    holder = (
        ModeLinks(mode_link=(target, peer))
        if case.owner_type is ModeLinks.ModeLink
        else ResetTypeLinks(reset_type_link=(target, peer))
        if case.owner_type is ResetTypeLinks.ResetTypeLink
        else ViewLinks(view_link=(target, peer))
    )
    external = _external(**{case.holder_attribute: holder})
    root = _root(external)
    case.getter(get_handle(external))
    target_id = get_handle(target)
    original_getter = case.getter
    observed_owner_ids: list[str] = []

    def observed_getter(owner_id: str) -> list[str]:
        observed_owner_ids.append(owner_id)
        return original_getter(owner_id)

    monkeypatch.setattr(api, case.getter.__name__, observed_getter)
    target_wrapper = getattr(target, _external_reference_attribute(case))
    wrapper_id = get_handle(target_wrapper)
    original_peers = getattr(holder, member_attribute)

    assert case.remover(target_id)
    assert observed_owner_ids == [get_handle(external)]
    assert getattr(holder, member_attribute) == [peer]
    assert case.getter(get_handle(external)) == [get_handle(peer)]
    assert resolve_handle(target_id) is None
    assert resolve_handle(wrapper_id) is None
    assert resolve_handle(get_handle(peer)) is peer
    assert root.external_type_definitions == (external,)

    assert case.remover(get_handle(peer))
    assert getattr(external, case.holder_attribute) is None
    assert case.getter(get_handle(external)) == []
    assert original_peers == (target, peer)


@pytest.mark.parametrize("case", _REMOVERS, ids=lambda case: case.name)
def test_removers_find_parsed_registered_owners_before_any_collection_getter(case: _RemovalCase) -> None:
    target = case.factory("parsed_target")
    peer = case.factory("parsed_peer")
    holder = (
        ModeLinks(mode_link=(target, peer))
        if case.owner_type is ModeLinks.ModeLink
        else ResetTypeLinks(reset_type_link=(target, peer))
        if case.owner_type is ResetTypeLinks.ResetTypeLink
        else ViewLinks(view_link=(target, peer))
    )
    parsed = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(_root(_external(**{case.holder_attribute: holder}))), TypeDefinitions
    )
    parsed_target = getattr(getattr(parsed.external_type_definitions[0], case.holder_attribute), case.member_attribute)[
        0
    ]
    parsed_peer = getattr(getattr(parsed.external_type_definitions[0], case.holder_attribute), case.member_attribute)[1]
    target_id = get_handle(parsed_target)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))

    # No collection getter has populated ownership handles before this operation.
    assert case.remover(target_id)
    assert case.getter(get_handle(parsed.external_type_definitions[0])) == [get_handle(parsed_peer)]
    assert resolve_handle(target_id) is None


@pytest.mark.parametrize("case", _REMOVERS, ids=lambda case: case.name)
def test_removers_reject_wrong_stale_or_orphan_handles_without_normalizing(case: _RemovalCase) -> None:
    target = case.factory("target")
    tuple_members = (target,)
    holder = (
        ModeLinks(mode_link=tuple_members)
        if case.owner_type is ModeLinks.ModeLink
        else ResetTypeLinks(reset_type_link=tuple_members)
        if case.owner_type is ResetTypeLinks.ResetTypeLink
        else ViewLinks(view_link=tuple_members)
    )
    external = _external(**{case.holder_attribute: holder})
    if case.owner_type is ModeLinks.ModeLink:
        wrong_link: Any = _reset_link("wrong")
    else:
        wrong_link = _mode_link("wrong")
    orphan = case.factory("orphan")
    _root(external)
    case.getter(get_handle(external))

    for invalid_id in ("stale-handle", get_handle(object()), get_handle(wrong_link), get_handle(orphan)):
        _assert_fault(lambda invalid_id=invalid_id: case.remover(invalid_id), TgiFaultCode.INVALID_ID)
        assert getattr(holder, case.member_attribute) is tuple_members

    # A correctly typed ID is still invalid if the holder no longer owns that exact object.
    setattr(holder, case.member_attribute, ())
    _assert_fault(lambda: case.remover(get_handle(target)), TgiFaultCode.INVALID_ID)
    assert getattr(holder, case.member_attribute) == ()


@pytest.mark.parametrize("case", _REMOVERS, ids=lambda case: case.name)
def test_removers_accept_malformed_link_sources_and_keep_other_holders(case: _RemovalCase) -> None:
    target = case.factory("target")
    setattr(getattr(target, _external_reference_attribute(case)), _reference_source_attribute(case), object())
    holder = (
        ModeLinks(mode_link=(target,))
        if case.owner_type is ModeLinks.ModeLink
        else ResetTypeLinks(reset_type_link=(target,))
        if case.owner_type is ResetTypeLinks.ResetTypeLink
        else ViewLinks(view_link=(target,))
    )
    other_holder = (
        ViewLinks(view_link=(_view_link("keep"),))
        if case.owner_type is not ViewLinks.ViewLink
        else ModeLinks(mode_link=(_mode_link("keep"),))
    )
    external = _external(
        **{
            case.holder_attribute: holder,
            "view_links" if case.holder_attribute != "view_links" else "mode_links": other_holder,
        }
    )
    _root(external)
    case.getter(get_handle(external))

    assert case.remover(get_handle(target))
    assert getattr(external, case.holder_attribute) is None
    assert other_holder is getattr(external, "view_links" if case.holder_attribute != "view_links" else "mode_links")


@pytest.mark.parametrize("case", _SETTERS, ids=lambda case: case.name)
def test_setter_result_serializes_to_schema_valid_ipxact(case: _SetterCase) -> None:
    link = case.factory("before")
    local_name = "local:mode_name" if case.owner_type is ModeLinks.ModeLink else "local:reset_type"
    root = _root(
        _external(
            **(
                {"mode_links": ModeLinks(mode_link=(link,))}
                if case.owner_type is ModeLinks.ModeLink
                else {"reset_type_links": ResetTypeLinks(reset_type_link=(link,))}
            )
        )
    )
    if case.owner_type is ModeLinks.ModeLink:
        root.modes = TypeDefinitions.Modes(
            mode=[TypeDefinitions.Modes.Mode(name="before"), TypeDefinitions.Modes.Mode(name=local_name)]
        )
    else:
        root.reset_types = TypeDefinitions.ResetTypes(
            reset_type=[
                TypeDefinitions.ResetTypes.ResetType(name="before"),
                TypeDefinitions.ResetTypes.ResetType(name=local_name),
            ]
        )
    assert case.setter(get_handle(link), "external:target" if case.external else local_name)
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    reparsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert XmlDocument.serializer().render(reparsed) == xml


def test_internal_setter_rejects_malformed_typed_sibling_atomically() -> None:
    first = _mode_link("first")
    second = _mode_link("second")
    holder = ModeLinks(mode_link=(first, second))
    external = _external(mode_links=holder)
    _root(external)
    api.getExternalTypeDefinitionsModeLinksIDs(get_handle(external))
    first.mode_reference = SimpleNamespace(mode_ref=object())  # type: ignore[assignment]
    second_id = get_handle(second)
    second_wrapper = second.mode_reference

    _assert_fault(lambda: api.setModeLinkModeReference(second_id, "usable"), TgiFaultCode.INVALID_ID)
    assert second.mode_reference is second_wrapper
    assert second_wrapper.mode_ref == "second"
