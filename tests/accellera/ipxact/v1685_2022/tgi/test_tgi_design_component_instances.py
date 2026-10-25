"""Design component instance TGI contracts from IEEE 1685-2022."""

import inspect
from collections.abc import Iterator
from pathlib import Path
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import design as api
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
    ComponentInstance,
    ComponentInstances,
    ConfigurableElementValue,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    Description,
    Design,
    DisplayName,
    InstanceName,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_API_FUNCTIONS = (
    "getComponentInstanceComponentRefByID",
    "getComponentInstanceComponentRefByVLNV",
    "getComponentInstanceName",
    "getDesignComponentInstanceIDs",
    "addDesignComponentInstance",
    "removeDesignComponentInstance",
    "setComponentInstanceComponentRef",
)
_VLNV = ("vendor", "library", "component", "1")


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _reference(
    vlnv: tuple[str, str, str, str] = _VLNV,
    *,
    configurable_element_values: ConfigurableElementValues | None = None,
    reference_id: str | None = None,
) -> ConfigurableLibraryRefType:
    return ConfigurableLibraryRefType(
        vendor=vlnv[0],
        library=vlnv[1],
        name=vlnv[2],
        version=vlnv[3],
        configurable_element_values=configurable_element_values,
        id=reference_id,
    )


def _instance(
    name: str = "u0",
    *,
    vlnv: tuple[str, str, str, str] = _VLNV,
    reference: ConfigurableLibraryRefType | None = None,
    description: str | None = None,
    display_name: str | None = None,
) -> ComponentInstance:
    return ComponentInstance(
        instance_name=InstanceName(value=name),
        component_ref=reference or _reference(vlnv),
        description=Description(value=description) if description is not None else None,
        display_name=DisplayName(value=display_name) if display_name is not None else None,
    )


def _design(*instances: ComponentInstance, name: str = "component_instances") -> Design:
    return Design(
        vendor="vendor",
        library="library",
        name=name,
        version="1",
        component_instances=ComponentInstances(component_instance=list(instances)) if instances else None,
    )


def _registered(*instances: ComponentInstance, name: str = "component_instances") -> Design:
    root = _design(*instances, name=name)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    return root


def _register_parsed(root: Design) -> Design:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Design)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    return parsed


def _round_trip(root: Design) -> str:
    xml = XmlDocument.serializer().render(root)
    parsed_xml = etree.fromstring(xml.encode())
    _SCHEMA.assertValid(parsed_xml)
    assert XmlDocument.serializer().render(XmlDocument.parser().from_string(xml, Design)) == xml
    return xml


def test_public_exports_and_annex_f_signatures() -> None:
    optional_vlnv = tuple[str | None, str | None, str | None, str | None]
    expected = {
        "getComponentInstanceComponentRefByID": ([str], str),
        "getComponentInstanceComponentRefByVLNV": ([str], optional_vlnv),
        "getComponentInstanceName": ([str], str | None),
        "getDesignComponentInstanceIDs": ([str], list[str]),
        "addDesignComponentInstance": ([str, tuple[str, str, str, str], str], str),
        "removeDesignComponentInstance": ([str], bool),
        "setComponentInstanceComponentRef": ([str, tuple[str, str, str, str]], bool),
    }
    sections = {
        "getComponentInstanceComponentRefByID": "F.7.37.8",
        "getComponentInstanceComponentRefByVLNV": "F.7.37.9",
        "getComponentInstanceName": "F.7.37.10",
        "getDesignComponentInstanceIDs": "F.7.37.14",
        "addDesignComponentInstance": "F.7.38.6",
        "removeDesignComponentInstance": "F.7.38.19",
        "setComponentInstanceComponentRef": "F.7.38.30",
    }

    assert set(_API_FUNCTIONS) == set(expected) == set(sections)
    for name in _API_FUNCTIONS:
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        hints = get_type_hints(function)
        assert [hints[parameter] for parameter in inspect.signature(function).parameters] == expected[name][0]
        assert hints["return"] == expected[name][1]
        assert all(
            not isinstance(parameter.annotation, str) for parameter in inspect.signature(function).parameters.values()
        )
        assert f"Section: {sections[name]}." in inspect.getdoc(function)


