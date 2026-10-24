"""Generated-model target resolution for Element attribute BASE ``*ByID``."""

import pytest
from xsdata.formats.dataclass.parsers import XmlParser

from amal.eda.accellera.ipxact.v1685_2022.tgi._attribute_references import _TARGET_TYPES, resolve_attribute_reference
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, registry
from amal.eda.accellera.ipxact.v1685_2022.tgi.element_attribute import _BASE_ATTRIBUTE_VALUE_FUNCS
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentInstance,
    ComponentInstances,
    ConfigurableLibraryRefType,
    Design,
    DesignConfiguration,
    Interconnection,
    Interconnections,
    Port,
)
from org.accellera.ipxact.v1685_2022.active_interface import ActiveInterface
from org.accellera.ipxact.v1685_2022.ad_hoc_connection import AdHocConnection
from org.accellera.ipxact.v1685_2022.ad_hoc_connections import AdHocConnections
from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.address_block_ref import AddressBlockRef
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.address_spaces import AddressSpaces
from org.accellera.ipxact.v1685_2022.alternate_register_ref import AlternateRegisterRef
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.bank import Bank
from org.accellera.ipxact.v1685_2022.bank_alignment_type import BankAlignmentType
from org.accellera.ipxact.v1685_2022.bank_ref import BankRef
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.bus_interface import BusInterface
from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType
from org.accellera.ipxact.v1685_2022.bus_interfaces import BusInterfaces
from org.accellera.ipxact.v1685_2022.choices import Choices
from org.accellera.ipxact.v1685_2022.component_port_direction_type import ComponentPortDirectionType
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.design_configuration import DesignConfiguration as DesignConfigurationModel
from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.indirect_address_ref import IndirectAddressRef
from org.accellera.ipxact.v1685_2022.indirect_data_ref import IndirectDataRef
from org.accellera.ipxact.v1685_2022.indirect_interface import IndirectInterface
from org.accellera.ipxact.v1685_2022.indirect_interfaces import IndirectInterfaces
from org.accellera.ipxact.v1685_2022.instance_name import InstanceName
from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType
from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps
from org.accellera.ipxact.v1685_2022.memory_remap import MemoryRemap
from org.accellera.ipxact.v1685_2022.memory_remap_ref import MemoryRemapRef
from org.accellera.ipxact.v1685_2022.model import Model
from org.accellera.ipxact.v1685_2022.parameter import Parameter
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.port_wire_type import PortWireType
from org.accellera.ipxact.v1685_2022.power_domain_ref import PowerDomainRef
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.register_file_ref import RegisterFileRef
from org.accellera.ipxact.v1685_2022.register_ref import RegisterRef
from org.accellera.ipxact.v1685_2022.reset import Reset
from org.accellera.ipxact.v1685_2022.signed_longint_expression import SignedLongintExpression
from org.accellera.ipxact.v1685_2022.struct_port_type_defs import StructPortTypeDefs
from org.accellera.ipxact.v1685_2022.sub_port_reference import SubPortReference
from org.accellera.ipxact.v1685_2022.sub_port_type import PortStructuredType, SubPortType
from org.accellera.ipxact.v1685_2022.subspace_map import SubspaceMap
from org.accellera.ipxact.v1685_2022.transparent_bridge import TransparentBridge
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression
from org.accellera.ipxact.v1685_2022.value import Value
from org.accellera.ipxact.v1685_2022.wire_power_constraint_type import WirePowerConstraintType

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def test_reference_target_table_covers_all_annex_f_base_by_id_names():
    by_id_xml_names = {
        attr_name
        for function_name, attr_name, _coerce, kind in _BASE_ATTRIBUTE_VALUE_FUNCS
        if function_name.endswith("ByID") and kind == "ref"
    }
    by_id_xml_names = {"memoryRemapRef" if name == "memoryReMapRef" else name for name in by_id_xml_names}
    assert by_id_xml_names | {"registerRef"} == set(_TARGET_TYPES)


def _parsed_component(
    address_spaces: str = "<ipxact:addressSpace><ipxact:name>fabric</ipxact:name>"
    "<ipxact:range>1</ipxact:range><ipxact:width>1</ipxact:width></ipxact:addressSpace>",
):
    xml = (
        f'<ipxact:component xmlns:ipxact="{NS}">'
        "<ipxact:vendor>v</ipxact:vendor><ipxact:library>l</ipxact:library>"
        "<ipxact:name>source</ipxact:name><ipxact:version>1</ipxact:version>"
        f"<ipxact:addressSpaces>{address_spaces}</ipxact:addressSpaces>"
        "<ipxact:busInterfaces><ipxact:busInterface><ipxact:name>init</ipxact:name>"
        '<ipxact:busType vendor="v" library="l" name="bus" version="1"/>'
        '<ipxact:initiator><ipxact:addressSpaceRef addressSpaceRef="fabric"/></ipxact:initiator>'
        "</ipxact:busInterface></ipxact:busInterfaces></ipxact:component>"
    )
    return XmlParser().from_string(xml, Component)


