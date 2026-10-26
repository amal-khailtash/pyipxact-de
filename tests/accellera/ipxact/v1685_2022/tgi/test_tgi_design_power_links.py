"""Design power-domain link TGI contracts from IEEE 1685-2022."""

import inspect
from collections.abc import Iterator
from pathlib import Path
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import design as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import miscellaneous as miscellaneous_api
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
    Component,
    ComponentInstance,
    ComponentType,
    ConfigurableLibraryRefType,
    Description,
    Design,
    DesignConfiguration,
    DesignConfigurationInstantiationType,
    DesignInstantiationType,
    InstanceName,
    LibraryRefType,
    Model,
    PowerDomainLinks,
    StringExpression,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_API_FUNCTIONS = (
    "getComponentInstancePowerDomainLinkIDs",
    "getPowerDomainLinkExternalPowerDomainRef",
    "getPowerDomainLinkExternalPowerDomainRefByID",
    "getPowerDomainLinkExternalPowerDomainRefByName",
    "getPowerDomainLinkExternalPowerDomainRefExpression",
    "getPowerDomainLinkExternalPowerDomainRefID",
    "getPowerDomainLinkInternalPowerDomainRefs",
    "setPowerDomainLinkExternalPowerDomainRef",
)
_DESIGN_VLNV = ("vendor", "library", "design", "1")
_CONFIGURATION_VLNV = ("vendor", "library", "configuration", "1")
_POWER_LINK = PowerDomainLinks.PowerDomainLink
_INTERNAL_REFERENCE = PowerDomainLinks.PowerDomainLink.InternalPowerDomainReference


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _link(
    external: StringExpression | None = None,
    *internal_names: str,
    link_id: str | None = None,
) -> PowerDomainLinks.PowerDomainLink:
    return _POWER_LINK(
        external_power_domain_reference=external or StringExpression(value='"TOP_PD"'),
        internal_power_domain_reference=[_INTERNAL_REFERENCE(value=name) for name in internal_names or ("CORE_PD",)],
        id=link_id,
    )


def _instance(
    name: str = "u0",
    *,
    link: PowerDomainLinks.PowerDomainLink | None = None,
    component_vlnv: tuple[str, str, str, str] = ("vendor", "library", "child", "1"),
) -> ComponentInstance:
    links = PowerDomainLinks(power_domain_link=[link]) if link is not None else None
    return ComponentInstance(
        instance_name=InstanceName(value=name),
        component_ref=ConfigurableLibraryRefType(
            vendor=component_vlnv[0], library=component_vlnv[1], name=component_vlnv[2], version=component_vlnv[3]
        ),
        power_domain_links=links,
    )


def _design_with_instances(*instances: ComponentInstance, name: str = "design") -> Design:
    from org.accellera.ipxact.v1685_2022 import ComponentInstances

    return Design(
        vendor=_DESIGN_VLNV[0],
        library=_DESIGN_VLNV[1],
        name=name,
        version=_DESIGN_VLNV[3],
        component_instances=ComponentInstances(component_instance=list(instances)),
    )


def _register_design(root: Design) -> Design:
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    return root


def _register_parsed(root: Design) -> Design:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Design)
    return _register_design(parsed)


def _round_trip(root: Design) -> str:
    xml = XmlDocument.serializer().render(root)
    parsed_xml = etree.fromstring(xml.encode())
    _SCHEMA.assertValid(parsed_xml)
    assert XmlDocument.serializer().render(XmlDocument.parser().from_string(xml, Design)) == xml
    return xml