def test_design_component_instance_ids_register_immediate_ownership_and_preserve_tuple_storage() -> None:
    first = _instance("u0")
    second = _instance("u1")
    root = _registered(first, second)
    holder = root.component_instances
    children = tuple(holder.component_instance)
    holder.component_instance = children

    ids = api.getDesignComponentInstanceIDs(get_handle(root))

    assert ids == [get_handle(first), get_handle(second)]
    assert holder.component_instance is children
    for child_id in ids:
        info = get_parent_info(child_id)
        assert info is not None
        assert (info.parent_handle, info.path, info.container) == (
            get_handle(holder),
            ("component_instance",),
            "list",
        )
    assert get_parent_info(get_handle(holder)) is not None


@pytest.mark.parametrize(
    "malformation",
    ["missing-holder", "wrong-holder", "non-sequence", "wrong-child"],
    ids=("missing-holder", "wrong-holder", "non-sequence", "wrong-child"),
)
def test_design_component_instance_ids_handle_empty_and_reject_malformed_graph(malformation: str) -> None:
    root = _registered(_instance())
    if malformation == "missing-holder":
        root.component_instances = None
        assert api.getDesignComponentInstanceIDs(get_handle(root)) == []
        return
    if malformation == "wrong-holder":
        root.component_instances = object()  # type: ignore[assignment]
    elif malformation == "non-sequence":
        root.component_instances.component_instance = object()  # type: ignore[assignment]
    else:
        root.component_instances.component_instance = [Description(value="wrong child")]  # type: ignore[list-item]

    with pytest.raises(TgiError) as error:
        api.getDesignComponentInstanceIDs(get_handle(root))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_component_reference_getters_resolve_registered_component_and_report_vlnv() -> None:
    instance = _instance("u0", reference=_reference(reference_id="component_ref_id"))
    root = _registered(instance)
    target = Component(vendor="vendor", library="library", name="component", version="1")
    registry.register(target, _VLNV)

    component_id = api.getComponentInstanceComponentRefByID(get_handle(instance))

    assert component_id == get_handle(target)
    assert resolve_handle(component_id) is target
    assert api.getComponentInstanceComponentRefByVLNV(get_handle(instance)) == _VLNV
    assert api.getComponentInstanceName(get_handle(instance)) == "u0"
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "target_kind", ["absent", "unregistered", "wrong-kind"], ids=("absent", "unregistered", "wrong-kind")
)
def test_component_reference_by_id_requires_a_registered_component_target(target_kind: str) -> None:
    ref = _reference()
    root = _registered(_instance(reference=ref))
    if target_kind == "wrong-kind":
        target = Design(vendor="vendor", library="library", name="component", version="1")
        registry.register(target, _VLNV)
    elif target_kind == "unregistered":
        Component(vendor="vendor", library="library", name="component", version="1")

    with pytest.raises(TgiError) as error:
        api.getComponentInstanceComponentRefByID(get_handle(root.component_instances.component_instance[0]))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


def test_component_reference_by_id_rejects_invalid_owner_and_malformed_reference() -> None:
    instance = _instance()
    root = _registered(instance)
    with pytest.raises(TgiError) as stale:
        api.getComponentInstanceComponentRefByID("stale-component-instance")
    assert stale.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as wrong_type:
        api.getComponentInstanceComponentRefByID(get_handle(root))
    assert wrong_type.value.fault_code == TgiFaultCode.INVALID_ID

    instance.component_ref = object()  # type: ignore[assignment]
    with pytest.raises(TgiError) as malformed:
        api.getComponentInstanceComponentRefByID(get_handle(instance))
    assert malformed.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("malformation", ["wrong-wrapper", "wrong-field"], ids=("wrong-wrapper", "wrong-field"))