def _registered_component(name: str, *, bus_name: str = "fabric", port_name: str = "stream") -> Component:
    structured = PortStructuredType(
        sub_ports=PortStructuredType.SubPorts(sub_port=[SubPortType(name="payload")]),
        struct_port_type_defs=StructPortTypeDefs(),
    )
    component = Component(
        vendor="v",
        library="l",
        name=name,
        version="1",
        bus_interfaces=BusInterfaces(
            bus_interface=[
                BusInterface(
                    name=bus_name,
                    bus_type=ConfigurableLibraryRefType(vendor="v", library="l", name="bus", version="1"),
                )
            ]
        ),
        model=Model(ports=Model.Ports(port=[Port(name=port_name, wire_or_transactional_or_structured=structured)])),
    )
    registry.register(component, ("v", "l", name, "1"))
    return component


def _design(target_name: str = "leaf") -> tuple[Design, object, object]:
    instance = ComponentInstance(
        instance_name=InstanceName(value="u0"),
        component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name=target_name, version="1"),
    )
    active = ActiveInterface(component_instance_ref="u0", bus_ref="fabric")
    internal = AdHocConnection.PortReferences.InternalPortReference(component_instance_ref="u0", port_ref="stream")
    connection = AdHocConnection(
        name="gpio",
        port_references=AdHocConnection.PortReferences(internal_port_reference_or_external_port_reference=[internal]),
    )
    design = Design(
        vendor="v",
        library="l",
        name="top",
        version="1",
        component_instances=ComponentInstances(component_instance=[instance]),
        interconnections=Interconnections(
            interconnection_or_monitor_interconnection=[Interconnection(name="bus", active_interface=[active])]
        ),
        ad_hoc_connections=AdHocConnections(ad_hoc_connection=[connection]),
    )
    registry.register(design, ("v", "l", "top", "1"))
    return design, active, internal


def test_address_space_reference_resolves_in_registered_parsed_root_and_is_isolated():
    first = _parsed_component()
    second = _parsed_component()
    registry.register(first, ("v", "l", "source", "1"))
    registry.register(second, ("v", "l", "source-copy", "1"))
    ref = first.bus_interfaces.bus_interface[0].choice.address_space_ref
    target = first.address_spaces.address_space[0]

    assert resolve_attribute_reference(get_handle(ref), "addressSpaceRef") == get_handle(target)
    other_target = second.address_spaces.address_space[0]
    assert resolve_attribute_reference(get_handle(ref), "addressSpaceRef") != get_handle(other_target)


def test_duplicate_local_names_are_reported_as_ambiguous_and_missing_target_is_not_found():
    duplicate = (
        "<ipxact:addressSpace><ipxact:name>fabric</ipxact:name><ipxact:range>1</ipxact:range>"
        "<ipxact:width>1</ipxact:width></ipxact:addressSpace>"
    )
    root = _parsed_component(address_spaces=duplicate + duplicate)
    registry.register(root, ("v", "l", "source", "1"))
    ref = root.bus_interfaces.bus_interface[0].choice.address_space_ref
    with pytest.raises(TgiError) as ambiguous:
        resolve_attribute_reference(get_handle(ref), "addressSpaceRef")
    assert ambiguous.value.fault_code == TgiFaultCode.INVALID_ARGUMENT

    missing = root.bus_interfaces.bus_interface[0].choice.address_space_ref
    missing.address_space_ref = "absent"
    with pytest.raises(TgiError) as not_found:
        resolve_attribute_reference(get_handle(missing), "addressSpaceRef")
    assert not_found.value.fault_code == TgiFaultCode.NOT_FOUND