def _component_for_design(
    design: Design,
    *domain_names: str,
    duplicate_design_references: bool = False,
    as_configuration: bool = False,
    component_name: str = "parent_component",
) -> tuple[Component, tuple[str, ...]]:
    from org.accellera.ipxact.v1685_2022 import ComponentType

    instantiations: list[DesignInstantiationType | DesignConfigurationInstantiationType]
    if as_configuration:
        configuration = DesignConfiguration(
            vendor=_CONFIGURATION_VLNV[0],
            library=_CONFIGURATION_VLNV[1],
            name=_CONFIGURATION_VLNV[2],
            version=_CONFIGURATION_VLNV[3],
            design_ref=LibraryRefType(
                vendor=design.vendor,
                library=design.library,
                name=design.name,
                version=design.version,
            ),
        )
        registry.register(configuration, _CONFIGURATION_VLNV)
        instantiations = [
            DesignConfigurationInstantiationType(
                name="configuration_instantiation",
                design_configuration_ref=ConfigurableLibraryRefType(
                    vendor=configuration.vendor,
                    library=configuration.library,
                    name=configuration.name,
                    version=configuration.version,
                ),
            )
        ]
    else:
        references = 2 if duplicate_design_references else 1
        instantiations = [
            DesignInstantiationType(
                name=f"design_instantiation_{index}",
                design_ref=ConfigurableLibraryRefType(
                    vendor=design.vendor,
                    library=design.library,
                    name=design.name,
                    version=design.version,
                ),
            )
            for index in range(references)
        ]
    component = Component(
        vendor="vendor",
        library="library",
        name=component_name,
        version="1",
        power_domains=ComponentType.PowerDomains(
            power_domain=[ComponentType.PowerDomains.PowerDomain(name=name) for name in domain_names]
        ),
        model=Model(
            instantiations=Model.Instantiations(
                component_instantiation_or_design_instantiation_or_design_configuration_instantiation=instantiations
            )
        ),
    )
    registry.register(component, (component.vendor, component.library, component.name, component.version))
    return component, tuple(get_handle(domain) for domain in component.power_domains.power_domain)


def test_public_exports_and_annex_f_signatures() -> None:
    expected = {
        "getComponentInstancePowerDomainLinkIDs": ([str], list[str]),
        "getPowerDomainLinkExternalPowerDomainRef": ([str], str | None),
        "getPowerDomainLinkExternalPowerDomainRefByID": ([str], str | None),
        "getPowerDomainLinkExternalPowerDomainRefByName": ([str], str | None),
        "getPowerDomainLinkExternalPowerDomainRefExpression": ([str], str | None),
        "getPowerDomainLinkExternalPowerDomainRefID": ([str], str | None),
        "getPowerDomainLinkInternalPowerDomainRefs": ([str], list[str]),
        "setPowerDomainLinkExternalPowerDomainRef": ([str, str], bool),
    }
    sections = {
        "getComponentInstancePowerDomainLinkIDs": "F.7.37.11",
        "getPowerDomainLinkExternalPowerDomainRef": "F.7.37.28",
        "getPowerDomainLinkExternalPowerDomainRefByID": "F.7.37.29",
        "getPowerDomainLinkExternalPowerDomainRefByName": "F.7.37.30",
        "getPowerDomainLinkExternalPowerDomainRefExpression": "F.7.37.31",
        "getPowerDomainLinkExternalPowerDomainRefID": "F.7.37.32",
        "getPowerDomainLinkInternalPowerDomainRefs": "F.7.37.33",
        "setPowerDomainLinkExternalPowerDomainRef": "F.7.38.37",
    }
    assert set(_API_FUNCTIONS) == set(expected) == set(sections)
    for name in _API_FUNCTIONS:
        function = getattr(api, name)
        signature = inspect.signature(function)
        assert getattr(tgi, name) is function
        assert name in api.__all__ and name in tgi.__all__
        hints = get_type_hints(function)
        assert [hints[parameter] for parameter in signature.parameters] == expected[name][0]
        assert hints["return"] == expected[name][1]
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert f"Section: {sections[name]}." in inspect.getdoc(function)


