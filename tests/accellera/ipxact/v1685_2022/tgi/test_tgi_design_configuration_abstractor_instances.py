"""TGI contracts for design-configuration abstractor instances."""

import inspect
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import design_configuration as api
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
    AbstractorModeType,
    AbstractorType,
    Component,
    ConfigurableElementValue,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    DesignConfiguration,
    LibraryRefType,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_API_FUNCTIONS = (
    "getAbstractorInstanceAbstractorRefByID",
    "getAbstractorInstanceAbstractorRefByVLNV",
    "getAbstractorInstanceInstanceName",
    "getAbstractorInstanceViewName",
    "addAbstractorInstancesAbstractorInstance",
    "removeAbstractorInstancesAbstractorInstance",
    "setAbstractorInstanceAbstractorRef",
    "setAbstractorInstanceInstanceName",
    "setAbstractorInstanceViewName",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _group(name: str, second_name: str | None = None) -> DesignConfiguration.InterconnectionConfiguration:
    abstractor_instance_type = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance
    abstractor_instances_type = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances
    return DesignConfiguration.InterconnectionConfiguration(
        interconnection_ref=f"connection_{name}",
        abstractor_instances=[
            abstractor_instances_type(
                interface_ref=[
                    abstractor_instances_type.InterfaceRef(component_ref="u0", bus_ref="bus0"),
                    abstractor_instances_type.InterfaceRef(component_ref="u1", bus_ref="bus1"),
                ],
                abstractor_instance=[
                    abstractor_instance_type(
                        instance_name=name,
                        abstractor_ref=ConfigurableLibraryRefType(
                            vendor="vendor", library="library", name="seed", version="1"
                        ),
                        view_name="rtl",
                    ),
                    *(
                        [
                            abstractor_instance_type(
                                instance_name=second_name,
                                abstractor_ref=ConfigurableLibraryRefType(
                                    vendor="vendor", library="library", name="seed", version="1"
                                ),
                                view_name="rtl",
                            )
                        ]
                        if second_name is not None
                        else []
                    ),
                ],
            )
        ],
    )


def _new_document(*names: tuple[str, str | None]) -> DesignConfiguration:
    root = DesignConfiguration(
        vendor="vendor",
        library="library",
        name="configuration",
        version="1",
        design_ref=LibraryRefType(vendor="vendor", library="library", name="design", version="1"),
        interconnection_configuration=[_group(*group_names) for group_names in names],
    )
    xml = XmlDocument.serializer().render(root)
    parsed = XmlDocument.parser().from_string(xml, DesignConfiguration)
    registry.register(parsed, ("vendor", "library", "configuration", "1"))
    return parsed


def _valid_round_trip(root: DesignConfiguration) -> str:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, DesignConfiguration) == root
    return xml


def _instance(
    root: DesignConfiguration, group_index: int = 0, instance_index: int = 0
) -> DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance:
    return root.interconnection_configuration[group_index].abstractor_instances[0].abstractor_instance[instance_index]


def test_public_exports_and_native_runtime_annotations() -> None:
    expected = {
        "getAbstractorInstanceAbstractorRefByID": ([str], str),
        "getAbstractorInstanceAbstractorRefByVLNV": ([str], tuple[str | None, str | None, str | None, str | None]),
        "getAbstractorInstanceInstanceName": ([str], str | None),
        "getAbstractorInstanceViewName": ([str], str | None),
        "addAbstractorInstancesAbstractorInstance": ([str, tuple[str, str, str, str], str, str], str),
        "removeAbstractorInstancesAbstractorInstance": ([str], bool),
        "setAbstractorInstanceAbstractorRef": ([str, tuple[str, str, str, str]], bool),
        "setAbstractorInstanceInstanceName": ([str, str], bool),
        "setAbstractorInstanceViewName": ([str, str], bool),
    }

    for name in _API_FUNCTIONS:
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        hints = get_type_hints(function)
        assert [hints[param] for param in inspect.signature(function).parameters] == expected[name][0]
        assert hints["return"] == expected[name][1]


def test_reference_getters_resolve_registered_abstractor_and_report_missing_or_wrong_kind() -> None:
    root = _new_document(("u_abs", None))
    instance = _instance(root)
    instance_id = get_handle(instance)
    target = Abstractor(
        vendor="vendor",
        library="library",
        name="seed",
        version="1",
        abstractor_mode=AbstractorType.AbstractorMode(value=AbstractorModeType.DIRECT),
        bus_type=LibraryRefType(vendor="vendor", library="library", name="bus", version="1"),
        abstractor_interfaces=AbstractorType.AbstractorInterfaces(),
    )
    registry.register(target, ("vendor", "library", "seed", "1"))

    assert api.getAbstractorInstanceAbstractorRefByID(instance_id) == get_handle(target)
    assert api.getAbstractorInstanceAbstractorRefByVLNV(instance_id) == (
        "vendor",
        "library",
        "seed",
        "1",
    )

    registry.clear()
    with pytest.raises(TgiError) as missing:
        api.getAbstractorInstanceAbstractorRefByID(instance_id)
    assert missing.value.fault_code == TgiFaultCode.NOT_FOUND

    wrong_kind = Component(vendor="vendor", library="library", name="seed", version="1")
    registry.register(wrong_kind, ("vendor", "library", "seed", "1"))
    with pytest.raises(TgiError) as wrong:
        api.getAbstractorInstanceAbstractorRefByID(instance_id)
    assert wrong.value.fault_code == TgiFaultCode.NOT_FOUND


