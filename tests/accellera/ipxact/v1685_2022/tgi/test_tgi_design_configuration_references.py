"""Design configuration reference API contracts from IEEE 1685-2022 Annex F."""

import inspect
from collections.abc import Iterator
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
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2014 import DesignConfiguration as DesignConfiguration2014
from org.accellera.ipxact.v1685_2022 import (
    ComponentInstance,
    ConfigurableElementValue,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    Design,
    DesignConfiguration,
    InstanceName,
    LibraryRefType,
)
from org.accellera.ipxact.v1685_2022.generator_chain import GeneratorChain

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_API_FUNCTIONS = (
    "getDesignConfigurationDesignRefByID",
    "getDesignConfigurationDesignRefByVLNV",
    "setDesignConfigurationDesignRef",
    "removeDesignConfigurationDesignRef",
    "getDesignConfigurationGeneratorChainConfigurationIDs",
    "getGeneratorChainConfigurationRefByID",
    "getGeneratorChainConfigurationRefByVLNV",
    "addDesignConfigurationGeneratorChainConfiguration",
    "removeDesignConfigurationGeneratorChainConfiguration",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _design_reference() -> LibraryRefType:
    return LibraryRefType(vendor="vendor", library="library", name="design", version="1", id="design_ref_id")


def _generator_reference(name: str, version: str = "1", override: str | None = None) -> ConfigurableLibraryRefType:
    values = None
    if override is not None:
        values = ConfigurableElementValues(
            configurable_element_value=[ConfigurableElementValue(reference_id="WIDTH", value=override)]
        )
    return ConfigurableLibraryRefType(
        vendor="vendor",
        library="library",
        name=name,
        version=version,
        id=f"{name}_ref_id",
        configurable_element_values=values,
    )


def _document(
    *,
    design_ref: LibraryRefType | None = None,
    generators: tuple[ConfigurableLibraryRefType, ...] = (),
    root_name: str = "configuration",
) -> DesignConfiguration:
    root = DesignConfiguration(
        vendor="vendor",
        library="library",
        name=root_name,
        version="1",
        design_ref=design_ref,
        generator_chain_configuration=list(generators),
    )
    xml = XmlDocument.serializer().render(root)
    parsed = XmlDocument.parser().from_string(xml, DesignConfiguration)
    registry.register(parsed, ("vendor", "library", root_name, "1"))
    return parsed


def _round_trip(root: DesignConfiguration) -> str:
    xml = XmlDocument.serializer().render(root)
    parsed_xml = etree.fromstring(xml.encode())
    _SCHEMA.assertValid(parsed_xml)
    assert etree.QName(parsed_xml).namespace == NS
    assert XmlDocument.parser().from_string(xml, DesignConfiguration) == root
    return xml


def test_public_exports_and_native_annotations() -> None:
    optional_vlnv = tuple[str | None, str | None, str | None, str | None]
    expected = {
        "getDesignConfigurationDesignRefByID": ([str], str),
        "getDesignConfigurationDesignRefByVLNV": ([str], optional_vlnv),
        "setDesignConfigurationDesignRef": ([str, tuple[str, str, str, str]], bool),
        "removeDesignConfigurationDesignRef": ([str], bool),
        "getDesignConfigurationGeneratorChainConfigurationIDs": ([str], list[str]),
        "getGeneratorChainConfigurationRefByID": ([str], str),
        "getGeneratorChainConfigurationRefByVLNV": ([str], optional_vlnv),
        "addDesignConfigurationGeneratorChainConfiguration": ([str, tuple[str, str, str, str]], str),
        "removeDesignConfigurationGeneratorChainConfiguration": ([str], bool),
    }

    for name in _API_FUNCTIONS:
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        hints = get_type_hints(function)
        assert [hints[param] for param in inspect.signature(function).parameters] == expected[name][0]
        assert hints["return"] == expected[name][1]


def test_design_ref_getters_return_reference_and_registered_target_handles() -> None:
    root = _document(design_ref=_design_reference())
    root_id = get_handle(root)
    ref = root.design_ref
    assert ref is not None
    assert api.getDesignConfigurationDesignRefByVLNV(root_id) == ("vendor", "library", "design", "1")

    target = Design(vendor="vendor", library="library", name="design", version="1")
    registry.register(target, ("vendor", "library", "design", "1"))
    assert api.getDesignConfigurationDesignRefByID(root_id) == get_handle(target)
    _round_trip(root)


def test_design_ref_target_lookup_requires_exact_registered_vlnv_and_design_type() -> None:
    root = _document(design_ref=_design_reference())
    root_id = get_handle(root)
    other_version = Design(vendor="vendor", library="library", name="design", version="2")
    registry.register(other_version, ("vendor", "library", "design", "2"))
    with pytest.raises(TgiError) as missing:
        api.getDesignConfigurationDesignRefByID(root_id)
    assert missing.value.fault_code == TgiFaultCode.NOT_FOUND

    wrong_type = DesignConfiguration(vendor="vendor", library="library", name="design", version="1")
    registry.register(wrong_type, ("vendor", "library", "design", "1"))
    with pytest.raises(TgiError) as wrong:
        api.getDesignConfigurationDesignRefByID(root_id)
    assert wrong.value.fault_code == TgiFaultCode.NOT_FOUND


def test_design_ref_getters_and_removal_cover_absent_and_invalid_owner() -> None:
    root = _document()
    root_id = get_handle(root)
    assert api.getDesignConfigurationDesignRefByVLNV(root_id) == (None, None, None, None)
    assert not api.removeDesignConfigurationDesignRef(root_id)
    with pytest.raises(TgiError) as invalid_remove:
        api.removeDesignConfigurationDesignRef("missing-design-configuration")
    assert invalid_remove.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as absent:
        api.getDesignConfigurationDesignRefByID(root_id)
    assert absent.value.fault_code == TgiFaultCode.NOT_FOUND

    wrong_version_root = DesignConfiguration2014(vendor="vendor", library="library", name="legacy", version="1")
    wrong_version_id = get_handle(wrong_version_root)
    with pytest.raises(TgiError) as invalid:
        api.getDesignConfigurationDesignRefByID(wrong_version_id)
    assert invalid.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as invalid_set:
        api.setDesignConfigurationDesignRef(wrong_version_id, ("vendor", "library", "design", "1"))
    assert invalid_set.value.fault_code == TgiFaultCode.INVALID_ID

    wrong_kind = get_handle(Design(vendor="vendor", library="library", name="wrong", version="1"))
    for operation in (
        lambda: api.getDesignConfigurationDesignRefByVLNV("missing-design-configuration"),
        lambda: api.setDesignConfigurationDesignRef("missing-design-configuration", ("v", "l", "d", "1")),
        lambda: api.removeDesignConfigurationDesignRef("missing-design-configuration"),
        lambda: api.getDesignConfigurationDesignRefByVLNV(wrong_kind),
        lambda: api.setDesignConfigurationDesignRef(wrong_kind, ("v", "l", "d", "1")),
        lambda: api.removeDesignConfigurationDesignRef(wrong_kind),
    ):
        with pytest.raises(TgiError) as invalid_operation:
            operation()
        assert invalid_operation.value.fault_code == TgiFaultCode.INVALID_ID


def test_set_design_ref_preserves_reference_identity_id_and_handle_and_creates_when_absent() -> None:
    root = _document(design_ref=_design_reference())
    root_id = get_handle(root)
    original = root.design_ref
    assert original is not None
    reference_id = get_handle(original)
    assert api.setDesignConfigurationDesignRef(root_id, ("new_vendor", "new_library", "new_design", "2"))
    assert root.design_ref is original
    assert root.design_ref.id == "design_ref_id"
    assert get_handle(root.design_ref) == reference_id
    assert resolve_handle(reference_id) is original
    assert api.getDesignConfigurationDesignRefByVLNV(root_id) == ("new_vendor", "new_library", "new_design", "2")
    _round_trip(root)

    without_reference = _document(root_name="configuration_without_design_ref")
    without_reference_id = get_handle(without_reference)
    assert api.setDesignConfigurationDesignRef(without_reference_id, ("vendor", "library", "created", "1"))
    assert api.getDesignConfigurationDesignRefByVLNV(without_reference_id) == ("vendor", "library", "created", "1")
    assert without_reference.design_ref is not None
    _round_trip(without_reference)


@pytest.mark.parametrize(
    "vlnv",
    [
        ("vendor", "library", "design"),
        ("vendor", "library", "design", ""),
        ("vendor", "library", "design", " \t"),
        ("vendor", "library", "bad\x00name", "1"),
        ("vendor", "library", "design", 1),
        None,
    ],
)
def test_set_design_ref_rejects_invalid_vlnv_without_mutation(vlnv: object) -> None:
    root = _document(design_ref=_design_reference())
    root_id = get_handle(root)
    reference = root.design_ref
    before = _round_trip(root)

    with pytest.raises(TgiError) as error:
        api.setDesignConfigurationDesignRef(root_id, vlnv)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.design_ref is reference
    assert _round_trip(root) == before


def test_remove_design_ref_invalidates_only_reference_handle() -> None:
    root = _document(design_ref=_design_reference())
    root_id = get_handle(root)
    reference = root.design_ref
    assert reference is not None
    reference_id = get_handle(reference)

    assert api.removeDesignConfigurationDesignRef(root_id)
    assert root.design_ref is None
    assert resolve_handle(reference_id) is None
    assert not api.removeDesignConfigurationDesignRef(root_id)
    _round_trip(root)


def test_generator_reference_ids_preserve_order_and_resolve_owned_configurable_refs() -> None:
    root = _document(generators=(_generator_reference("first", override="16"), _generator_reference("second")))
    root_id = get_handle(root)
    refs = list(root.generator_chain_configuration)
    ref_ids = api.getDesignConfigurationGeneratorChainConfigurationIDs(root_id)
    assert ref_ids == [get_handle(ref) for ref in refs]
    assert [resolve_handle(ref_id) for ref_id in ref_ids] == refs
    for ref_id in ref_ids:
        parent = get_parent_info(ref_id)
        assert parent is not None
        assert (parent.parent_handle, parent.path, parent.container) == (
            root_id,
            ("generator_chain_configuration",),
            "list",
        )
    targets = [
        GeneratorChain(vendor="vendor", library="library", name=name, version="1")
        for name in ("first", "second")
    ]
    for target in targets:
        registry.register(target, (target.vendor, target.library, target.name, target.version))
    assert [api.getGeneratorChainConfigurationRefByID(ref_id) for ref_id in ref_ids] == [
        get_handle(target) for target in targets
    ]
    assert api.getGeneratorChainConfigurationRefByVLNV(ref_ids[0]) == ("vendor", "library", "first", "1")
    assert api.getGeneratorChainConfigurationRefByVLNV(ref_ids[1]) == ("vendor", "library", "second", "1")
    _round_trip(root)


def test_generator_reference_getters_reject_invalid_wrong_kind_and_unowned_handles() -> None:
    root = _document(generators=(_generator_reference("owned"),))
    wrong_kind = get_handle(Design(vendor="vendor", library="library", name="other", version="1"))
    unowned = get_handle(_generator_reference("orphan"))
    for bad_handle in ("missing-generator-ref", wrong_kind, unowned):
        with pytest.raises(TgiError) as by_id:
            api.getGeneratorChainConfigurationRefByID(bad_handle)
        assert by_id.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as by_vlnv:
            api.getGeneratorChainConfigurationRefByVLNV(bad_handle)
        assert by_vlnv.value.fault_code == TgiFaultCode.INVALID_ID

    owned = root.generator_chain_configuration[0]
    owned_id = get_handle(owned)
    with pytest.raises(TgiError) as target_missing:
        api.getGeneratorChainConfigurationRefByID(owned_id)
    assert target_missing.value.fault_code == TgiFaultCode.NOT_FOUND

    wrong_target = Design(vendor="vendor", library="library", name="owned", version="1")
    registry.register(wrong_target, ("vendor", "library", "owned", "1"))
    with pytest.raises(TgiError) as target_wrong_type:
        api.getGeneratorChainConfigurationRefByID(owned_id)
    assert target_wrong_type.value.fault_code == TgiFaultCode.NOT_FOUND

    for bad_handle in ("missing-design-configuration", wrong_kind):
        with pytest.raises(TgiError) as error:
            api.getDesignConfigurationGeneratorChainConfigurationIDs(bad_handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    for operation in (
        lambda: api.addDesignConfigurationGeneratorChainConfiguration(
            "missing-design-configuration", ("v", "l", "chain", "1")
        ),
        lambda: api.addDesignConfigurationGeneratorChainConfiguration(wrong_kind, ("v", "l", "chain", "1")),
    ):
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_add_generator_ref_validates_and_rejects_duplicate_full_vlnv_atomically() -> None:
    root = _document(generators=(_generator_reference("existing", override="32"),))
    root_id = get_handle(root)
    existing = root.generator_chain_configuration[0]
    existing_override = existing.configurable_element_values
    before = _round_trip(root)

    with pytest.raises(TgiError) as duplicate:
        api.addDesignConfigurationGeneratorChainConfiguration(root_id, ("vendor", "library", "existing", "1"))
    assert duplicate.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert root.generator_chain_configuration == [existing]
    assert existing.configurable_element_values is existing_override
    assert _round_trip(root) == before

    with pytest.raises(TgiError) as invalid:
        api.addDesignConfigurationGeneratorChainConfiguration(root_id, ("vendor", "library", "bad\x00name", "1"))
    assert invalid.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.generator_chain_configuration == [existing]
    assert _round_trip(root) == before

    added_id = api.addDesignConfigurationGeneratorChainConfiguration(root_id, ("vendor", "library", "existing", "2"))
    added = resolve_handle(added_id)
    assert added is root.generator_chain_configuration[-1]
    assert (added.vendor, added.library, added.name, added.version) == ("vendor", "library", "existing", "2")
    assert existing.configurable_element_values is existing_override
    assert existing.configurable_element_values.configurable_element_value[0].value == "32"
    assert api.getDesignConfigurationGeneratorChainConfigurationIDs(root_id) == [
        get_handle(ref) for ref in root.generator_chain_configuration
    ]
    _round_trip(root)


@pytest.mark.parametrize(
    "vlnv",
    [
        ("vendor", "library", "chain"),
        ("vendor", "library", "chain", ""),
        ("vendor", "library", "chain\x00", "1"),
        ("vendor", "library", "chain", None),
    ],
)
def test_add_generator_ref_rejects_invalid_vlnv_atomically(vlnv: object) -> None:
    root = _document(generators=(_generator_reference("existing"),))
    root_id = get_handle(root)
    before = _round_trip(root)
    refs = list(root.generator_chain_configuration)

    with pytest.raises(TgiError) as error:
        api.addDesignConfigurationGeneratorChainConfiguration(root_id, vlnv)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.generator_chain_configuration == refs
    assert _round_trip(root) == before


def test_remove_generator_ref_discovers_owner_invalidates_overrides_and_preserves_siblings() -> None:
    root = _document(generators=(_generator_reference("remove", override="8"), _generator_reference("keep")))
    first, sibling = root.generator_chain_configuration
    first_id, sibling_id = get_handle(first), get_handle(sibling)
    values = first.configurable_element_values
    assert values is not None
    values_id = get_handle(values)
    override_id = get_handle(values.configurable_element_value[0])
    target = GeneratorChain(vendor="vendor", library="library", name="remove", version="1")
    registry.register(target, ("vendor", "library", "remove", "1"))
    target_id = get_handle(target)

    assert api.removeDesignConfigurationGeneratorChainConfiguration(first_id)
    assert root.generator_chain_configuration == [sibling]
    assert [resolve_handle(item) for item in (first_id, values_id, override_id)] == [None, None, None]
    assert resolve_handle(sibling_id) is sibling
    assert resolve_handle(target_id) is target
    assert not api.removeDesignConfigurationGeneratorChainConfiguration(first_id)
    assert not api.removeDesignConfigurationGeneratorChainConfiguration("missing-generator-ref")
    assert not api.removeDesignConfigurationGeneratorChainConfiguration(get_handle(root))
    _round_trip(root)


def test_generator_ref_removal_returns_false_for_unowned_or_detached_reference() -> None:
    root = _document(generators=(_generator_reference("owned"),))
    unowned_id = get_handle(_generator_reference("orphan"))
    detached = root.generator_chain_configuration[0]
    detached_id = get_handle(detached)
    root.generator_chain_configuration = []

    assert not api.removeDesignConfigurationGeneratorChainConfiguration(unowned_id)
    assert not api.removeDesignConfigurationGeneratorChainConfiguration(detached_id)
    assert resolve_handle(detached_id) is detached
    _round_trip(root)


def test_generator_ref_getter_and_removal_reject_refs_owned_by_other_fields() -> None:
    unrelated = ConfigurableLibraryRefType(vendor="vendor", library="library", name="component", version="1")
    component_instance = ComponentInstance(
        instance_name=InstanceName(value="u0"),
        component_ref=unrelated,
    )
    unrelated_id = get_handle(unrelated)
    register_parent(unrelated, component_instance, ("component_ref",), "single")

    for operation in (
        lambda: api.getGeneratorChainConfigurationRefByID(unrelated_id),
        lambda: api.getGeneratorChainConfigurationRefByVLNV(unrelated_id),
    ):
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert not api.removeDesignConfigurationGeneratorChainConfiguration(unrelated_id)


def test_schema_is_2022_specific_and_round_trips_reference_annotations() -> None:
    root = _document(design_ref=_design_reference(), generators=(_generator_reference("chain", override="4"),))
    xml = _round_trip(root)
    legacy_xml = xml.replace(NS, "http://www.accellera.org/XMLSchema/IPXACT/1685-2014", 1)
    with pytest.raises(etree.DocumentInvalid):
        _SCHEMA.assertValid(etree.fromstring(legacy_xml.encode()))