def test_link_getters_evaluate_string_values_retain_source_and_register_typed_child_ownership() -> None:
    expression = StringExpression(value='{"TOP", "_PD"}', other_attributes={"{urn:test}marker": "preserve"})
    link = _link(expression, "CORE_PD", "AUX_PD", link_id="link_id")
    instance = _instance(link=link)
    root = _register_parsed(_design_with_instances(instance))
    parsed_instance = root.component_instances.component_instance[0]
    parsed_link = parsed_instance.power_domain_links.power_domain_link[0]
    link_id = get_handle(parsed_link)
    expression_id = get_handle(parsed_link.external_power_domain_reference)
    internal_refs = tuple(parsed_link.internal_power_domain_reference)
    parsed_link.internal_power_domain_reference = internal_refs
    holder_links = parsed_instance.power_domain_links.power_domain_link
    parsed_instance.power_domain_links.power_domain_link = tuple(holder_links)

    ids = api.getComponentInstancePowerDomainLinkIDs(get_handle(parsed_instance))
    assert ids == [link_id]
    assert api.getPowerDomainLinkExternalPowerDomainRef(link_id) == "TOP_PD"
    assert api.getPowerDomainLinkExternalPowerDomainRefByName(link_id) == "TOP_PD"
    assert api.getPowerDomainLinkExternalPowerDomainRefExpression(link_id) == '{"TOP", "_PD"}'
    assert parsed_link.external_power_domain_reference.other_attributes == {"{urn:test}marker": "preserve"}
    assert api.getPowerDomainLinkExternalPowerDomainRefID(link_id) == expression_id
    assert api.getPowerDomainLinkInternalPowerDomainRefs(link_id) == ["CORE_PD", "AUX_PD"]
    assert parsed_link.internal_power_domain_reference is internal_refs
    assert parsed_instance.power_domain_links.power_domain_link is not holder_links
    assert tuple(parsed_instance.power_domain_links.power_domain_link) == tuple(holder_links)

    expected_parents = (
        (link_id, get_handle(parsed_instance.power_domain_links), ("power_domain_link",), "list"),
        (expression_id, link_id, ("external_power_domain_reference",), "single"),
        (get_handle(internal_refs[0]), link_id, ("internal_power_domain_reference",), "list"),
    )
    for child_id, parent_id, path, container in expected_parents:
        info = get_parent_info(child_id)
        assert info is not None
        assert (info.parent_handle, info.path, info.container) == (parent_id, path, container)


def test_link_getters_return_none_for_absent_wrapper_and_fault_on_unresolved_string_expression() -> None:
    missing_link = _POWER_LINK(
        external_power_domain_reference=None,  # type: ignore[arg-type]
        internal_power_domain_reference=[_INTERNAL_REFERENCE(value="CORE_PD")],
    )
    unresolved_link = _link(StringExpression(value="MISSING_DOMAIN"), "CORE_PD")
    instance = _instance(link=missing_link)
    instance.power_domain_links.power_domain_link.append(unresolved_link)
    _register_design(_design_with_instances(instance))
    first_id, second_id = [get_handle(link) for link in instance.power_domain_links.power_domain_link]

    for getter in (
        api.getPowerDomainLinkExternalPowerDomainRef,
        api.getPowerDomainLinkExternalPowerDomainRefByID,
        api.getPowerDomainLinkExternalPowerDomainRefByName,
        api.getPowerDomainLinkExternalPowerDomainRefExpression,
        api.getPowerDomainLinkExternalPowerDomainRefID,
    ):
        assert getter(first_id) is None
    assert api.getPowerDomainLinkExternalPowerDomainRefExpression(second_id) == "MISSING_DOMAIN"
    with pytest.raises(TgiError) as unresolved:
        api.getPowerDomainLinkExternalPowerDomainRef(second_id)
    assert unresolved.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    "malformation",
    ["wrong-holder", "wrong-link-list", "wrong-link-child"],
    ids=("wrong-holder", "wrong-link-list", "wrong-link-child"),
)
def test_component_instance_power_link_ids_reject_malformed_graph(malformation: str) -> None:
    instance = _instance(link=_link())
    _register_design(_design_with_instances(instance))
    if malformation == "wrong-holder":
        instance.power_domain_links = object()  # type: ignore[assignment]
    elif malformation == "wrong-link-list":
        instance.power_domain_links.power_domain_link = object()  # type: ignore[assignment]
    else:
        instance.power_domain_links.power_domain_link = [instance]

    with pytest.raises(TgiError) as error:
        api.getComponentInstancePowerDomainLinkIDs(get_handle(instance))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_component_instance_power_link_ids_return_empty_for_unowned_instance_without_links() -> None:
    assert api.getComponentInstancePowerDomainLinkIDs(get_handle(_instance())) == []


