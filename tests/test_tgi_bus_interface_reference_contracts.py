"""Bus-interface references resolve to typed, locally owned IP-XACT targets."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_interface as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.abstraction_definition import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.abstraction_types import AbstractionTypes
from org.accellera.ipxact.v1685_2022.address_spaces import AddressSpaces
from org.accellera.ipxact.v1685_2022.bus_definition import BusDefinition
from org.accellera.ipxact.v1685_2022.bus_interface import BusInterface
from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType
from org.accellera.ipxact.v1685_2022.bus_interfaces import BusInterfaces
from org.accellera.ipxact.v1685_2022.channels import Channels
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType
from org.accellera.ipxact.v1685_2022.memory_map_ref import MemoryMapRef
from org.accellera.ipxact.v1685_2022.memory_map_ref_type import MemoryMapRefType
from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps
from org.accellera.ipxact.v1685_2022.model import Model
from org.accellera.ipxact.v1685_2022.model_type import ModelType
from org.accellera.ipxact.v1685_2022.transparent_bridge import TransparentBridge
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression
from org.accellera.ipxact.v1685_2022.view_ref import ViewRef
from org.accellera.ipxact.v1685_2022.wire import Wire

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_BUS_VLNV = ("acme", "buses", "control", "1.0")
_ABSTRACTION_VLNV = ("acme", "abstractions", "control_rtl", "1.0")


@pytest.fixture(autouse=True)
def clean_registry(monkeypatch):
    """Keep every case's registry entries limited to its top-level documents."""
    registry.clear()
    register = registry.register

    def register_top_level(element, *args, **kwargs):
        assert isinstance(element, (Component, BusDefinition, AbstractionDefinition))
        return register(element, *args, **kwargs)

    monkeypatch.setattr(registry, "register", register_top_level)
    yield
    registry.clear()


def _configurable_ref(vlnv):
    return ConfigurableLibraryRefType(vendor=vlnv[0], library=vlnv[1], name=vlnv[2], version=vlnv[3])


def _abstraction_ref(vlnv=_ABSTRACTION_VLNV, view_name=None):
    abstraction_type = AbstractionTypes.AbstractionType(abstraction_ref=_configurable_ref(vlnv))
    if view_name is not None:
        abstraction_type.view_ref.append(ViewRef(value=view_name))
    return AbstractionTypes(abstraction_type=[abstraction_type])


def _interface(name, choice, *, bus_vlnv=_BUS_VLNV, abstraction_vlnv=None, view_name=None):
    return BusInterface(
        name=name,
        bus_type=_configurable_ref(bus_vlnv),
        abstraction_types=(
            _abstraction_ref(abstraction_vlnv or _ABSTRACTION_VLNV, view_name)
            if abstraction_vlnv is not None or view_name is not None
            else None
        ),
        choice=choice,
    )


def _component(name, interfaces, **fields):
    return Component(
        vendor="acme",
        library="devices",
        name=name,
        version="1.0",
        bus_interfaces=BusInterfaces(bus_interface=interfaces),
        **fields,
    )


def _validated_round_trip(document, root_type):
    xml = XmlDocument.serializer().render(document)
    tree = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(tree), _SCHEMA.error_log
    return XmlDocument.parser().from_string(xml, root_type)


def _register_component(component):
    loaded = _validated_round_trip(component, Component)
    registry.register(loaded, (loaded.vendor, loaded.library, loaded.name, loaded.version))
    return loaded


def _register_bus_definition(vlnv=_BUS_VLNV):
    document = BusDefinition(
        vendor=vlnv[0],
        library=vlnv[1],
        name=vlnv[2],
        version=vlnv[3],
        direct_connection=True,
        is_addressable=True,
    )
    loaded = _validated_round_trip(document, BusDefinition)
    registry.register(loaded, vlnv)
    return loaded


def _register_abstraction_definition(vlnv=_ABSTRACTION_VLNV):
    document = AbstractionDefinition(
        vendor=vlnv[0],
        library=vlnv[1],
        name=vlnv[2],
        version=vlnv[3],
        bus_type=LibraryRefType(vendor=_BUS_VLNV[0], library=_BUS_VLNV[1], name=_BUS_VLNV[2], version=_BUS_VLNV[3]),
        ports=AbstractionDefinition.Ports(
            port=[AbstractionDefinition.Ports.Port(logical_name="data", wire_or_transactional=Wire())]
        ),
    )
    loaded = _validated_round_trip(document, AbstractionDefinition)
    registry.register(loaded, vlnv)
    return loaded