def test_component_reference_vlnv_getter_rejects_malformed_reference(malformation: str) -> None:
    instance = _instance()
    _registered(instance)
    if malformation == "wrong-wrapper":
        instance.component_ref = Description(value="wrong reference")  # type: ignore[assignment]
    else:
        instance.component_ref.version = 5  # type: ignore[assignment]

    with pytest.raises(TgiError) as error:
        api.getComponentInstanceComponentRefByVLNV(get_handle(instance))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_component_reference_vlnv_getter_returns_none_tuple_when_reference_is_absent() -> None:
    instance = _instance()
    _registered(instance)
    instance.component_ref = None  # type: ignore[assignment]

    assert api.getComponentInstanceComponentRefByVLNV(get_handle(instance)) == (None, None, None, None)


@pytest.mark.parametrize(
    "malformation",
    ["wrong-wrapper", "missing-value", "wrong-content"],
    ids=("wrong-wrapper", "missing-value", "wrong-content"),
)
def test_component_instance_name_getter_validates_wrapper_and_content(malformation: str) -> None:
    instance = _instance()
    _registered(instance)
    if malformation == "wrong-wrapper":
        instance.instance_name = Description(value="wrong wrapper")  # type: ignore[assignment]
    elif malformation == "missing-value":
        instance.instance_name = InstanceName(value=None)  # type: ignore[arg-type]
    else:
        instance.instance_name.value = 17  # type: ignore[assignment]

    with pytest.raises(TgiError) as error:
        api.getComponentInstanceName(get_handle(instance))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_component_instance_name_getter_returns_none_for_absent_instance_name() -> None:
    instance = _instance()
    _registered(instance)
    instance.instance_name = None  # type: ignore[assignment]

    assert api.getComponentInstanceName(get_handle(instance)) is None


def test_add_component_instance_collapses_name_keeps_order_and_does_not_resolve_target() -> None:
    first = _instance("u0", description="keep first")
    root = _registered(first)
    holder = root.component_instances
    holder.component_instance = tuple(holder.component_instance)

    new_id = api.addDesignComponentInstance(get_handle(root), ("missing", "library", "new_component", "2"), " \tu1\r\n")
    added = resolve_handle(new_id)

    assert isinstance(added, ComponentInstance)
    assert added.instance_name == InstanceName(value="u1")
    assert (
        added.component_ref.vendor,
        added.component_ref.library,
        added.component_ref.name,
        added.component_ref.version,
    ) == (
        "missing",
        "library",
        "new_component",
        "2",
    )
    assert isinstance(added.component_ref, ConfigurableLibraryRefType)
    assert isinstance(holder.component_instance, list)
    assert holder.component_instance == [first, added]
    assert holder.component_instance[0] is first
    assert first.description == Description(value="keep first")
    info = get_parent_info(new_id)
    assert info is not None
    assert (info.parent_handle, info.path, info.container) == (
        get_handle(holder),
        ("component_instance",),
        "list",
    )


@pytest.mark.parametrize(
    "name,vlnv",
    [
        ("bad name", _VLNV),
        ("1bad", _VLNV),
        ("u1", ("", "library", "component", "1")),
        ("u1", ("vendor", "", "component", "1")),
        ("u1", ("vendor", "library", "", "1")),
        ("u1", ("vendor", "library", "component", "")),
        ("u1", ("vendor\x01", "library", "component", "1")),
    ],
    ids=(
        "name-space",
        "name-start",
        "empty-vendor",
        "empty-library",
        "empty-name",
        "empty-version",
        "xml-illegal-vlnv",
    ),
)
def test_add_component_instance_rejects_invalid_input_before_creating_holder(
    name: str, vlnv: tuple[str, str, str, str]
) -> None:
    root = _registered()

    with pytest.raises(TgiError) as error:
        api.addDesignComponentInstance(get_handle(root), vlnv, name)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.component_instances is None