@pytest.mark.parametrize(
    "field,malformation",
    [
        ("external_power_domain_reference", "wrong-wrapper"),
        ("external_power_domain_reference", "wrong-value"),
        ("internal_power_domain_reference", "non-sequence"),
        ("internal_power_domain_reference", "wrong-child"),
        ("internal_power_domain_reference", "non-string-name"),
        ("internal_power_domain_reference", "invalid-name"),
    ],
    ids=(
        "external-wrapper",
        "external-content",
        "internal-non-sequence",
        "internal-wrong-child",
        "internal-non-string",
        "internal-name",
    ),
)
def test_link_getters_reject_malformed_reference_wrappers_and_contents(field: str, malformation: str) -> None:
    link = _link()
    instance = _instance(link=link)
    _register_design(_design_with_instances(instance))
    if field == "external_power_domain_reference":
        if malformation == "wrong-wrapper":
            link.external_power_domain_reference = object()  # type: ignore[assignment]
            for getter in (
                api.getPowerDomainLinkExternalPowerDomainRef,
                api.getPowerDomainLinkExternalPowerDomainRefByID,
                api.getPowerDomainLinkExternalPowerDomainRefByName,
                api.getPowerDomainLinkExternalPowerDomainRefExpression,
                api.getPowerDomainLinkExternalPowerDomainRefID,
            ):
                with pytest.raises(TgiError) as error:
                    getter(get_handle(link))
                assert error.value.fault_code == TgiFaultCode.INVALID_ID
            return
        expression = StringExpression(value=17)  # type: ignore[arg-type]
        link.external_power_domain_reference = expression
        for getter in (
            api.getPowerDomainLinkExternalPowerDomainRef,
            api.getPowerDomainLinkExternalPowerDomainRefByName,
        ):
            with pytest.raises(TgiError) as error:
                getter(get_handle(link))
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as malformed_source:
            api.getPowerDomainLinkExternalPowerDomainRefExpression(get_handle(link))
        assert malformed_source.value.fault_code == TgiFaultCode.INVALID_ID
        assert api.getPowerDomainLinkExternalPowerDomainRefID(get_handle(link)) == get_handle(expression)
        with pytest.raises(TgiError) as malformed_by_id:
            api.getPowerDomainLinkExternalPowerDomainRefByID(get_handle(link))
        assert malformed_by_id.value.fault_code == TgiFaultCode.INVALID_ID
        return
    elif malformation == "non-sequence":
        link.internal_power_domain_reference = object()  # type: ignore[assignment]
        getters = (api.getPowerDomainLinkInternalPowerDomainRefs,)
    elif malformation == "wrong-child":
        link.internal_power_domain_reference = [Description(value="wrong child")]  # type: ignore[list-item]
        getters = (api.getPowerDomainLinkInternalPowerDomainRefs,)
    elif malformation == "non-string-name":
        link.internal_power_domain_reference[0].value = 7  # type: ignore[assignment]
        getters = (api.getPowerDomainLinkInternalPowerDomainRefs,)
    else:
        link.internal_power_domain_reference[0].value = "bad name"
        getters = (api.getPowerDomainLinkInternalPowerDomainRefs,)

    for getter in getters:
        with pytest.raises(TgiError) as error:
            getter(get_handle(link))
        expected_fault = TgiFaultCode.INVALID_ARGUMENT if malformation == "invalid-name" else TgiFaultCode.INVALID_ID
        assert error.value.fault_code == expected_fault


def test_internal_reference_getter_collapses_names_and_preserves_tuple_storage() -> None:
    link = _link(StringExpression(value='"TOP_PD"'), " CORE_PD ", "AUX_PD")
    instance = _instance(link=link)
    _register_design(_design_with_instances(instance))
    link.internal_power_domain_reference = tuple(link.internal_power_domain_reference)

    assert api.getPowerDomainLinkInternalPowerDomainRefs(get_handle(link)) == ["CORE_PD", "AUX_PD"]
    assert isinstance(link.internal_power_domain_reference, tuple)


def test_external_domain_by_id_uses_referencing_component_for_direct_design_instantiation() -> None:
    link = _link(StringExpression(value='"TOP_PD"'), "CORE_PD")
    instance = _instance(link=link)
    root = _register_design(_design_with_instances(instance))
    owner, expected_domain_ids = _component_for_design(root, "TOP_PD", "OTHER_PD", duplicate_design_references=True)
    child_component = Component(
        vendor="vendor",
        library="library",
        name="child",
        version="1",
        power_domains=ComponentType.PowerDomains(power_domain=[ComponentType.PowerDomains.PowerDomain(name="TOP_PD")]),
    )
    registry.register(child_component, (child_component.vendor, child_component.library, child_component.name, "1"))

    link_id = get_handle(link)
    assert api.getPowerDomainLinkExternalPowerDomainRefByID(link_id) == expected_domain_ids[0]
    assert api.getPowerDomainLinkExternalPowerDomainRefByID(link_id) != get_handle(
        child_component.power_domains.power_domain[0]
    )
    assert resolve_handle(get_handle(owner)) is owner


