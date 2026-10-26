"""Typed name and reference-handle getters for mode and reset-type links."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import partial
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
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    ModeLinks,
    ResetTypeLinks,
    TypeDefinitions,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@dataclass(frozen=True)
class _ReferenceCase:
    label: str
    owner_type: type[Any]
    reference_type: type[Any]
    foreign_reference_type: type[Any]
    reference_attribute: str
    raw_attribute: str
    xml_name: str
    id_getter: Callable[[str], str]
    name_getter: Callable[[str], str]
    section: str


_CASES = (
    _ReferenceCase(
        "external mode",
        ModeLinks.ModeLink,
        ModeLinks.ModeLink.ExternalModeReference,
        ModeLinks.ModeLink.ModeReference,
        "external_mode_reference",
        "mode_ref",
        "modeRef",
        api.getModeLinkExternalModeReferenceID,
        api.getModeLinkExternalModeReferenceRefByName,
        "F.7.81.19",
    ),
    _ReferenceCase(
        "mode",
        ModeLinks.ModeLink,
        ModeLinks.ModeLink.ModeReference,
        ModeLinks.ModeLink.ExternalModeReference,
        "mode_reference",
        "mode_ref",
        "modeRef",
        api.getModeLinkModeReferenceID,
        api.getModeLinkModeReferenceRefByName,
        "F.7.81.21",
    ),
    _ReferenceCase(
        "external reset type",
        ResetTypeLinks.ResetTypeLink,
        ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference,
        ResetTypeLinks.ResetTypeLink.ResetTypeReference,
        "external_reset_type_reference",
        "reset_type_ref",
        "resetTypeRef",
        api.getResetTypeLinkExternalResetTypeReferenceID,
        api.getResetTypeLinkExternalResetTypeRefByName,
        "F.7.81.26",
    ),
    _ReferenceCase(
        "reset type",
        ResetTypeLinks.ResetTypeLink,
        ResetTypeLinks.ResetTypeLink.ResetTypeReference,
        ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference,
        "reset_type_reference",
        "reset_type_ref",
        "resetTypeRef",
        api.getResetTypeLinkResetTypeReferenceID,
        api.getResetTypeLinkResetTypeReferenceRefByName,
        "F.7.81.28",
    ),
)


def _mode_link(value: str = "mode_name") -> ModeLinks.ModeLink:
    return ModeLinks.ModeLink(
        external_mode_reference=ModeLinks.ModeLink.ExternalModeReference(mode_ref=f"external_{value}"),
        mode_reference=ModeLinks.ModeLink.ModeReference(mode_ref=value),
    )


def _reset_type_link(value: str = "reset_name") -> ResetTypeLinks.ResetTypeLink:
    return ResetTypeLinks.ResetTypeLink(
        external_reset_type_reference=ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference(
            reset_type_ref=f"external_{value}"
        ),
        reset_type_reference=ResetTypeLinks.ResetTypeLink.ResetTypeReference(reset_type_ref=value),
    )


def _owner(case: _ReferenceCase, value: str = "mode_or_reset") -> tuple[Any, Any]:
    link = _mode_link(value) if case.owner_type is ModeLinks.ModeLink else _reset_type_link(value)
    return link, getattr(link, case.reference_attribute)


def _root(*links: Any) -> TypeDefinitions:
    mode_links = [link for link in links if isinstance(link, ModeLinks.ModeLink)]
    reset_links = [link for link in links if isinstance(link, ResetTypeLinks.ResetTypeLink)]
    external = ExternalTypeDefinitions(
        name="shared_types",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor="example.org", library="types", name="shared_types", version="1.0"
        ),
        mode_links=ModeLinks(mode_link=mode_links) if mode_links else None,
        reset_type_links=ResetTypeLinks(reset_type_link=reset_links) if reset_links else None,
    )
    return TypeDefinitions(
        vendor="example.org",
        library="types",
        name="device_types",
        version="1.0",
        external_type_definitions=(external,),
        modes=TypeDefinitions.Modes(mode=[TypeDefinitions.Modes.Mode(name="active")]),
        reset_types=TypeDefinitions.ResetTypes(reset_type=[TypeDefinitions.ResetTypes.ResetType(name="cold")]),
    )


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _assert_invalid_id(action: Callable[[], object]) -> None:
    with pytest.raises(TgiError) as error:
        action()
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_reference_getters_have_native_signatures_exports_and_annex_sections() -> None:
    expected = {
        "getModeLinkExternalModeReferenceRefByName": ("modeLinkID", "F.7.81.19"),
        "getModeLinkExternalModeReferenceID": ("modeLinkID", "F.7.81.20"),
        "getModeLinkModeReferenceRefByName": ("modeLinkID", "F.7.81.21"),
        "getModeLinkModeReferenceID": ("modeLinkID", "F.7.81.22"),
        "getResetTypeLinkExternalResetTypeRefByName": ("resetTypeLinkID", "F.7.81.26"),
        "getResetTypeLinkExternalResetTypeReferenceID": ("resetTypeLinkID", "F.7.81.27"),
        "getResetTypeLinkResetTypeReferenceRefByName": ("resetTypeLinkID", "F.7.81.28"),
        "getResetTypeLinkResetTypeReferenceID": ("resetTypeLinkID", "F.7.81.29"),
    }

    for name, (parameter_name, section) in expected.items():
        operation = getattr(api, name)
        assert getattr(root_api, name) is operation
        assert name in api.__all__
        assert name in root_api.__all__
        operation_signature = signature(operation)
        assert tuple(operation_signature.parameters) == (parameter_name,)
        parameter = operation_signature.parameters[parameter_name]
        assert parameter.annotation is str
        assert parameter.default is parameter.empty
        assert operation_signature.return_annotation is str
        docstring = getdoc(operation)
        assert docstring is not None and f"Section: {section}." in docstring
        assert "Args:" in docstring and "Returns:" in docstring


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.label)
def test_id_getters_return_required_typed_owned_reference(case: _ReferenceCase) -> None:
    link, reference = _owner(case)
    link_id = get_handle(link)

    reference_id = case.id_getter(link_id)

    assert reference_id == get_handle(reference)
    assert type(resolve_handle(reference_id)) is case.reference_type
    parent = get_parent_info(reference_id)
    assert parent is not None
    assert parent.parent_handle == link_id
    assert parent.path == (case.reference_attribute,)
    assert parent.container == "single"


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.label)
def test_id_getters_reject_wrong_stale_and_other_owner_ids(case: _ReferenceCase) -> None:
    link, reference = _owner(case)
    wrong_owner = _reset_type_link() if case.owner_type is ModeLinks.ModeLink else _mode_link()

    for invalid_owner_id in ("stale-handle", get_handle(object()), get_handle(wrong_owner), get_handle(reference)):
        _assert_invalid_id(partial(case.id_getter, invalid_owner_id))
        _assert_invalid_id(partial(case.name_getter, invalid_owner_id))


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.label)
def test_id_getters_reject_absent_and_foreign_reference_models(case: _ReferenceCase) -> None:
    link, _reference = _owner(case)
    link_id = get_handle(link)
    setattr(link, case.reference_attribute, None)
    _assert_invalid_id(lambda: case.id_getter(link_id))
    _assert_invalid_id(lambda: case.name_getter(link_id))

    link, _reference = _owner(case)
    setattr(link, case.reference_attribute, case.foreign_reference_type(**{case.raw_attribute: "foreign"}))
    link_id = get_handle(link)
    _assert_invalid_id(lambda: case.id_getter(link_id))
    _assert_invalid_id(lambda: case.name_getter(link_id))


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.label)
def test_name_getters_use_id_getter_and_shared_reader(case: _ReferenceCase, monkeypatch: pytest.MonkeyPatch) -> None:
    link, reference = _owner(case, "δ_mode_or_reset")
    link_id = get_handle(link)
    reference_id = case.id_getter(link_id)
    original_id_getter = case.id_getter
    original_reader = api._reference_name
    observed_ids: list[str] = []
    observed_reads: list[tuple[str, str]] = []

    def id_getter(owner_id: str) -> str:
        observed_ids.append(owner_id)
        return original_id_getter(owner_id)

    def reader(child_id: str, xml_name: str) -> str:
        observed_reads.append((child_id, xml_name))
        return original_reader(child_id, xml_name)

    monkeypatch.setattr(api, case.id_getter.__name__, id_getter)
    monkeypatch.setattr(api, "_reference_name", reader)

    assert case.name_getter(link_id) == original_reader(reference_id, case.xml_name)
    assert observed_ids == [link_id]
    assert observed_reads == [(reference_id, case.xml_name)]
    assert getattr(reference, case.raw_attribute) == original_reader(reference_id, case.xml_name)


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.label)
@pytest.mark.parametrize("source", [None, 7, "", "bad name", "1starts_with_digit"])
def test_name_getters_reject_invalid_sources_but_keep_typed_child_repairable(
    case: _ReferenceCase, source: object
) -> None:
    link, reference = _owner(case)
    link_id = get_handle(link)
    setattr(reference, case.raw_attribute, source)

    reference_id = case.id_getter(link_id)
    assert resolve_handle(reference_id) is reference
    assert get_parent_info(reference_id).parent_handle == link_id
    _assert_invalid_id(lambda: case.name_getter(link_id))
    assert getattr(reference, case.raw_attribute) == source

    setattr(reference, case.raw_attribute, "repaired_name")
    assert case.id_getter(link_id) == reference_id
    assert case.name_getter(link_id) == "repaired_name"


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.label)
def test_name_getters_normalize_xml_name_whitespace_without_mutation(case: _ReferenceCase) -> None:
    link, reference = _owner(case)
    link_id = get_handle(link)
    reference_id = case.id_getter(link_id)
    padded_name = " \tδ_mode_or_reset\r\n"
    setattr(reference, case.raw_attribute, padded_name)

    assert case.name_getter(link_id) == "δ_mode_or_reset"
    assert case.id_getter(link_id) == reference_id
    assert getattr(reference, case.raw_attribute) == padded_name


def test_parsed_mode_and_reset_type_links_round_trip_with_nested_reference_ownership() -> None:
    root = _root(_mode_link("active"), _reset_type_link("cold"))
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert XmlDocument.serializer().render(parsed) == xml

    external = parsed.external_type_definitions[0]
    assert external.mode_links is not None
    assert external.reset_type_links is not None
    for case in _CASES[:2]:
        holder = external.mode_links
        assert holder is not None
        collection_attribute = "mode_link"
        links = getattr(holder, collection_attribute)
        assert len(links) == 1
        link = links[0]
        reference = getattr(link, case.reference_attribute)
        link_id = get_handle(link)
        reference_id = case.id_getter(link_id)
        parent = get_parent_info(reference_id)
        assert parent is not None
        assert parent.parent_handle == link_id
        assert type(resolve_handle(reference_id)) is case.reference_type
        assert case.name_getter(link_id) == getattr(reference, case.raw_attribute)

    for case in _CASES[2:]:
        holder = external.reset_type_links
        assert holder is not None
        collection_attribute = "reset_type_link"
        links = getattr(holder, collection_attribute)
        assert len(links) == 1
        link = links[0]
        reference = getattr(link, case.reference_attribute)
        link_id = get_handle(link)
        reference_id = case.id_getter(link_id)
        parent = get_parent_info(reference_id)
        assert parent is not None
        assert parent.parent_handle == link_id
        assert type(resolve_handle(reference_id)) is case.reference_type
        assert case.name_getter(link_id) == getattr(reference, case.raw_attribute)