def test_component_instance_bus_port_and_subport_reference_chains():
    leaf = _registered_component("leaf")
    # Another registered component has same-named targets. Resolution follows
    # the componentRef VLNV from the selected instance.
    _registered_component("other")
    design, active, internal = _design()
    instance = design.component_instances.component_instance[0]

    assert resolve_attribute_reference(get_handle(active), "componentInstanceRef") == get_handle(instance)
    assert resolve_attribute_reference(get_handle(active), "busRef") == get_handle(leaf.bus_interfaces.bus_interface[0])
    assert resolve_attribute_reference(get_handle(internal), "portRef") == get_handle(leaf.model.ports.port[0])
    sub_port = internal.sub_port_reference
    # Add a generated SubPortReference below the InternalPortReference.
    sub_port.append(SubPortReference(sub_port_ref="payload"))
    assert resolve_attribute_reference(get_handle(sub_port[0]), "subPortRef") == get_handle(
        leaf.model.ports.port[0].wire_or_transactional_or_structured.sub_ports.sub_port[0]
    )


def test_unregistered_component_references_fail_instead_of_matching_local_names():
    _, active, internal = _design(target_name="unregistered-leaf")
    with pytest.raises(TgiError) as bus_error:
        resolve_attribute_reference(get_handle(active), "busRef")
    assert bus_error.value.fault_code == TgiFaultCode.NOT_FOUND

    with pytest.raises(TgiError) as port_error:
        resolve_attribute_reference(get_handle(internal), "portRef")
    assert port_error.value.fault_code == TgiFaultCode.NOT_FOUND


def test_design_configuration_component_ref_uses_registered_design():
    _registered_component("leaf")
    design, _, _ = _design()
    interface_ref = DesignConfigurationModel.InterconnectionConfiguration.AbstractorInstances.InterfaceRef(
        component_ref="u0", bus_ref="fabric"
    )
    dc = DesignConfiguration(
        vendor="v",
        library="l",
        name="top-config",
        version="1",
        design_ref=LibraryRefType(vendor="v", library="l", name="top", version="1"),
        interconnection_configuration=[
            DesignConfigurationModel.InterconnectionConfiguration(
                interconnection_ref="bus",
                abstractor_instances=[
                    DesignConfigurationModel.InterconnectionConfiguration.AbstractorInstances(
                        interface_ref=[interface_ref]
                    )
                ],
            )
        ],
    )
    registry.register(dc, ("v", "l", "top-config", "1"))

    assert resolve_attribute_reference(get_handle(interface_ref), "componentRef") == get_handle(
        design.component_instances.component_instance[0]
    )
    assert resolve_attribute_reference(get_handle(interface_ref), "busRef") == get_handle(_registered_bus("leaf"))


def test_view_reference_uses_the_view_configuration_instance_context():
    leaf = _registered_component("view-leaf")
    leaf.model.views = Model.Views(view=[Model.Views.View(name="simulation")])
    design, _, _ = _design(target_name="view-leaf")
    view_configuration = DesignConfigurationModel.ViewConfiguration(
        instance_name=InstanceName(value="u0"),
        view=DesignConfigurationModel.ViewConfiguration.View(view_ref="simulation"),
    )
    dc = DesignConfiguration(
        vendor="v",
        library="l",
        name="view-config",
        version="1",
        design_ref=LibraryRefType(vendor="v", library="l", name="top", version="1"),
        view_configuration=[view_configuration],
    )
    registry.register(dc, ("v", "l", "view-config", "1"))

    assert resolve_attribute_reference(get_handle(view_configuration), "viewRef") == get_handle(
        leaf.model.views.view[0]
    )


def _registered_bus(component_name: str):
    component_id = registry.get_id(("v", "l", component_name, "1"))
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import resolve_handle

    return resolve_handle(component_id).bus_interfaces.bus_interface[0]


def test_field_reference_qualifiers_select_the_named_register_and_restore_owner():
    def register(name: str) -> AddressBlockType.Register:
        return AddressBlockType.Register(
            name=name,
            address_offset=UnsignedLongintExpression(value="0"),
            choice=[FieldType(name="shared", bit_offset=UnsignedIntExpression(value="0"))],
        )

    block_a = AddressBlock(
        name="blockA",
        base_address=BaseAddress(value="0"),
        choice=[register("registerA")],
    )
    block_b = AddressBlock(
        name="blockB",
        base_address=BaseAddress(value="0"),
        choice=[register("registerB")],
    )
    field_ref = FieldRef(field_ref="shared")
    indirect_address = IndirectAddressRef(
        address_block_ref=AddressBlockRef(address_block_ref="blockB"),
        register_ref=RegisterRef(register_ref="registerB"),
        field_ref=field_ref,
    )
    root = Component(
        vendor="v",
        library="l",
        name="nested",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block_a, block_b])]),
        indirect_interfaces=IndirectInterfaces(
            indirect_interface=[
                IndirectInterface(
                    name="indirect",
                    indirect_address_ref=indirect_address,
                    indirect_data_ref=IndirectDataRef(field_ref=FieldRef(field_ref="shared")),
                )
            ]
        ),
    )
    registry.register(root, ("v", "l", "nested", "1"))
    expected = block_b.choice[0].choice[0]

    target_id = resolve_attribute_reference(get_handle(field_ref), "fieldRef")
    assert target_id == get_handle(expected)
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_parent_info

    info = get_parent_info(target_id)
    assert info is not None
    assert info.parent_handle == get_handle(block_b.choice[0])
    assert info.path == ("choice",)


