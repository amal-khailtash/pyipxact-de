"""Typed collection getters for modes, reset types, views, and their external links."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass, fields, is_dataclass
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
    ViewLinks,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))

type _Getter = Callable[[str], list[str]]
type _MemberFactory = Callable[[str], object]


@dataclass(frozen=True)
class _Collection:
    label: str
    getter: _Getter
    section: str
    root_type: type[Any]
    root_attribute: str
    holder_type: type[Any]
    member_attribute: str
    member_type: type[Any]
    member_factory: _MemberFactory


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _mode(name: str) -> TypeDefinitions.Modes.Mode:
    return TypeDefinitions.Modes.Mode(name=name)


def _reset_type(name: str) -> TypeDefinitions.ResetTypes.ResetType:
    return TypeDefinitions.ResetTypes.ResetType(name=name)


def _view(name: str) -> TypeDefinitions.Views.View:
    return TypeDefinitions.Views.View(name=name)


def _mode_link(name: str) -> ModeLinks.ModeLink:
    return ModeLinks.ModeLink(
        external_mode_reference=ModeLinks.ModeLink.ExternalModeReference(mode_ref=f"external_{name}"),
        mode_reference=ModeLinks.ModeLink.ModeReference(mode_ref=name),
    )


def _reset_type_link(name: str) -> ResetTypeLinks.ResetTypeLink:
    return ResetTypeLinks.ResetTypeLink(
        external_reset_type_reference=ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference(
            reset_type_ref=f"external_{name}"
        ),
        reset_type_reference=ResetTypeLinks.ResetTypeLink.ResetTypeReference(reset_type_ref=name),
    )


def _view_link(name: str) -> ViewLinks.ViewLink:
    return ViewLinks.ViewLink(
        external_view_reference=ViewLinks.ViewLink.ExternalViewReference(view_ref=f"external_{name}"),
        view_reference=ViewLinks.ViewLink.ViewReference(view_ref=name),
    )


def _cases() -> list[_Collection]:
    return [
        _Collection(
            "modes",
            api.getTypeDefinitionsModeIDs,
            "F.7.81.38",
            TypeDefinitions,
            "modes",
            TypeDefinitions.Modes,
            "mode",
            TypeDefinitions.Modes.Mode,
            _mode,
        ),
        _Collection(
            "reset types",
            api.getTypeDefinitionsResetTypeIDs,
            "F.7.81.41",
            TypeDefinitions,
            "reset_types",
            TypeDefinitions.ResetTypes,
            "reset_type",
            TypeDefinitions.ResetTypes.ResetType,
            _reset_type,
        ),
        _Collection(
            "views",
            api.getTypeDefinitionsViewIDs,
            "F.7.81.42",
            TypeDefinitions,
            "views",
            TypeDefinitions.Views,
            "view",
            TypeDefinitions.Views.View,
            _view,
        ),
        _Collection(
            "external mode links",
            api.getExternalTypeDefinitionsModeLinksIDs,
            "F.7.81.11",
            ExternalTypeDefinitions,
            "mode_links",
            ModeLinks,
            "mode_link",
            ModeLinks.ModeLink,
            _mode_link,
        ),
        _Collection(
            "external reset-type links",
            api.getExternalTypeDefinitionsResetTypeLinkIDs,
            "F.7.81.12",
            ExternalTypeDefinitions,
            "reset_type_links",
            ResetTypeLinks,
            "reset_type_link",
            ResetTypeLinks.ResetTypeLink,
            _reset_type_link,
        ),
        _Collection(
            "external view links",
            api.getExternalTypeDefinitionsViewLinkIDs,
            "F.7.81.15",
            ExternalTypeDefinitions,
            "view_links",
            ViewLinks,
            "view_link",
            ViewLinks.ViewLink,
            _view_link,
        ),
    ]


def _owner(case: _Collection, *, with_collection: bool = True) -> tuple[object, object, tuple[object, ...]]:
    members = tuple(case.member_factory(f"{case.label}_{index}") for index in range(2))
    holder = case.holder_type(**{case.member_attribute: members if with_collection else []})
    if case.root_type is TypeDefinitions:
        return _root(**{case.root_attribute: holder}), holder, members
    return _external(**{case.root_attribute: holder}), holder, members


def _root(**attributes: Any) -> TypeDefinitions:
    return TypeDefinitions(vendor="example.org", library="types", name="device_types", version="1.0", **attributes)


def _external(**attributes: Any) -> ExternalTypeDefinitions:
    return ExternalTypeDefinitions(
        name="external_types",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor="example.org", library="types", name="shared_types", version="1.0"
        ),
        **attributes,
    )


def _assert_descendant_ownership(root: object) -> None:
    pending = [root]
    seen: set[int] = set()
    while pending:
        parent = pending.pop()
        if id(parent) in seen or not is_dataclass(parent) or isinstance(parent, type):
            continue
        seen.add(id(parent))
        for model_field in fields(parent):
            value = getattr(parent, model_field.name)
            children = value if isinstance(value, (list, tuple)) else (value,)
            for child in children:
                if not is_dataclass(child) or isinstance(child, type):
                    continue
                info = get_parent_info(get_handle(child))
                assert info is not None
                assert info.parent_handle == get_handle(parent)
                assert info.path == (model_field.name,)
                assert info.container == ("list" if isinstance(value, (list, tuple)) else "single")
                pending.append(child)


def test_link_collection_getters_have_native_public_signatures() -> None:
    for case in _cases():
        operation = getattr(api, case.getter.__name__)
        assert getattr(root_api, case.getter.__name__) is operation, case.label
        assert case.getter.__name__ in api.__all__, case.label
        assert case.getter.__name__ in root_api.__all__, case.label
        operation_signature = signature(operation)
        assert tuple(operation_signature.parameters) == (
            "typeDefinitionsID" if case.root_type is TypeDefinitions else "externalTypeDefinitionsID",
        ), case.label
        assert tuple(parameter.annotation for parameter in operation_signature.parameters.values()) == (str,), (
            case.label
        )
        assert operation_signature.return_annotation == list[str], case.label
        assert all(parameter.default is parameter.empty for parameter in operation_signature.parameters.values()), (
            case.label
        )
        docstring = getdoc(operation)
        assert docstring is not None and f"Section: {case.section}." in docstring, case.label
        assert "Args:" in docstring and "Returns:" in docstring, case.label


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.label)
def test_link_collection_getters_preserve_order_identity_and_ownership(case: _Collection) -> None:
    owner, holder, members = _owner(case)
    stored_members = getattr(holder, case.member_attribute)
    assert isinstance(stored_members, tuple)
    assert stored_members is members

    ids = case.getter(get_handle(owner))
    assert ids == [get_handle(member) for member in members], case.label
    assert [resolve_handle(handle) for handle in ids] == list(members), case.label
    assert getattr(holder, case.member_attribute) is members, case.label

    for handle in ids:
        info = get_parent_info(handle)
        assert info is not None, case.label
        assert info.parent_handle == get_handle(holder), case.label
        assert info.path == (case.member_attribute,), case.label
        assert info.container == "list", case.label
        _assert_descendant_ownership(resolve_handle(handle))
    holder_info = get_parent_info(get_handle(holder))
    assert holder_info is not None, case.label
    assert holder_info.parent_handle == get_handle(owner), case.label
    assert holder_info.path == (case.root_attribute,), case.label
    assert holder_info.container == "single", case.label


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.label)
def test_link_collection_getters_return_empty_for_absent_optional_holders(case: _Collection) -> None:
    owner, _holder, _members = _owner(case, with_collection=False)
    setattr(owner, case.root_attribute, None)
    assert case.getter(get_handle(owner)) == []


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.label)
def test_link_collection_getters_reject_wrong_roots_holders_and_members(case: _Collection) -> None:
    wrong_root = _external() if case.root_type is TypeDefinitions else _root()
    for handle in ("stale-handle", get_handle(object()), get_handle(wrong_root)):
        with pytest.raises(TgiError) as error:
            case.getter(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID, case.label

    owner, holder, _members = _owner(case)
    setattr(owner, case.root_attribute, object())
    with pytest.raises(TgiError) as error:
        case.getter(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID, f"{case.label}: wrong holder"

    owner, holder, _members = _owner(case)
    collection_owner = holder
    attribute = case.member_attribute
    setattr(collection_owner, attribute, object())
    with pytest.raises(TgiError) as error:
        case.getter(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID, f"{case.label}: wrong collection"

    owner, holder, _members = _owner(case)
    collection_owner = holder
    attribute = case.member_attribute
    for invalid_members in ([object()], (object(),)):
        setattr(collection_owner, attribute, invalid_members)
        with pytest.raises(TgiError) as error:
            case.getter(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID, f"{case.label}: wrong member"


def test_parsed_type_definitions_external_links_roundtrip_with_nested_ownership() -> None:
    external = ExternalTypeDefinitions(
        name="external_types",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor="example.org", library="types", name="shared_types", version="1.0"
        ),
        mode_links=ModeLinks(mode_link=(_mode_link("active"),)),
        reset_type_links=ResetTypeLinks(reset_type_link=(_reset_type_link("cold"),)),
        view_links=ViewLinks(view_link=(_view_link("rtl"),)),
    )
    root = _root(
        external_type_definitions=(external,),
        modes=TypeDefinitions.Modes(mode=(_mode("active"),)),
        reset_types=TypeDefinitions.ResetTypes(reset_type=(_reset_type("cold"),)),
        views=TypeDefinitions.Views(view=(_view("rtl"),)),
    )
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    parsed_external = parsed.external_type_definitions[0]

    external_ids = api.getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(parsed))
    assert external_ids == [get_handle(parsed_external)]
    external_info = get_parent_info(external_ids[0])
    assert external_info is not None
    assert external_info.parent_handle == get_handle(parsed)
    assert external_info.path == ("external_type_definitions",)
    assert external_info.container == "list"

    for getter, holder, attribute in (
        (api.getExternalTypeDefinitionsModeLinksIDs, parsed_external.mode_links, "mode_link"),
        (
            api.getExternalTypeDefinitionsResetTypeLinkIDs,
            parsed_external.reset_type_links,
            "reset_type_link",
        ),
        (api.getExternalTypeDefinitionsViewLinkIDs, parsed_external.view_links, "view_link"),
    ):
        ids = getter(get_handle(parsed_external))
        members = getattr(holder, attribute)
        assert ids == [get_handle(member) for member in members]
        info = get_parent_info(ids[0])
        assert info is not None
        assert info.parent_handle == get_handle(holder)
        assert info.path == (attribute,)
        assert info.container == "list"
        _assert_descendant_ownership(resolve_handle(ids[0]))