def _basic_initiator():
    return BusInterfaceType.Initiator()


def test_bus_and_abstraction_refs_return_registered_typed_root_handles():
    """Reference getters return top-level definition handles and their VLNVs."""
    bus_definition = _register_bus_definition()
    abstraction_definition = _register_abstraction_definition()
    component = _register_component(
        _component(
            "reference_owner",
            [_interface("master", _basic_initiator(), abstraction_vlnv=_ABSTRACTION_VLNV)],
        )
    )
    interface = component.bus_interfaces.bus_interface[0]
    interface_id = get_handle(interface)
    abstraction_type_id = get_handle(interface.abstraction_types.abstraction_type[0])

    bus_id = api.getBusInterfaceBusTypeRefByID(interface_id)
    abstraction_id = api.getAbstractionTypeAbstractionRefByID(abstraction_type_id)
    assert resolve_handle(bus_id) is bus_definition
    assert resolve_handle(abstraction_id) is abstraction_definition
    assert api.getBusInterfaceBusTypeRefByVLNV(interface_id) == _BUS_VLNV
    assert api.getAbstractionTypeAbstractionRefByVLNV(abstraction_type_id) == _ABSTRACTION_VLNV


@pytest.mark.parametrize("reference_kind", ["bus", "abstraction"])
@pytest.mark.parametrize("target_kind", ["missing", "wrong_type"])
def test_external_definition_refs_reject_missing_and_wrong_target_types(reference_kind, target_kind):
    """Both reference kinds reject unresolved registry entries and wrong root types."""
    interface = _interface(
        "master",
        _basic_initiator(),
        abstraction_vlnv=_ABSTRACTION_VLNV,
    )
    component = _register_component(_component("owner", [interface]))
    interface = component.bus_interfaces.bus_interface[0]
    wrong_vlnv = _BUS_VLNV if reference_kind == "bus" else _ABSTRACTION_VLNV

    if target_kind == "wrong_type":
        wrong_target = _register_component(
            Component(
                vendor=wrong_vlnv[0],
                library=wrong_vlnv[1],
                name=wrong_vlnv[2],
                version=wrong_vlnv[3],
                bus_interfaces=BusInterfaces(bus_interface=[_interface("decoy", _basic_initiator())]),
            )
        )
        assert type(wrong_target) is Component

    with pytest.raises(TgiError) as error:
        if reference_kind == "bus":
            api.getBusInterfaceBusTypeRefByID(get_handle(interface))
        else:
            abstraction_type = interface.abstraction_types.abstraction_type[0]
            api.getAbstractionTypeAbstractionRefByID(get_handle(abstraction_type))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


def test_abstraction_view_refs_resolve_inside_each_owning_component():
    """Equal view names in separate components resolve to distinct local view handles."""
    roots = [
        _register_component(
            _component(
                f"view_owner_{index}",
                [_interface("master", _basic_initiator(), abstraction_vlnv=_ABSTRACTION_VLNV, view_name="rtl")],
                model=Model(views=ModelType.Views(view=[ModelType.Views.View(name="rtl")])),
            )
        )
        for index in range(2)
    ]

    referenced_views = []
    for root in roots:
        interface = root.bus_interfaces.bus_interface[0]
        abstraction_type_id = get_handle(interface.abstraction_types.abstraction_type[0])
        view_ref_id = api.getAbstractionTypeViewRefIDs(abstraction_type_id)[0]
        assert api.getAbstractionTypeViewRefByNames(abstraction_type_id) == ["rtl"]
        referenced_views.append(api.getAbstractionTypeViewRefByID(abstraction_type_id, view_ref_id))
        assert resolve_handle(referenced_views[-1]) is root.model.views.view[0]

    assert referenced_views[0] != referenced_views[1]