def test_memory_remap_schema_spelling_and_segment_scope_follow_reference_chains():
    remap = MemoryRemap(name="remap")
    remap_ref = MemoryRemapRef(memory_remap_ref="remap")
    root = Component(
        vendor="v",
        library="l",
        name="remap-root",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[remap])]),
        indirect_interfaces=IndirectInterfaces(
            indirect_interface=[
                IndirectInterface(
                    name="indirect",
                    indirect_address_ref=IndirectAddressRef(
                        address_space_ref_or_memory_map_ref_or_memory_remap_ref=[remap_ref],
                        field_ref=FieldRef(field_ref="field"),
                    ),
                    indirect_data_ref=IndirectDataRef(field_ref=FieldRef(field_ref="field")),
                )
            ]
        ),
    )
    registry.register(root, ("v", "l", "remap-root", "1"))
    assert resolve_attribute_reference(get_handle(remap_ref), "memoryReMapRef") == get_handle(remap)

    def address_space(name: str) -> AddressSpaces.AddressSpace:
        return AddressSpaces.AddressSpace(
            name=name,
            range=UnsignedPositiveLongintExpression(value="1"),
            width=UnsignedPositiveIntExpression(value="1"),
            segments=AddressSpaces.AddressSpace.Segments(
                segment=[
                    AddressSpaces.AddressSpace.Segments.Segment(
                        name="shared",
                        address_offset=UnsignedLongintExpression(value="0"),
                        range=UnsignedPositiveLongintExpression(value="1"),
                    )
                ]
            ),
        )

    segment_root = Component(
        vendor="v",
        library="l",
        name="segment-root",
        version="1",
        address_spaces=AddressSpaces(address_space=[address_space("spaceA"), address_space("spaceB")]),
        bus_interfaces=BusInterfaces(
            bus_interface=[
                BusInterface(
                    name="initB",
                    bus_type=ConfigurableLibraryRefType(vendor="v", library="l", name="bus", version="1"),
                    choice=BusInterfaceType.Initiator(
                        address_space_ref=BusInterfaceType.Initiator.AddressSpaceRef(address_space_ref="spaceB")
                    ),
                )
            ]
        ),
        memory_maps=MemoryMaps(
            memory_map=[
                MemoryMapType(
                    name="mapping",
                    choice=[
                        SubspaceMap(
                            name="subspace",
                            base_address=SignedLongintExpression(value="0"),
                            initiator_ref="initB",
                            segment_ref="shared",
                        )
                    ],
                )
            ]
        ),
    )
    registry.register(segment_root, ("v", "l", "segment-root", "1"))
    source = segment_root.memory_maps.memory_map[0].choice[0]
    expected = segment_root.address_spaces.address_space[1].segments.segment[0]
    assert resolve_attribute_reference(get_handle(source), "segmentRef") == get_handle(expected)


