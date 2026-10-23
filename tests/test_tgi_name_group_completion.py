"""Annex F Name group source text, mutation and generated XML contracts."""

import inspect
from types import SimpleNamespace

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import name_group as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, get_parent_info, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, Description, DisplayName, ShortDescription

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_FIELDS = [
    ("Description", "description", Description),
    ("DisplayName", "display_name", str),
    ("Name", "name", str),
    ("ShortDescription", "short_description", ShortDescription),
]


def _root():
    return Component(vendor="v", library="l", name="component", version="1")


def _valid(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, Component) == root
    return xml


@pytest.mark.parametrize("suffix,field,wrapper", _FIELDS)
def test_generated_text_get_set_remove_contracts(suffix, field, wrapper):
    root = _root()
    text = "original" if wrapper is str else wrapper(value="original")
    setattr(root, field, text)
    handle = get_handle(root)
    get = getattr(api, "get" + suffix)
    set_text = getattr(api, "set" + suffix)
    remove = getattr(api, "remove" + suffix)
    assert get(handle) == "original"
    child_id = None if wrapper is str else get_handle(text)
    replacement = "new_name" if suffix == "Name" else '$sformatf("Name %d", WIDTH)'
    assert set_text(handle, replacement)
    assert get(handle) == replacement
    if child_id:
        assert getattr(root, field) is text
        assert resolve_handle(child_id) is text
        assert get_parent_info(child_id) is not None
    _valid(root)
    assert remove(handle)
    assert get(handle) is None
    assert remove(handle) is False
    if child_id:
        assert resolve_handle(child_id) is None
        assert resolve_handle(handle) is root
    if suffix in ("Description", "DisplayName"):
        assert set_text(handle, "absent") is False
        assert getattr(root, field) is None
    else:
        assert set_text(handle, "restored")
        assert get(handle) == "restored"
        if wrapper is not str:
            assert isinstance(getattr(root, field), wrapper)
    if suffix != "Name" or root.name is not None:
        _valid(root)


@pytest.mark.parametrize("suffix,field,wrapper", _FIELDS)
def test_empty_text_is_present_and_invalid_set_is_atomic(suffix, field, wrapper):
    root = _root()
    setattr(root, field, "" if wrapper is str else wrapper(value=""))
    handle = get_handle(root)
    assert getattr(api, "get" + suffix)(handle) == ""
    for invalid in (None, 123, True, [], "bad\x00text", "bad\ud800text"):
        with pytest.raises(TgiError) as exc:
            getattr(api, "set" + suffix)(handle, invalid)
        assert exc.value.fault_code == "INVALID_ARGUMENT"
        assert getattr(api, "get" + suffix)(handle) == ""
    assert getattr(api, "remove" + suffix)(handle)


@pytest.mark.parametrize("operation", api.__all__)
def test_invalid_and_unsupported_handles_fault_without_mutation(operation):
    function = getattr(api, operation)
    unsupported = SimpleNamespace(other="untouched")
    for handle in ("missing", None, [], get_handle(unsupported)):
        args = (handle, "value") if operation.startswith("set") else (handle,)
        with pytest.raises(TgiError) as exc:
            function(*args)
        assert exc.value.fault_code == "INVALID_ID"
    assert vars(unsupported) == {"other": "untouched"}


def test_parsed_wrappers_survive_edit_and_removal():
    root = _root()
    root.description = Description(value="documented")
    root.display_name = "Shown"
    root.short_description = ShortDescription(value='{"A", PARAM}')
    parsed = XmlDocument.parser().from_string(_valid(root), Component)
    handle = get_handle(parsed)
    description_id = get_handle(parsed.description)
    assert api.setDescription(handle, "revised")
    assert resolve_handle(description_id) is parsed.description
    assert api.getShortDescription(handle) == '{"A", PARAM}'
    _valid(parsed)
    assert api.removeDescription(handle)
    assert resolve_handle(description_id) is None
    assert api.removeDisplayName(handle)
    assert api.removeShortDescription(handle)
    _valid(parsed)


def test_legacy_camel_case_fields_preserve_empty_content():
    obj = SimpleNamespace(displayName="", shortDescription=None)
    handle = get_handle(obj)
    assert api.getDisplayName(handle) == ""
    assert api.setDisplayName(handle, "shown")
    assert api.setShortDescription(handle, "source")
    assert vars(obj) == {"displayName": "shown", "shortDescription": "source"}
    assert api.removeDisplayName(handle)
    assert api.removeShortDescription(handle)