def test_channel_local_names_resolve_to_interfaces_in_their_own_component():
    """Channel references are local names and do not cross component roots."""
    roots = []
    for index in range(2):
        refs = [
            Channels.Channel.BusInterfaceRef(local_name="upstream"),
            Channels.Channel.BusInterfaceRef(local_name="downstream"),
        ]
        roots.append(
            _register_component(
                _component(
                    f"channel_owner_{index}",
                    [_interface("upstream", _basic_initiator()), _interface("downstream", _basic_initiator())],
                    channels=Channels(channel=[Channels.Channel(name="link", bus_interface_ref=refs)]),
                )
            )
        )

    resolved_pairs = []
    for root in roots:
        channel_id = get_handle(root.channels.channel[0])
        reference_ids = api.getChannelBusInterfaceRefIDs(channel_id)
        expected = [get_handle(item) for item in root.bus_interfaces.bus_interface]
        resolved = [api.getChannelBusInterfaceRefByID(reference_id) for reference_id in reference_ids]
        assert resolved == expected
        resolved_pairs.append(resolved)

    assert resolved_pairs[0][0] != resolved_pairs[1][0]


def test_address_space_memory_map_and_mode_refs_are_scoped_to_root():
    """Local reference names and mode handles resolve within each component."""
    roots = []
    for index in range(2):
        initiator = _interface(
            "master",
            BusInterfaceType.Initiator(
                address_space_ref=BusInterfaceType.Initiator.AddressSpaceRef(
                    address_space_ref="space",
                    mode_ref=[
                        BusInterfaceType.Initiator.AddressSpaceRef.ModeRef(value="active"),
                        BusInterfaceType.Initiator.AddressSpaceRef.ModeRef(value="sleep"),
                    ],
                )
            ),
        )
        target = _interface(
            "target",
            BusInterfaceType.Target(
                memory_map_ref_or_transparent_bridge=[
                    MemoryMapRef(
                        memory_map_ref="map",
                        mode_ref=[MemoryMapRefType.ModeRef(value="active")],
                    )
                ]
            ),
        )
        roots.append(
            _register_component(
                _component(
                    f"mode_owner_{index}",
                    [initiator, target],
                    modes=ComponentType.Modes(
                        mode=[ComponentType.Modes.Mode(name="active"), ComponentType.Modes.Mode(name="sleep")]
                    ),
                    address_spaces=AddressSpaces(
                        address_space=[
                            AddressSpaces.AddressSpace(
                                name="space",
                                range=UnsignedPositiveLongintExpression(value="256"),
                                width=UnsignedPositiveIntExpression(value="32"),
                            )
                        ]
                    ),
                    memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map")]),
                )
            )
        )

    address_mode_handles = []
    memory_mode_handles = []
    for root in roots:
        initiator, target = root.bus_interfaces.bus_interface
        initiator_id = get_handle(initiator.choice)
        target_id = get_handle(target.choice)
        address_ref_id = api.getInitiatorAddressSpaceRefID(initiator_id)
        memory_ref_id = api.getTargetMemoryMapRefID(target_id)

        assert api.getInitiatorAddressSpaceRefByName(initiator_id) == "space"
        assert api.getTargetMemoryMapRefByName(target_id) == "map"
        assert api.getAddressSpaceRefModeRefByNames(address_ref_id) == ["active", "sleep"]
        assert api.getMemoryMapRefModeRefByNames(memory_ref_id) == ["active"]
        address_mode_handles.append(api.getAddressSpaceRefModeRefByID(address_ref_id, "active"))
        memory_mode_handles.append(api.getMemoryMapRefModeRefByID(memory_ref_id, "active"))
        assert resolve_handle(address_mode_handles[-1]) is root.modes.mode[0]
        assert resolve_handle(memory_mode_handles[-1]) is root.modes.mode[0]

    assert address_mode_handles[0] != address_mode_handles[1]
    assert memory_mode_handles[0] != memory_mode_handles[1]


def test_target_transparent_bridge_handles_preserve_local_initiator_ref():
    """The standard target getter returns bridge records with their local name intact."""
    roots = []
    for index in range(2):
        upstream = _interface("upstream", _basic_initiator())
        downstream = _interface(
            "downstream",
            BusInterfaceType.Target(memory_map_ref_or_transparent_bridge=[TransparentBridge(initiator_ref="upstream")]),
        )
        roots.append(_register_component(_component(f"bridge_owner_{index}", [upstream, downstream])))

    resolved = []
    for root in roots:
        target = root.bus_interfaces.bus_interface[1]
        target_id = api.getBusInterfaceTargetID(get_handle(target))
        bridge_ids = api.getTargetTransparentBridgeIDs(target_id)
        assert len(bridge_ids) == 1
        bridge = resolve_handle(bridge_ids[0])
        assert bridge.initiator_ref == "upstream"
        resolved.append(bridge_ids[0])

    assert resolved[0] != resolved[1]