def test_external_domain_by_id_resolves_through_registered_design_configuration() -> None:
    root = _register_design(
        _design_with_instances(_instance(link=_link(StringExpression(value='"TOP_PD"'), "CORE_PD")))
    )
    _owner, domain_ids = _component_for_design(root, "TOP_PD", as_configuration=True)
    link_id = get_handle(root.component_instances.component_instance[0].power_domain_links.power_domain_link[0])

    assert api.getPowerDomainLinkExternalPowerDomainRefByID(link_id) == domain_ids[0]


def test_external_domain_resolution_returns_none_without_context_or_match_and_ignores_unrelated_roots() -> None:
    root = _register_design(
        _design_with_instances(_instance(link=_link(StringExpression(value='"TOP_PD"'), "CORE_PD")))
    )
    link_id = get_handle(root.component_instances.component_instance[0].power_domain_links.power_domain_link[0])
    assert api.getPowerDomainLinkExternalPowerDomainRefByID(link_id) is None
    unrelated, _ = _component_for_design(root, "OTHER_PD", component_name="unrelated")
    assert api.getPowerDomainLinkExternalPowerDomainRefByID(link_id) is None
    assert resolve_handle(get_handle(unrelated)) is unrelated

    registry.unregister((unrelated.vendor, unrelated.library, unrelated.name, unrelated.version))
    missing_reference_owner = Component(
        vendor="vendor",
        library="library",
        name="missing_reference_owner",
        version="1",
        power_domains=ComponentType.PowerDomains(power_domain=[ComponentType.PowerDomains.PowerDomain(name="TOP_PD")]),
        model=Model(
            instantiations=Model.Instantiations(
                component_instantiation_or_design_instantiation_or_design_configuration_instantiation=[
                    DesignInstantiationType(
                        name="missing_design",
                        design_ref=ConfigurableLibraryRefType(
                            vendor="vendor", library="library", name="unregistered_design", version="1"
                        ),
                    )
                ]
            )
        ),
    )
    registry.register(missing_reference_owner, ("vendor", "library", "missing_reference_owner", "1"))
    assert api.getPowerDomainLinkExternalPowerDomainRefByID(link_id) is None


def test_external_domain_resolution_rejects_multiple_contexts_and_duplicate_normalized_domains() -> None:
    root = _register_design(
        _design_with_instances(_instance(link=_link(StringExpression(value='"TOP_PD"'), "CORE_PD")))
    )
    link_id = get_handle(root.component_instances.component_instance[0].power_domain_links.power_domain_link[0])
    _component_for_design(root, "TOP_PD", component_name="owner_a")
    _component_for_design(root, "TOP_PD", component_name="owner_b")
    with pytest.raises(TgiError) as ambiguous_context:
        api.getPowerDomainLinkExternalPowerDomainRefByID(link_id)
    assert ambiguous_context.value.fault_code == TgiFaultCode.INVALID_ARGUMENT

    registry.clear()
    root = _register_design(
        _design_with_instances(_instance(link=_link(StringExpression(value='"TOP_PD"'), "CORE_PD")))
    )
    link_id = get_handle(root.component_instances.component_instance[0].power_domain_links.power_domain_link[0])
    _component_for_design(root, "TOP_PD", " TOP_PD ")
    with pytest.raises(TgiError) as duplicate_domain:
        api.getPowerDomainLinkExternalPowerDomainRefByID(link_id)
    assert duplicate_domain.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_external_setter_evaluates_expression_and_preserves_wrapper_metadata() -> None:
    expression = StringExpression(value='"OLD_PD"', other_attributes={"{urn:test}marker": "keep"})
    link = _link(expression, "CORE_PD", link_id="link_id")
    instance = _instance(link=link)
    root = _register_design(_design_with_instances(instance))
    expression_id = get_handle(expression)

    assert api.getPowerDomainLinkExternalPowerDomainRef(get_handle(link)) == "OLD_PD"
    assert api.setPowerDomainLinkExternalPowerDomainRef(get_handle(link), '{"NEW_", "PD"}')

    assert link.external_power_domain_reference is expression
    assert get_handle(link.external_power_domain_reference) == expression_id
    assert expression.value == '{"NEW_", "PD"}'
    assert expression.other_attributes == {"{urn:test}marker": "keep"}
    assert api.getPowerDomainLinkExternalPowerDomainRef(get_handle(link)) == "NEW_PD"
    assert api.getPowerDomainLinkExternalPowerDomainRefExpression(get_handle(link)) == '{"NEW_", "PD"}'
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "expression",
    ["", "42", "1 +", '"NEW_" + "PD"', "bad\x00text", None, 17],
    ids=("empty", "numeric", "malformed", "numeric-string-addition", "xml-illegal", "none", "non-string"),
)
def test_external_setter_rejects_invalid_expression_without_mutation(expression: object) -> None:
    original = StringExpression(value='"OLD_PD"', other_attributes={"{urn:test}marker": "keep"})
    link = _link(original, "CORE_PD")
    instance = _instance(link=link)
    _register_design(_design_with_instances(instance))

    with pytest.raises(TgiError) as error:
        api.setPowerDomainLinkExternalPowerDomainRef(get_handle(link), expression)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert link.external_power_domain_reference is original
    assert original.value == '"OLD_PD"'
    assert original.other_attributes == {"{urn:test}marker": "keep"}