@pytest.mark.parametrize("operation", api.__all__)
def test_exact_signature_and_static_documentation(operation):
    function = getattr(api, operation)
    suffix = operation.removeprefix("set")
    second = {
        "Description": "description",
        "DisplayName": "displayName",
        "Name": "name",
        "ShortDescription": "shortDescription",
    }
    parameters = ["elementID", second[suffix]] if operation.startswith("set") else ["elementID"]
    assert list(inspect.signature(function).parameters) == parameters
    doc = inspect.getdoc(function)
    for parameter in parameters:
        assert f"{parameter}:" in doc
    assert "Returns:" in doc
    assert "Section: F.7." in doc


def test_name_groups_use_distinct_schema_lexical_types_atomically():
    from org.accellera.ipxact.v1685_2022 import ComponentInstantiationType, FileSet, ParameterType, Port, Value
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    targets = [
        (FileSet(name="files"), "\t new_name \r", "new_name"),
        (ComponentInstantiationType(name="rtl"), " 9.rtl ", "9.rtl"),
        (ModelType.Views.View(name="rtl"), " 9.rtl ", "9.rtl"),
        (Port(name="port"), "\n new:port \t", "new:port"),
        (ParameterType(name="parameter", value=Value(value="1")), " arbitrary name \t", " arbitrary name \t"),
    ]
    for obj, source, expected in targets:
        handle = get_handle(obj)
        assert api.setName(handle, source)
        assert api.getName(handle) == expected
        if isinstance(obj, ParameterType):
            continue
        for invalid in ("", "two names", "name/child"):
            with pytest.raises(TgiError):
                api.setName(handle, invalid)
            assert api.getName(handle) == expected
    with pytest.raises(TgiError):
        api.setName(get_handle(targets[0][0]), "9name")
    with pytest.raises(TgiError):
        api.setName(get_handle(targets[3][0]), "9port")


def test_nested_display_name_wrapper_is_preserved_in_schema_round_trip():
    from org.accellera.ipxact.v1685_2022 import FileSet, FileSets

    root = _root()
    child = FileSet(name="sources", display_name=DisplayName(value="Sources"))
    root.file_sets = FileSets(file_set=[child])
    handle = get_handle(child)
    wrapped_id = get_handle(child.display_name)
    assert api.setDisplayName(handle, "RTL Sources")
    assert resolve_handle(wrapped_id) is child.display_name
    assert api.getDisplayName(handle) == "RTL Sources"
    _valid(root)
    assert api.removeDisplayName(handle)
    assert resolve_handle(wrapped_id) is None
    _valid(root)


def test_registered_name_rename_preserves_vlnv_identity_and_rejects_conflicts():
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import registry

    registry.clear()
    try:
        root = _root()
        handle = get_handle(root)
        registry.register(root, ("v", "l", "component", "1"), "component.xml", element_type="Component")
        other = Component(vendor="v", library="l", name="occupied", version="1")
        registry.register(other, ("v", "l", "occupied", "1"))
        assert api.setName(handle, " 9renamed ")
        assert registry.get_vlnv(handle) == ("v", "l", "9renamed", "1")
        assert registry.get_id(("v", "l", "component", "1")) is None
        assert registry.get_id(("v", "l", "9renamed", "1")) == handle
        assert registry.get_file_name(handle) == "component.xml"
        assert registry.get_element_type(handle) == "Component"
        _valid(root)
        with pytest.raises(TgiError) as exc:
            api.setName(handle, "occupied")
        assert exc.value.fault_code == "ALREADY_EXISTS"
        assert root.name == "9renamed"
        assert registry.get_vlnv(handle) == ("v", "l", "9renamed", "1")
        assert api.removeName(handle) is False
        assert root.name == "9renamed"
        assert api.setName(handle, "9renamed")
        assert resolve_handle(handle) is root
    finally:
        registry.clear()


def test_optional_name_and_short_description_create_typed_schema_valid_children():
    from org.accellera.ipxact.v1685_2022 import ConstraintSet

    obj = ConstraintSet()
    handle = get_handle(obj)
    assert api.getName(handle) is None
    assert api.setName(handle, " optional_name ")
    assert api.setShortDescription(handle, '{"prefix", SYMBOL}')
    assert isinstance(obj.short_description, ShortDescription)
    assert api.getShortDescription(handle) == '{"prefix", SYMBOL}'
    xml = XmlDocument.serializer().render(obj)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, ConstraintSet) == obj
    assert api.removeName(handle)
    assert api.getName(handle) is None
    xml = XmlDocument.serializer().render(obj)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