def test_name_and_view_getters_and_setters_accept_unicode_and_normalize_xml_whitespace() -> None:
    root = _new_document(("original", None))
    instance_id = get_handle(_instance(root))

    assert api.getAbstractorInstanceInstanceName(instance_id) == "original"
    assert api.getAbstractorInstanceViewName(instance_id) == "rtl"
    assert api.setAbstractorInstanceInstanceName(instance_id, "\t名札_α\n")
    assert api.setAbstractorInstanceViewName(instance_id, "\n表示_β\t")
    assert api.getAbstractorInstanceInstanceName(instance_id) == "名札_α"
    assert api.getAbstractorInstanceViewName(instance_id) == "表示_β"
    _valid_round_trip(root)


@pytest.mark.parametrize(
    ("setter", "field"),
    [
        (api.setAbstractorInstanceInstanceName, "instance_name"),
        (api.setAbstractorInstanceViewName, "view_name"),
    ],
)
@pytest.mark.parametrize("bad_value", ["", " \t\n ", "bad name", "bad\x00name"])
def test_name_and_view_setters_reject_invalid_xml_names_atomically(
    setter: Callable[[str, str], bool], field: str, bad_value: str
) -> None:
    root = _new_document(("original", None))
    instance = _instance(root)
    original = getattr(instance, field)
    before = _valid_round_trip(root)

    with pytest.raises(TgiError) as error:
        setter(get_handle(instance), bad_value)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(instance, field) == original
    assert _valid_round_trip(root) == before


def test_add_uses_declared_argument_order_and_creates_schema_valid_instance() -> None:
    root = _new_document(("seed", None), ("other", None))
    instances = root.interconnection_configuration[1].abstractor_instances[0]

    instance_id = api.addAbstractorInstancesAbstractorInstance(
        get_handle(instances), ("vendor2", "library2", "abstractor2", "9"), "  新規_α\t", " view_β "
    )
    added = resolve_handle(instance_id)
    assert added is instances.abstractor_instance[1]
    assert added.instance_name == "新規_α"
    assert added.view_name == "view_β"
    assert (
        added.abstractor_ref.vendor,
        added.abstractor_ref.library,
        added.abstractor_ref.name,
        added.abstractor_ref.version,
    ) == ("vendor2", "library2", "abstractor2", "9")
    assert _valid_round_trip(root)


@pytest.mark.parametrize(
    ("vlnv", "instance_name", "view_name"),
    [
        (("vendor", "library", "leaf"), "new", "rtl"),
        (("vendor", "library", "leaf", ""), "new", "rtl"),
        (("vendor", "library", "leaf\x00", "1"), "new", "rtl"),
        (("vendor", "library", "leaf", "1"), "bad name", "rtl"),
        (("vendor", "library", "leaf", "1"), "new", "bad\x00view"),
    ],
)
def test_add_rejects_invalid_values_without_editing_the_group(
    vlnv: tuple[object, ...], instance_name: str, view_name: str
) -> None:
    root = _new_document(("seed", None))
    instances = root.interconnection_configuration[0].abstractor_instances[0]
    before = _valid_round_trip(root)
    original_children = list(instances.abstractor_instance)

    with pytest.raises(TgiError) as error:
        api.addAbstractorInstancesAbstractorInstance(get_handle(instances), vlnv, instance_name, view_name)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert instances.abstractor_instance == original_children
    assert _valid_round_trip(root) == before


def test_instance_names_are_unique_across_interconnection_configuration_groups() -> None:
    root = _new_document(("used_name", None), ("other", None))
    other_group = root.interconnection_configuration[1].abstractor_instances[0]
    before = _valid_round_trip(root)

    with pytest.raises(TgiError) as error:
        api.addAbstractorInstancesAbstractorInstance(
            get_handle(other_group), ("v", "l", "next", "1"), "used_name", "rtl"
        )
    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert len(other_group.abstractor_instance) == 1
    assert _valid_round_trip(root) == before

    with pytest.raises(TgiError) as setter_error:
        api.setAbstractorInstanceInstanceName(get_handle(_instance(root, 1)), "used_name")
    assert setter_error.value.fault_code == TgiFaultCode.ALREADY_EXISTS