def test_external_setter_defers_only_undeclared_string_identifiers_and_creates_missing_wrapper() -> None:
    link = _POWER_LINK(
        external_power_domain_reference=None,  # type: ignore[arg-type]
        internal_power_domain_reference=[_INTERNAL_REFERENCE(value="CORE_PD")],
    )
    instance = _instance(link=link)
    root = _register_design(_design_with_instances(instance))

    assert api.setPowerDomainLinkExternalPowerDomainRef(get_handle(link), "TOP_PD")

    expression = link.external_power_domain_reference
    assert isinstance(expression, StringExpression)
    assert expression.value == "TOP_PD"
    info = get_parent_info(get_handle(expression))
    assert info is not None
    assert (info.parent_handle, info.path, info.container) == (
        get_handle(link),
        ("external_power_domain_reference",),
        "single",
    )
    assert api.getPowerDomainLinkExternalPowerDomainRefExpression(get_handle(link)) == "TOP_PD"
    with pytest.raises(TgiError) as unresolved:
        api.getPowerDomainLinkExternalPowerDomainRef(get_handle(link))
    assert unresolved.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert _round_trip(root)


def test_generic_string_expression_operations_share_link_setter_string_semantics() -> None:
    link = _link(StringExpression(value='"START"'))
    instance = _instance(link=link)
    _register_design(_design_with_instances(instance))
    expression_id = api.getPowerDomainLinkExternalPowerDomainRefID(get_handle(link))

    assert miscellaneous_api.getExpressionValue(expression_id) == "START"
    with pytest.raises(TgiError) as numeric:
        miscellaneous_api.setExpressionValue(expression_id, "42")
    assert numeric.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert link.external_power_domain_reference.value == '"START"'
    assert miscellaneous_api.setExpressionValue(expression_id, '"END"')
    assert miscellaneous_api.getExpressionValue(expression_id) == "END"
    assert miscellaneous_api.getExpression(expression_id) == '"END"'


@pytest.mark.parametrize(
    "operation",
    ["external-value", "external-id", "internal-list", "component-links", "set-external"],
    ids=("external-value", "external-id", "internal-list", "component-links", "setter"),
)
def test_link_api_rejects_wrong_stale_and_orphan_handles(operation: str) -> None:
    link = _link()
    instance = _instance(link=link)
    root = _register_design(_design_with_instances(instance))
    wrong_id = get_handle(instance)
    stale_id = "stale-power-domain-link"
    operation_by_name = {
        "external-value": api.getPowerDomainLinkExternalPowerDomainRef,
        "external-id": api.getPowerDomainLinkExternalPowerDomainRefID,
        "internal-list": api.getPowerDomainLinkInternalPowerDomainRefs,
        "component-links": api.getComponentInstancePowerDomainLinkIDs,
        "set-external": lambda handle: api.setPowerDomainLinkExternalPowerDomainRef(handle, '"NEW_PD"'),
    }
    function = operation_by_name[operation]
    bad_handles = (wrong_id, stale_id) if operation != "component-links" else (get_handle(root), stale_id)
    for bad_handle in bad_handles:
        with pytest.raises(TgiError) as error:
            function(bad_handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
