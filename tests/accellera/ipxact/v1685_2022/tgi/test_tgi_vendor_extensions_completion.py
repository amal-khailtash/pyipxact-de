"""Completion checks for IEEE 1685-2022 Vendor extensions TGI calls."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import (
    addVendorExtensions,
    getVendorExtensionElementAttributeNames,
    getVendorExtensionElementAttributeValue,
    getVendorExtensionElementNames,
    getVendorExtensionElementText,
    getVendorExtensions,
    getVendorExtensionsIDs,
    removeVendorExtensions,
    removeVendorExtensionsElement,
    setVendorExtensions,
)
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.catalog import Catalog
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions


def _catalog() -> Catalog:
    return Catalog(vendor="example.org", library="test", name="catalog", version="1.0")


def test_get_vendor_extensions_returns_the_generated_container_handle() -> None:
    catalog = _catalog()
    assert getVendorExtensions(get_handle(catalog)) is None

    catalog.vendor_extensions = VendorExtensions()
    parent_id = get_handle(catalog)
    container_id = getVendorExtensions(parent_id)

    assert container_id is not None
    assert resolve_handle(container_id) is catalog.vendor_extensions


def test_add_vendor_extensions_preserves_xml_content_order_and_serialization() -> None:
    catalog = _catalog()
    parent_id = get_handle(catalog)
    fragment = (
        '<vend:first xmlns:vend="urn:vendor" vend:code="A&amp;B">before'
        "<vend:child>inner &amp; text</vend:child>after</vend:first>"
        ' \n <second xmlns="urn:second" flag="yes">last</second>'
    )

    assert addVendorExtensions(parent_id, fragment) is True
    assert catalog.vendor_extensions is not None
    elements = list(catalog.vendor_extensions.any_element)
    assert [element.qname for element in elements] == ["{urn:vendor}first", "{urn:second}second"]
    assert elements[0].attributes == {"{urn:vendor}code": "A&B"}
    assert elements[0].text == "before"
    assert elements[0].children[0].qname == "{urn:vendor}child"
    assert elements[0].children[0].text == "inner & text"
    assert elements[0].children[0].tail == "after"
    assert elements[0].tail == " \n "
    assert elements[1].text == "last"

    serialized = XmlDocument.serializer().render(catalog)
    reparsed = XmlDocument.parser().from_string(serialized, Catalog)
    assert reparsed.vendor_extensions is not None
    reparsed_elements = list(reparsed.vendor_extensions.any_element)
    assert [element.qname for element in reparsed_elements] == ["{urn:vendor}first", "{urn:second}second"]
    assert reparsed_elements[0].attributes == {"{urn:vendor}code": "A&B"}
    assert reparsed_elements[0].children[0].tail == "after"


def test_vendor_extension_compatibility_getters_work_with_any_element() -> None:
    catalog = _catalog()
    parent_id = get_handle(catalog)
    addVendorExtensions(parent_id, '<one xmlns="urn:vendor" key="v">value</one><two />')

    assert getVendorExtensionElementNames(parent_id) == ["one", "two"]
    assert getVendorExtensionElementText(parent_id, "one") == ["value"]
    assert getVendorExtensionElementAttributeNames(parent_id, "one") == ["key"]
    assert getVendorExtensionElementAttributeValue(parent_id, "one", "key") == ["v"]
    extension_ids = getVendorExtensionsIDs(parent_id)
    assert len(extension_ids) == 2
    assert all(resolve_handle(handle) is not None for handle in extension_ids)


def test_invalid_fragment_is_atomic_for_add_and_set() -> None:
    catalog = _catalog()
    parent_id = get_handle(catalog)
    addVendorExtensions(parent_id, "<valid />")
    original_container = catalog.vendor_extensions
    original_elements = list(original_container.any_element)

    for operation in (addVendorExtensions, setVendorExtensions):
        with pytest.raises(TgiError) as error:
            operation(parent_id, "<valid /><broken>")
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert catalog.vendor_extensions is original_container
        assert list(catalog.vendor_extensions.any_element) == original_elements

    untouched = _catalog()
    with pytest.raises(TgiError) as error:
        addVendorExtensions(get_handle(untouched), "<broken>")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert untouched.vendor_extensions is None


def test_add_keeps_existing_handles_and_set_invalidates_replaced_subtrees() -> None:
    catalog = _catalog()
    parent_id = get_handle(catalog)
    addVendorExtensions(parent_id, "<old><nested /></old>")
    old_id = getVendorExtensionsIDs(parent_id)[0]
    old_nested_id = get_handle(resolve_handle(old_id).children[0])
    old_container_id = getVendorExtensions(parent_id)
    assert old_container_id is not None

    addVendorExtensions(parent_id, "<added />")
    assert resolve_handle(old_id) is not None
    assert [element.qname for element in catalog.vendor_extensions.any_element] == ["old", "added"]

    setVendorExtensions(parent_id, "<replacement><child /></replacement>")
    replacement_id = getVendorExtensionsIDs(parent_id)[0]
    assert resolve_handle(old_id) is None
    assert resolve_handle(old_nested_id) is None
    assert resolve_handle(old_container_id) is catalog.vendor_extensions
    assert resolve_handle(replacement_id) is catalog.vendor_extensions.any_element[0]
    replacement_nested_id = get_handle(catalog.vendor_extensions.any_element[0].children[0])

    assert removeVendorExtensions(parent_id) is True
    assert catalog.vendor_extensions is None
    assert resolve_handle(old_container_id) is None
    assert resolve_handle(replacement_id) is None
    assert resolve_handle(replacement_nested_id) is None


def test_remove_vendor_extensions_unknown_id_reports_invalid_id() -> None:
    with pytest.raises(TgiError) as error:
        removeVendorExtensions("unknown-vendor-extensions-handle")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_remove_duplicate_extension_by_handle_removes_the_selected_sibling() -> None:
    catalog = _catalog()
    parent_id = get_handle(catalog)
    addVendorExtensions(parent_id, "<duplicate /><duplicate />")
    first_id, second_id = getVendorExtensionsIDs(parent_id)

    assert resolve_handle(first_id) == resolve_handle(second_id)
    assert removeVendorExtensionsElement(second_id) is True
    assert catalog.vendor_extensions is not None
    assert len(catalog.vendor_extensions.any_element) == 1
    assert resolve_handle(first_id) is catalog.vendor_extensions.any_element[0]
    assert resolve_handle(second_id) is None