@pytest.mark.parametrize(
    "vlnv",
    [
        (),
        ("vendor", "library", "abstractor"),
        ("vendor", "library", "abstractor", ""),
        ("vendor", "library", "abstractor\x00", "1"),
        (1, "library", "abstractor", "1"),
    ],
)
def test_reference_setter_rejects_malformed_or_xml_invalid_vlnv_before_mutation(vlnv: tuple[object, ...]) -> None:
    root = _new_document(("seed", None))
    instance = _instance(root)
    reference = instance.abstractor_ref
    before = _valid_round_trip(root)
    previous = (reference.vendor, reference.library, reference.name, reference.version)

    with pytest.raises(TgiError) as error:
        api.setAbstractorInstanceAbstractorRef(get_handle(instance), vlnv)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert instance.abstractor_ref is reference
    assert (reference.vendor, reference.library, reference.name, reference.version) == previous
    assert _valid_round_trip(root) == before


def test_reference_setter_preserves_generated_reference_identity_metadata_and_overrides() -> None:
    root = _new_document(("seed", None))
    instance = _instance(root)
    reference = instance.abstractor_ref
    holder = ConfigurableElementValues(
        configurable_element_value=[ConfigurableElementValue(reference_id="WIDTH", value="32")]
    )
    reference.configurable_element_values = holder
    reference.id = "reference_metadata"
    reference_handle = get_handle(reference)
    override_handle = get_handle(holder.configurable_element_value[0])
    _valid_round_trip(root)

    assert api.setAbstractorInstanceAbstractorRef(
        get_handle(instance), ("new_vendor", "new_library", "new_abstractor", "2")
    )

    assert instance.abstractor_ref is reference
    assert get_handle(instance.abstractor_ref) == reference_handle
    assert reference.id == "reference_metadata"
    assert reference.configurable_element_values is holder
    assert holder.configurable_element_value[0].reference_id == "WIDTH"
    assert holder.configurable_element_value[0].value == "32"
    assert resolve_handle(override_handle) is holder.configurable_element_value[0]
    assert (reference.vendor, reference.library, reference.name, reference.version) == (
        "new_vendor",
        "new_library",
        "new_abstractor",
        "2",
    )
    assert _valid_round_trip(root)


def test_removal_recovers_parsed_ownership_invalidates_descendants_and_keeps_sibling() -> None:
    root = _new_document(("remove_me", "keep_me"))
    removed = _instance(root, instance_index=0)
    sibling = _instance(root, instance_index=1)
    overrides = ConfigurableElementValues(
        configurable_element_value=[ConfigurableElementValue(reference_id="WIDTH", value="16")]
    )
    removed.abstractor_ref.configurable_element_values = overrides
    removed_handles = [
        get_handle(removed),
        get_handle(removed.abstractor_ref),
        get_handle(overrides),
        get_handle(overrides.configurable_element_value[0]),
    ]
    sibling_handle = get_handle(sibling)
    sibling_reference_handle = get_handle(sibling.abstractor_ref)
    instances = root.interconnection_configuration[0].abstractor_instances[0]

    assert api.removeAbstractorInstancesAbstractorInstance(removed_handles[0])
    assert instances.abstractor_instance == [sibling]
    assert resolve_handle(sibling_handle) is sibling
    assert resolve_handle(sibling_reference_handle) is sibling.abstractor_ref
    assert all(resolve_handle(handle) is None for handle in removed_handles)
    assert not api.removeAbstractorInstancesAbstractorInstance(removed_handles[0])
    assert _valid_round_trip(root)


@pytest.mark.parametrize("wrong_kind", [False, True])
def test_leaf_operations_reject_invalid_or_wrong_kind_handles(wrong_kind: bool) -> None:
    root = _new_document(("seed", None))
    bad_handle = get_handle(root) if wrong_kind else "missing"
    calls = [
        lambda: api.getAbstractorInstanceAbstractorRefByID(bad_handle),
        lambda: api.getAbstractorInstanceAbstractorRefByVLNV(bad_handle),
        lambda: api.getAbstractorInstanceInstanceName(bad_handle),
        lambda: api.getAbstractorInstanceViewName(bad_handle),
        lambda: api.setAbstractorInstanceAbstractorRef(bad_handle, ("v", "l", "a", "1")),
        lambda: api.setAbstractorInstanceInstanceName(bad_handle, "name"),
        lambda: api.setAbstractorInstanceViewName(bad_handle, "view"),
        lambda: api.addAbstractorInstancesAbstractorInstance(bad_handle, ("v", "l", "a", "1"), "name", "view"),
    ]
    for call in calls:
        with pytest.raises(TgiError) as error:
            call()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert not api.removeAbstractorInstancesAbstractorInstance(bad_handle)


def test_new_child_can_be_removed_from_unregistered_container() -> None:
    group = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances()
    handle = api.addAbstractorInstancesAbstractorInstance(get_handle(group), ("v", "l", "a", "1"), "name", "view")
    child = group.abstractor_instance[0]
    ref_handle = get_handle(child.abstractor_ref)
    assert api.removeAbstractorInstancesAbstractorInstance(handle)
    assert not group.abstractor_instance
    assert resolve_handle(handle) is None
    assert resolve_handle(ref_handle) is None