def test_generated_memory_interface_and_attribute_targets_resolve_by_typed_name():
    address_space_ref = IndirectAddressRef.AddressSpaceRef(address_space_ref="space")
    memory_map_ref = IndirectAddressRef.MemoryMapRef(memory_map_ref="map")
    address_block_ref = AddressBlockRef(address_block_ref="block")
    alternate_register_ref = AlternateRegisterRef(alternate_register_ref="alternate")
    bank_ref = BankRef(bank_ref="bank")
    remap_ref = MemoryRemapRef(memory_remap_ref="remap")
    register_file_ref = RegisterFileRef(register_file_ref="registerFile")
    indirect_refs = [
        ("addressSpaceRef", {"address_space_ref_or_memory_map_ref_or_memory_remap_ref": [address_space_ref]}),
        ("memoryMapRef", {"address_space_ref_or_memory_map_ref_or_memory_remap_ref": [memory_map_ref]}),
        ("addressBlockRef", {"address_block_ref": address_block_ref}),
        ("alternateRegisterRef", {"alternate_register_ref": alternate_register_ref}),
        ("bankRef", {"bank_ref": [bank_ref]}),
        ("memoryRemapRef", {"address_space_ref_or_memory_map_ref_or_memory_remap_ref": [remap_ref]}),
        ("registerFileRef", {"register_file_ref": [register_file_ref]}),
    ]
    indirect_items = []
    for index, (_xml_name, attributes) in enumerate(indirect_refs):
        indirect_items.append(
            IndirectInterface(
                name=f"indirect{index}",
                indirect_address_ref=IndirectAddressRef(
                    field_ref=FieldRef(field_ref="field"),
                    **attributes,
                ),
                indirect_data_ref=IndirectDataRef(field_ref=FieldRef(field_ref="field")),
            )
        )

    reset = Reset(value=UnsignedBitVectorExpression(value="0"), reset_type_ref="warm")
    field = FieldType(
        name="field",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[FieldType.Resets(reset=[reset])],
    )
    register = AddressBlockType.Register(
        name="register",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[field],
        alternate_registers=AlternateRegisters(
            alternate_register=[AlternateRegisters.AlternateRegister(name="alternate")]
        ),
    )
    register_file = RegisterFile(
        name="registerFile",
        address_offset=UnsignedLongintExpression(value="0"),
    )
    block = AddressBlock(
        name="block",
        base_address=BaseAddress(value="0"),
        choice=[register, register_file],
    )
    memory_map = MemoryMapType(
        name="map",
        choice=[
            block,
            Bank(
                name="bank",
                base_address=BaseAddress(value="0"),
                bank_alignment=BankAlignmentType.PARALLEL,
            ),
            MemoryRemap(name="remap"),
        ],
    )
    power_domain_ref = PowerDomainRef(value="domain")
    port = Port(
        name="gpio",
        wire_or_transactional_or_structured=PortWireType(
            direction=ComponentPortDirectionType.IN,
            power_constraints=PortWireType.PowerConstraints(
                power_constraint=[WirePowerConstraintType(power_domain_ref=power_domain_ref)]
            ),
        ),
    )
    parameter = Parameter(name="mode", value=Value(value="a"), choice_ref="selection")
    bridge = TransparentBridge(initiator_ref="initiator")
    target_interface = BusInterface(
        name="target",
        bus_type=ConfigurableLibraryRefType(vendor="v", library="l", name="bus", version="1"),
        choice=BusInterfaceType.Target(memory_map_ref_or_transparent_bridge=[bridge]),
    )
    initiator_interface = BusInterface(
        name="initiator",
        bus_type=ConfigurableLibraryRefType(vendor="v", library="l", name="bus", version="1"),
    )
    component = Component(
        vendor="v",
        library="l",
        name="typed-targets",
        version="1",
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="space",
                    range=UnsignedPositiveLongintExpression(value="1"),
                    width=UnsignedPositiveIntExpression(value="1"),
                )
            ]
        ),
        bus_interfaces=BusInterfaces(bus_interface=[target_interface, initiator_interface]),
        memory_maps=MemoryMaps(memory_map=[memory_map]),
        indirect_interfaces=IndirectInterfaces(indirect_interface=indirect_items),
        power_domains=ComponentType.PowerDomains(power_domain=[ComponentType.PowerDomains.PowerDomain(name="domain")]),
        reset_types=ComponentType.ResetTypes(reset_type=[ComponentType.ResetTypes.ResetType(name="warm")]),
        choices=Choices(choice=[Choices.Choice(name="selection")]),
        parameters=Parameters(parameter=[parameter]),
        model=Model(ports=Model.Ports(port=[port])),
    )
    registry.register(component, ("v", "l", "typed-targets", "1"))

    expected_targets = [
        component.address_spaces.address_space[0],
        memory_map,
        block,
        register.alternate_registers.alternate_register[0],
        memory_map.choice[1],
        memory_map.choice[2],
        register_file,
        initiator_interface,
        component.choices.choice[0],
        component.reset_types.reset_type[0],
        component.power_domains.power_domain[0],
    ]
    source_targets = [
        (address_space_ref, "addressSpaceRef"),
        (memory_map_ref, "memoryMapRef"),
        (address_block_ref, "addressBlockRef"),
        (alternate_register_ref, "alternateRegisterRef"),
        (bank_ref, "bankRef"),
        (remap_ref, "memoryRemapRef"),
        (register_file_ref, "registerFileRef"),
        (bridge, "initiatorRef"),
        (parameter, "choiceRef"),
        (reset, "resetTypeRef"),
        (power_domain_ref, "powerDomainRef"),
    ]
    for (source, xml_name), target in zip(source_targets, expected_targets, strict=True):
        assert resolve_attribute_reference(get_handle(source), xml_name) == get_handle(target)