def test_add_component_instance_rejects_duplicate_normalized_and_malformed_existing_names_atomically() -> None:
    existing = _instance("u0")
    root = _registered(existing)
    before = root.component_instances.component_instance
    with pytest.raises(TgiError) as duplicate:
        api.addDesignComponentInstance(get_handle(root), _VLNV, " \tu0\n")
    assert duplicate.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.component_instances.component_instance is before
    assert tuple(before) == (existing,)

    existing.instance_name.value = ""
    with pytest.raises(TgiError) as malformed:
        api.addDesignComponentInstance(get_handle(root), _VLNV, "u1")
    assert malformed.value.fault_code == TgiFaultCode.INVALID_ID
    assert root.component_instances.component_instance is before


def test_add_component_instance_creates_missing_holder_and_round_trips_schema_valid_document() -> None:
    root = _registered()

    new_id = api.addDesignComponentInstance(get_handle(root), _VLNV, "u0")

    assert root.component_instances is not None
    assert root.component_instances.component_instance == [resolve_handle(new_id)]
    xml = _round_trip(root)
    parsed = XmlDocument.parser().from_string(xml, Design)
    assert parsed.component_instances.component_instance[0].instance_name.value == "u0"
    assert parsed.component_instances.component_instance[0].component_ref.vendor == "vendor"


def test_set_component_reference_preserves_wrapper_configurable_values_and_metadata() -> None:
    value = ConfigurableElementValue(reference_id="WIDTH", value="32", id="value_id")
    values = ConfigurableElementValues(configurable_element_value=[value])
    ref = _reference(configurable_element_values=values, reference_id="ref_id")
    instance = _instance("u0", reference=ref, description="keep description", display_name="keep display")
    root = _registered(instance)
    name_wrapper = instance.instance_name
    description = instance.description
    display_name = instance.display_name

    assert api.setComponentInstanceComponentRef(get_handle(instance), ("new_vendor", "new_library", "new_name", "2"))

    assert instance.component_ref is ref
    assert (ref.vendor, ref.library, ref.name, ref.version) == ("new_vendor", "new_library", "new_name", "2")
    assert ref.id == "ref_id"
    assert ref.configurable_element_values is values
    assert values.configurable_element_value[0] is value
    assert value.value == "32" and value.id == "value_id"
    assert instance.instance_name is name_wrapper
    assert instance.description is description and instance.display_name is display_name
    assert resolve_handle(get_handle(root)) is root


def test_set_component_reference_creates_missing_wrapper_and_registers_ownership() -> None:
    instance = _instance("u0")
    root = _registered(instance)
    instance.component_ref = None  # type: ignore[assignment]

    assert api.setComponentInstanceComponentRef(get_handle(instance), ("new_vendor", "new_library", "new_name", "2"))

    ref = instance.component_ref
    assert isinstance(ref, ConfigurableLibraryRefType)
    assert (ref.vendor, ref.library, ref.name, ref.version) == ("new_vendor", "new_library", "new_name", "2")
    info = get_parent_info(get_handle(ref))
    assert info is not None
    assert (info.parent_handle, info.path, info.container) == (get_handle(instance), ("component_ref",), "single")
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "vlnv",
    [
        ("", "library", "component", "1"),
        ("vendor", "", "component", "1"),
        ("vendor", "library", "", "1"),
        ("vendor", "library", "component", ""),
        ("vendor", "library", "component"),
        ("vendor", "library", "component", "1", "extra"),
        ("vendor", "library", "component", 1),
        ("vendor\x01", "library", "component", "1"),
    ],
    ids=(
        "empty-vendor",
        "empty-library",
        "empty-name",
        "empty-version",
        "short-tuple",
        "long-tuple",
        "non-string",
        "xml-illegal",
    ),
)
def test_set_component_reference_rejects_invalid_vlnv_atomically(vlnv: object) -> None:
    ref = _reference(reference_id="preserve_ref")
    instance = _instance("u0", reference=ref)
    _registered(instance)
    before = (ref.vendor, ref.library, ref.name, ref.version)

    with pytest.raises(TgiError) as error:
        api.setComponentInstanceComponentRef(get_handle(instance), vlnv)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert instance.component_ref is ref
    assert (ref.vendor, ref.library, ref.name, ref.version) == before


def test_component_instance_remover_finds_parsed_owner_without_getter_first_and_invalidates_subtree() -> None:
    removed_value = ConfigurableElementValue(reference_id="WIDTH", value="32")
    removed = _instance(
        "u0",
        reference=_reference(
            configurable_element_values=ConfigurableElementValues(configurable_element_value=[removed_value])
        ),
        description="removed description",
        display_name="removed display",
    )
    sibling = _instance("u1", vlnv=("other", "library", "component", "1"), description="keep sibling")
    root = _register_parsed(_design(removed, sibling, name="parsed_component_instances"))
    holder = root.component_instances
    parsed_removed, parsed_sibling = holder.component_instance
    removed_id = get_handle(parsed_removed)
    display_id = get_handle(parsed_removed.display_name)
    description_id = get_handle(parsed_removed.description)
    ref_id = get_handle(parsed_removed.component_ref)
    values_id = get_handle(parsed_removed.component_ref.configurable_element_values)
    value_id = get_handle(parsed_removed.component_ref.configurable_element_values.configurable_element_value[0])
    sibling_id = get_handle(parsed_sibling)
    assert get_parent_info(removed_id) is None

    assert api.removeDesignComponentInstance(removed_id)

    assert holder.component_instance == [parsed_sibling]
    assert resolve_handle(removed_id) is None
    assert resolve_handle(display_id) is None
    assert resolve_handle(description_id) is None
    assert resolve_handle(ref_id) is None
    assert resolve_handle(values_id) is None
    assert resolve_handle(value_id) is None
    assert resolve_handle(sibling_id) is parsed_sibling
    assert parsed_sibling.description == Description(value="keep sibling")
    assert api.getDesignComponentInstanceIDs(get_handle(root)) == [sibling_id]


def test_component_instance_remover_preserves_empty_holder_and_rejects_wrong_or_stale_handles() -> None:
    instance = _instance("u0")
    root = _registered(instance)
    holder = root.component_instances
    child_id = get_handle(instance)

    with pytest.raises(TgiError) as wrong:
        api.removeDesignComponentInstance(get_handle(root))
    assert wrong.value.fault_code == TgiFaultCode.INVALID_ID
    orphan_id = get_handle(_instance("orphan"))
    with pytest.raises(TgiError) as orphan:
        api.removeDesignComponentInstance(orphan_id)
    assert orphan.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as stale:
        api.removeDesignComponentInstance("stale-component-instance")
    assert stale.value.fault_code == TgiFaultCode.INVALID_ID

    assert api.removeDesignComponentInstance(child_id)
    assert holder.component_instance == []
    assert root.component_instances is holder
    assert resolve_handle(child_id) is None
    with pytest.raises(TgiError) as stale:
        api.removeDesignComponentInstance(child_id)
    assert stale.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "malformed_value",
    [object(), [Description(value="wrong child")]],
    ids=("non-sequence", "wrong-child"),
)
def test_component_instance_remover_rejects_forged_parent_and_malformed_membership_atomically(
    malformed_value: object,
) -> None:
    instance = _instance("u0")
    root = _registered(instance)
    other_instance = _instance("other")
    other = _registered(other_instance, name="other_design")
    child_id = get_handle(instance)
    register_parent(instance, other.component_instances, ("component_instance",), "list")

    with pytest.raises(TgiError) as forged_parent:
        api.removeDesignComponentInstance(child_id)
    assert forged_parent.value.fault_code == TgiFaultCode.INVALID_ID
    assert root.component_instances.component_instance == [instance]
    assert other.component_instances.component_instance == [other_instance]
    assert resolve_handle(child_id) is instance

    register_parent(instance, root.component_instances, ("component_instance",), "list")
    root.component_instances.component_instance = malformed_value  # type: ignore[assignment]
    with pytest.raises(TgiError) as malformed_list_error:
        api.removeDesignComponentInstance(child_id)
    assert malformed_list_error.value.fault_code == TgiFaultCode.INVALID_ID
    assert root.component_instances.component_instance is malformed_value
    assert resolve_handle(child_id) is instance
