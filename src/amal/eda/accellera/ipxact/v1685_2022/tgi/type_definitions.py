"""Type Definitions category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.81) and EXTENDED (F.7.82) functions for the
``typeDefinitions`` document describing reusable type definition collections.

BASE getters validate generated definition and reference handles. Expression
source is preserved, and resolved values use SystemVerilog constant evaluation.
Required references reject missing content; optional collections retain empty
results. Target getters resolve the referenced document or local model object.
EXTENDED mutators raise :class:`TgiError` using
``TgiFaultCode.INVALID_ID`` for unknown handles and
``TgiFaultCode.INVALID_ARGUMENT`` for semantic issues.
"""

from collections.abc import Callable, Sequence
from typing import Protocol, cast

from org.accellera.ipxact.v1685_2022 import (
    AddressBlockDefinitions,
    AddressUnitBits,
    BankDefinitions,
    Choices,
    ComplexBaseExpression,
    ComponentType,
    ConfigurableLibraryRefType,
    EnumeratedValues,
    EnumeratedValueType,
    EnumerationDefinitions,
    ExternalTypeDefinitions,
    FieldAccessPolicyDefinitions,
    FieldDefinitions,
    FieldType,
    MemoryMapDefinitions,
    MemoryRemapDefinitions,
    ModeLinks,
    RegisterDefinitions,
    RegisterFileDefinitions,
    ResetTypeLinks,
    UnsignedBitVectorExpression,
    UnsignedIntExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    ViewLinks,
)
from org.accellera.ipxact.v1685_2022.type_definitions import TypeDefinitions

from ._attribute_references import _reference_name, resolve_attribute_reference
from ._expressions import _constant_source, _integer, _source
from ._library_reference import _set_reference, _xml_vlnv
from ._model import _owned_list_ids
from .address_space import _register_owned_child, _remove_owned
from .choice import addChoiceEnumeration
from .component import _list_attr, _register_graph
from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    resolve_handle,
)
from .instantiation import _registered_reference_target
from .miscellaneous import getExpression
from .port_map import _child, _child_id, _name, _remove_child
from .register_file import _expression, _numeric

__all__ = [
    # BASE (F.7.81)
    "getAddressBlockDefinitionAddressUnitBits",
    "getAddressBlockDefinitionAddressUnitBitsExpression",
    "getAddressBlockDefinitionAddressUnitBitsID",
    "getBankDefinitionAddressUnitBits",
    "getBankDefinitionAddressUnitBitsExpression",
    "getBankDefinitionAddressUnitBitsID",
    "getEnumerationDefinitionEnumeratedValueIDs",
    "getEnumerationDefinitionWidth",
    "getEnumerationDefinitionWidthExpression",
    "getEnumerationDefinitionWidthID",
    "getExternalTypeDefinitionsModeLinksIDs",
    "getExternalTypeDefinitionsResetTypeLinkIDs",
    "getExternalTypeDefinitionsTypeDefinitionsRefByID",
    "getExternalTypeDefinitionsTypeDefinitionsRefByVLNV",
    "getExternalTypeDefinitionsViewLinkIDs",
    "getMemoryRemapDefinitionAddressUnitBits",
    "getMemoryRemapDefinitionAddressUnitBitsExpression",
    "getMemoryRemapDefinitionAddressUnitBitsID",
    "getModeLinkExternalModeReferenceRefByName",
    "getModeLinkExternalModeReferenceID",
    "getModeLinkModeReferenceRefByName",
    "getModeLinkModeReferenceID",
    "getRegisterFileDefinitionAddressUnitBits",
    "getRegisterFileDefinitionAddressUnitBitsExpression",
    "getRegisterFileDefinitionAddressUnitBitsID",
    "getResetTypeLinkExternalResetTypeRefByName",
    "getResetTypeLinkExternalResetTypeReferenceID",
    "getResetTypeLinkResetTypeReferenceRefByName",
    "getResetTypeLinkResetTypeReferenceID",
    "getTypeDefinitionsAddressBlockDefinitionIDs",
    "getTypeDefinitionsBankDefinitionIDs",
    "getTypeDefinitionsChoiceIDs",
    "getTypeDefinitionsEnumerationDefinitionIDs",
    "getTypeDefinitionsExternalTypeDefinitionsIDs",
    "getTypeDefinitionsFieldDefinitionIDs",
    "getTypeDefinitionsMemoryMapDefinitionIDs",
    "getTypeDefinitionsMemoryRemapDefinitionIDs",
    "getTypeDefinitionsModeIDs",
    "getTypeDefinitionsRegisterDefinitionIDs",
    "getTypeDefinitionsRegisterFileDefinitionIDs",
    "getTypeDefinitionsResetTypeIDs",
    "getTypeDefinitionsViewIDs",
    "getViewLinkExternalViewReferenceRefByName",
    "getViewLinkExternalViewReferenceID",
    "getViewLinkViewReferenceRefByID",
    "getViewLinkViewReferenceRefByName",
    "getViewLinkViewReferenceID",
    # EXTENDED (F.7.82)
    "addComponentExternalTypeDefinitions",
    "addEnumerationDefinition",
    "addEnumerationDefinitionEnumeratedValue",
    "addExternalTypeDefinitionsModeLink",
    "addExternalTypeDefinitionsViewLink",
    "addFieldDefinitionsEnumeratedValue",
    "addTypeDefinitionsAddressBlockDefinition",
    "addTypeDefinitionsBankDefinition",
    "addTypeDefinitionsChoice",
    "addTypeDefinitionsEnumerationDefinition",
    "addTypeDefinitionsExternalTypeDefinitions",
    "addTypeDefinitionsFieldAccessPolicyDefinition",
    "addTypeDefinitionsFieldDefinition",
    "addTypeDefinitionsMemoryMapDefinition",
    "addTypeDefinitionsMemoryRemapDefinition",
    "addTypeDefinitionsMode",
    "addTypeDefinitionsRegisterDefinition",
    "addTypeDefinitionsRegisterFileDefinition",
    "addTypeDefinitionsResetType",
    "addTypeDefinitionsView",
    "removeAddressBlockDefinitionAddressUnitBits",
    "removeBankDefinitionAddressUnitBits",
    "removeComponentExternalTypeDefinitions",
    "removeEnumerationDefinitionEnumeratedValue",
    "removeExternalTypeDefinitionsModeLink",
    "removeExternalTypeDefinitionsResetTypeLink",
    "removeExternalTypeDefinitionsViewLink",
    "removeFieldDefinitionEnumerationDefinitionRef",
    "removeFieldDefinitionsEnumeratedValue",
    "removeMemoryRemapDefinitionAddressUnitBits",
    "removeRegisterFileDefinitionAddressUnitBits",
    "removeTypeDefinitionsAddressBlockDefinition",
    "removeTypeDefinitionsBankDefinition",
    "removeTypeDefinitionsChoice",
    "removeTypeDefinitionsEnumerationDefinition",
    "removeTypeDefinitionsExternalTypeDefinitions",
    "removeTypeDefinitionsFieldAccessPolicyDefinition",
    "removeTypeDefinitionsFieldDefinition",
    "removeTypeDefinitionsMemoryMapDefinition",
    "removeTypeDefinitionsMemoryRemapDefinition",
    "removeTypeDefinitionsMode",
    "removeTypeDefinitionsRegisterDefinition",
    "removeTypeDefinitionsRegisterFileDefinition",
    "removeTypeDefinitionsResetType",
    "removeTypeDefinitionsView",
    "setAddressBlockDefinitionAddressUnitBits",
    "setBankDefinitionAddressUnitBits",
    "setEnumerationDefinitionWidth",
    "setExternalTypeDefinitionsTypeDefinitionsRef",
    "setMemoryRemapDefinitionAddressUnitBits",
    "setModeLinkExternalModeReference",
    "setModeLinkModeReference",
    "setRegisterFileDefinitionAddressUnitBits",
    "setResetTypeLinkExternalResetTypeReference",
    "setResetTypeLinkResetTypeReference",
    "setViewLinkExternalViewReference",
    "setViewLinkViewReference",
]


type _UnitDefinition = (
    AddressBlockDefinitions.AddressBlockDefinition
    | BankDefinitions.BankDefinition
    | MemoryRemapDefinitions.MemoryRemapDefinition
    | RegisterFileDefinitions.RegisterFileDefinition
)


# ---------------------------------------------------------------------------
# Helpers (internal)
# ---------------------------------------------------------------------------


def _definition[T](definition_id: str, model_type: type[T]) -> T:
    """Require the generated definition owner before accessing its children."""
    owner = resolve_handle(definition_id)
    if not isinstance(owner, model_type):
        raise TgiError("Invalid type definition handle", TgiFaultCode.INVALID_ID)
    return owner


def _definition_expression_source[T: ComplexBaseExpression](reference_id: str, model_type: type[T]) -> str:
    """Read typed expression source without evaluating it."""
    node = resolve_handle(reference_id)
    if not isinstance(node, model_type) or not isinstance(node.value, str):
        raise TgiError("Invalid definition expression content", TgiFaultCode.INVALID_ID)
    return getExpression(reference_id)


def _definition_expression_value[T: AddressUnitBits | UnsignedPositiveIntExpression](
    reference_id: str, model_type: type[T]
) -> int:
    """Evaluate a typed definition expression within schema and TGI Long bounds."""
    _definition_expression_source(reference_id, model_type)
    node = resolve_handle(reference_id)
    if not isinstance(node, model_type):
        raise TgiError("Invalid definition expression handle", TgiFaultCode.INVALID_ID)
    maximum = (1 << 32) - 1 if isinstance(node, UnsignedPositiveIntExpression) else (1 << 63) - 1
    value = _numeric(node, "definition expression", minimum=1, maximum=maximum)
    assert value is not None
    return value


def _set_definition_unit(owner: _UnitDefinition, source: str) -> bool:
    """Validate an address-unit update before attaching or changing its wrapper."""
    node = _child(owner, "address_unit_bits", AddressUnitBits)
    candidate = node if node is not None else AddressUnitBits()
    value = _expression(source, "addressUnitBits", 1, (1 << 64) - 1, candidate)
    candidate.value = value
    if node is None:
        owner.address_unit_bits = candidate
    _child_id(owner, "address_unit_bits", AddressUnitBits)
    return True


def _definition_list[T](owner: object, attribute: str, model_type: type[T]) -> Sequence[T]:
    """Validate a generated definition list without normalizing tuple storage."""
    children = getattr(owner, attribute)
    if not isinstance(children, (list, tuple)) or any(not isinstance(child, model_type) for child in children):
        raise TgiError("Invalid definition list", TgiFaultCode.INVALID_ID)
    return cast(Sequence[T], children)


def _definition_list_ids[T](owner: object, attribute: str, model_type: type[T]) -> list[str]:
    """Restore immediate and descendant ownership for a typed definition list."""
    children = _definition_list(owner, attribute, model_type)
    for child in children:
        _register_graph(child)
    return _owned_list_ids(owner, children, attribute)


def _definition_new_name(children: Sequence[object], source: str) -> str:
    """Require a normalized XML name distinct from existing definition members."""
    name = _name(source, "Name")
    for child in children:
        current = getattr(child, "name", None)
        if not isinstance(current, str):
            raise TgiError("Invalid definition name content", TgiFaultCode.INVALID_ID)
        try:
            current = _name(current, "Name")
        except TgiError as error:
            raise TgiError("Invalid definition name", TgiFaultCode.INVALID_ID) from error
        if current == name:
            raise TgiError("Duplicate definition name", TgiFaultCode.ALREADY_EXISTS)
    return name


def _enumeration_value_source(source: str, node: UnsignedBitVectorExpression, width: int | None) -> str:
    """Validate unsigned value source and its fit within a known enumeration width."""
    source = _source(source, node, maximum=None)
    value = _integer(source, None, True)
    if width is not None and value is not None and value.bit_length() > width:
        raise TgiError("Enumerated value exceeds enumeration width", TgiFaultCode.INVALID_ARGUMENT)
    return source


def _new_enumerated_value(name: str, source: str, width: int | None) -> EnumeratedValueType:
    """Create a generated enumerated value using shared expression-width validation."""
    value = UnsignedBitVectorExpression()
    value.value = _enumeration_value_source(source, value, width)
    return EnumeratedValueType(name=name, value=value)


def _set_link_reference[T, H](
    owner: object,
    attribute: str,
    model_type: type[T],
    source_attribute: str,
    source: str,
    holder_type: type[H] | None = None,
    member_attribute: str = "",
) -> bool:
    """Update a generated name reference, preserving its node and known local uniqueness."""
    name = _name(source, "Name")
    node = _child(owner, attribute, model_type)
    if holder_type is not None:
        holder = _register_owned_child(owner, holder_type)
        if holder is not None:
            members = _definition_list(holder, member_attribute, type(owner))
            if not any(member is owner for member in members):
                raise TgiError("Link is not in its owning list", TgiFaultCode.INVALID_ID)
            for member in members:
                if member is owner:
                    continue
                peer = getattr(member, attribute)
                if not isinstance(peer, model_type) or not isinstance(getattr(peer, source_attribute), str):
                    raise TgiError("Invalid local link reference content", TgiFaultCode.INVALID_ID)
                try:
                    peer_name = _name(getattr(peer, source_attribute), "Name")
                except TgiError as error:
                    raise TgiError("Invalid local link reference name", TgiFaultCode.INVALID_ID) from error
                if peer_name == name:
                    raise TgiError("Duplicate local link reference", TgiFaultCode.ALREADY_EXISTS)
    if node is None:
        node = model_type(**{source_attribute: name})
        setattr(owner, attribute, node)
        _child(owner, attribute, model_type)
    else:
        setattr(node, source_attribute, name)
    return True


def _remove_definition_collection_member[M, H](
    member_id: str,
    model_type: type[M],
    holder_type: type[H],
    owner_type: type[TypeDefinitions | ExternalTypeDefinitions],
    holder_attribute: str,
    member_attribute: str,
    ids_getter: Callable[[str], list[str]],
    label: str,
) -> bool:
    """Remove an actual typed collection member and prune an empty optional holder."""
    child = _definition(member_id, model_type)
    holder = _register_owned_child(child, holder_type)
    if not isinstance(holder, holder_type):
        raise TgiError(f"{label} has no owning container", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, owner_type)
    if not isinstance(owner, owner_type) or getattr(owner, holder_attribute) is not holder:
        raise TgiError(f"{label} has no matching collection owner", TgiFaultCode.INVALID_ID)
    members = _definition_list(holder, member_attribute, model_type)
    if not any(member is child for member in members):
        raise TgiError(f"{label} is not in its owning list", TgiFaultCode.INVALID_ID)
    ids_getter(get_handle(owner))
    _list_attr(holder, member_attribute)
    result = _remove_owned(member_id, model_type, holder_type, label)
    if not getattr(holder, member_attribute):
        _remove_child(owner, holder_attribute)
    return result


def _definition_unit_source(reference_id: str | None) -> str | None:
    """Read stored address-unit source while retaining malformed strings for repair."""
    if reference_id is None:
        return None
    return _definition_expression_source(reference_id, AddressUnitBits)


def _definition_unit_value(reference_id: str | None) -> int | None:
    """Evaluate positive address units within the schema and TGI Long domains."""
    if reference_id is None:
        return None
    return _definition_expression_value(reference_id, AddressUnitBits)


# ---------------------------------------------------------------------------
# BASE (F.7.81)
# Numeric, collection and reference getters validate generated handles.
# Optional collections return empty lists; required references reject missing
# content. Structure-specific attribute names align with generated schema
# naming (snake_case).
# ---------------------------------------------------------------------------


def getAddressBlockDefinitionAddressUnitBits(addressBlockDefinitionID: str) -> int | None:  # F.7.81.1
    """Return the resolved address-unit value.

    Section: F.7.81.1.

    Args:
        addressBlockDefinitionID: Handle to an addressBlockDefinition element.

    Returns:
        Evaluated positive address units as a TGI Long, or None when absent.
    """
    return _definition_unit_value(getAddressBlockDefinitionAddressUnitBitsID(addressBlockDefinitionID))


def getAddressBlockDefinitionAddressUnitBitsExpression(addressBlockDefinitionID: str) -> str | None:  # F.7.81.2
    """Return the original address-unit expression.

    Section: F.7.81.2.

    Args:
        addressBlockDefinitionID: Handle to an addressBlockDefinition element.

    Returns:
        Stored expression text without evaluation, or None when absent.
    """
    return _definition_unit_source(getAddressBlockDefinitionAddressUnitBitsID(addressBlockDefinitionID))


def getAddressBlockDefinitionAddressUnitBitsID(addressBlockDefinitionID: str) -> str | None:  # F.7.81.3
    """Return the address-unit element handle.

    Section: F.7.81.3.

    Args:
        addressBlockDefinitionID: Handle to an addressBlockDefinition element.

    Returns:
        Handle to the owned addressUnitBits element, or None when absent.
    """
    return _child_id(
        _definition(addressBlockDefinitionID, AddressBlockDefinitions.AddressBlockDefinition),
        "address_unit_bits",
        AddressUnitBits,
    )


def getBankDefinitionAddressUnitBits(bankDefinitionID: str) -> int | None:  # F.7.81.4
    """Return the resolved address-unit value.

    Section: F.7.81.4.

    Args:
        bankDefinitionID: Handle to a bankDefinition element.

    Returns:
        Evaluated positive address units as a TGI Long, or None when absent.
    """
    return _definition_unit_value(getBankDefinitionAddressUnitBitsID(bankDefinitionID))


def getBankDefinitionAddressUnitBitsExpression(bankDefinitionID: str) -> str | None:  # F.7.81.5
    """Return the original address-unit expression.

    Section: F.7.81.5.

    Args:
        bankDefinitionID: Handle to a bankDefinition element.

    Returns:
        Stored expression text without evaluation, or None when absent.
    """
    return _definition_unit_source(getBankDefinitionAddressUnitBitsID(bankDefinitionID))


def getBankDefinitionAddressUnitBitsID(bankDefinitionID: str) -> str | None:  # F.7.81.6
    """Return the address-unit element handle.

    Section: F.7.81.6.

    Args:
        bankDefinitionID: Handle to a bankDefinition element.

    Returns:
        Handle to the owned addressUnitBits element, or None when absent.
    """
    return _child_id(
        _definition(bankDefinitionID, BankDefinitions.BankDefinition), "address_unit_bits", AddressUnitBits
    )


def getEnumerationDefinitionEnumeratedValueIDs(enumerationDefinitionID: str) -> list[str]:  # F.7.81.7
    """Return ordered owned enumerated-value handles.

    Section: F.7.81.7.

    Args:
        enumerationDefinitionID: Handle to an enumerationDefinition element.

    Returns:
        Ordered handles to enumerated values, including their value descendants.
    """
    owner = _definition(enumerationDefinitionID, EnumerationDefinitions.EnumerationDefinition)
    # Enumeration definition schema has direct enumerated_value list
    return _definition_list_ids(owner, "enumerated_value", EnumeratedValueType)


def getEnumerationDefinitionWidth(enumerationDefinitionID: str) -> int:  # F.7.81.8
    """Return the resolved enumeration width.

    Section: F.7.81.8.

    Args:
        enumerationDefinitionID: Handle to an enumerationDefinition element.

    Returns:
        Evaluated positive 32-bit enumeration width as a TGI Long.
    """
    return _definition_expression_value(
        getEnumerationDefinitionWidthID(enumerationDefinitionID), UnsignedPositiveIntExpression
    )


def getEnumerationDefinitionWidthExpression(enumerationDefinitionID: str) -> str:  # F.7.81.9
    """Return the original enumeration-width expression.

    Section: F.7.81.9.

    Args:
        enumerationDefinitionID: Handle to an enumerationDefinition element.

    Returns:
        Stored width expression text without evaluation.
    """
    # UnsignedPositiveIntExpression stores expression source in its value.
    return _definition_expression_source(
        getEnumerationDefinitionWidthID(enumerationDefinitionID), UnsignedPositiveIntExpression
    )


def getEnumerationDefinitionWidthID(enumerationDefinitionID: str) -> str:  # F.7.81.10
    """Return the required enumeration-width element handle.

    Section: F.7.81.10.

    Args:
        enumerationDefinitionID: Handle to an enumerationDefinition element.

    Returns:
        Handle to the owned required width element.
    """
    owner = _definition(enumerationDefinitionID, EnumerationDefinitions.EnumerationDefinition)
    child_id = _child_id(owner, "width", UnsignedPositiveIntExpression)
    if child_id is None:
        raise TgiError("Missing enumerationDefinition width", TgiFaultCode.INVALID_ID)
    return child_id


def getExternalTypeDefinitionsModeLinksIDs(externalTypeDefinitionsID: str) -> list[str]:  # F.7.81.11
    """Return ordered owned mode-link handles.

    Section: F.7.81.11.

    Args:
        externalTypeDefinitionsID: Handle to an externalTypeDefinitions element.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    container = _child(owner, "mode_links", ModeLinks)
    if container is None:
        return []
    return _definition_list_ids(container, "mode_link", ModeLinks.ModeLink)


def getExternalTypeDefinitionsResetTypeLinkIDs(externalTypeDefinitionsID: str) -> list[str]:  # F.7.81.12
    """Return ordered owned reset-type-link handles.

    Section: F.7.81.12.

    Args:
        externalTypeDefinitionsID: Handle to an externalTypeDefinitions element.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    container = _child(owner, "reset_type_links", ResetTypeLinks)
    if container is None:
        return []
    return _definition_list_ids(container, "reset_type_link", ResetTypeLinks.ResetTypeLink)


def getExternalTypeDefinitionsTypeDefinitionsRefByID(externalTypeDefinitionsID: str) -> str:  # F.7.81.13
    """Return the registered Type definitions document referenced by VLNV.

    Section: F.7.81.13.

    Args:
        externalTypeDefinitionsID: Handle to an externalTypeDefinitions element.

    Returns:
        Referenced 1685-2022 document handle; unavailable or wrong-kind targets raise NOT_FOUND.
    """
    getExternalTypeDefinitionsTypeDefinitionsRefByVLNV(externalTypeDefinitionsID)
    owner = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    try:
        target = _registered_reference_target(owner.type_definitions_ref, TypeDefinitions, "typeDefinitionsRef")
    except TgiError as error:
        if error.fault_code == TgiFaultCode.INVALID_ID:
            raise TgiError("Referenced document edition is unsupported", TgiFaultCode.NOT_FOUND) from error
        raise
    return get_handle(target)


def getExternalTypeDefinitionsTypeDefinitionsRefByVLNV(
    externalTypeDefinitionsID: str,
) -> tuple[str, str, str, str]:  # F.7.81.14
    """Return the complete stored VLNV of the required external document reference.

    Section: F.7.81.14.

    Args:
        externalTypeDefinitionsID: Handle to an externalTypeDefinitions element.

    Returns:
        Validated vendor, library, name and version strings, without target lookup.
    """
    owner = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    reference = _child(owner, "type_definitions_ref", ConfigurableLibraryRefType)
    if reference is None:
        raise TgiError("Missing required typeDefinitionsRef", TgiFaultCode.INVALID_ID)
    try:
        return _xml_vlnv((reference.vendor, reference.library, reference.name, reference.version))
    except TgiError as error:
        raise TgiError("Invalid typeDefinitionsRef VLNV", TgiFaultCode.INVALID_ID) from error


def getExternalTypeDefinitionsViewLinkIDs(externalTypeDefinitionsID: str) -> list[str]:  # F.7.81.15
    """Return ordered owned view-link handles.

    Section: F.7.81.15.

    Args:
        externalTypeDefinitionsID: Handle to an externalTypeDefinitions element.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    container = _child(owner, "view_links", ViewLinks)
    if container is None:
        return []
    return _definition_list_ids(container, "view_link", ViewLinks.ViewLink)


def getMemoryRemapDefinitionAddressUnitBits(memoryRemapDefinitionID: str) -> int | None:  # F.7.81.16
    """Return the resolved address-unit value.

    Section: F.7.81.16.

    Args:
        memoryRemapDefinitionID: Handle to a memoryRemapDefinition element.

    Returns:
        Evaluated positive address units as a TGI Long, or None when absent.
    """
    return _definition_unit_value(getMemoryRemapDefinitionAddressUnitBitsID(memoryRemapDefinitionID))


def getMemoryRemapDefinitionAddressUnitBitsExpression(memoryRemapDefinitionID: str) -> str | None:  # F.7.81.17
    """Return the original address-unit expression.

    Section: F.7.81.17.

    Args:
        memoryRemapDefinitionID: Handle to a memoryRemapDefinition element.

    Returns:
        Stored expression text without evaluation, or None when absent.
    """
    return _definition_unit_source(getMemoryRemapDefinitionAddressUnitBitsID(memoryRemapDefinitionID))


def getMemoryRemapDefinitionAddressUnitBitsID(memoryRemapDefinitionID: str) -> str | None:  # F.7.81.18
    """Return the address-unit element handle.

    Section: F.7.81.18.

    Args:
        memoryRemapDefinitionID: Handle to a memoryRemapDefinition element.

    Returns:
        Handle to the owned addressUnitBits element, or None when absent.
    """
    return _child_id(
        _definition(memoryRemapDefinitionID, MemoryRemapDefinitions.MemoryRemapDefinition),
        "address_unit_bits",
        AddressUnitBits,
    )


def getModeLinkExternalModeReferenceRefByName(modeLinkID: str) -> str:  # F.7.81.19
    """Return the referenced XML name.

    Section: F.7.81.19.

    Args:
        modeLinkID: Handle to a modeLink element.

    Returns:
        Normalized XML name of the referenced mode or reset type, without source mutation.
    """
    return _reference_name(getModeLinkExternalModeReferenceID(modeLinkID), "modeRef")


def getModeLinkExternalModeReferenceID(modeLinkID: str) -> str:  # F.7.81.20
    """Return the reference element handle.

    Section: F.7.81.20.

    Args:
        modeLinkID: Handle to a modeLink element.

    Returns:
        Owned handle to the required reference element; typed source remains accessible for repair.
    """
    reference_id = _child_id(
        _definition(modeLinkID, ModeLinks.ModeLink), "external_mode_reference", ModeLinks.ModeLink.ExternalModeReference
    )
    if reference_id is None:
        raise TgiError("Missing required external_mode_reference reference", TgiFaultCode.INVALID_ID)
    return reference_id


def getModeLinkModeReferenceRefByName(modeLinkID: str) -> str:  # F.7.81.21
    """Return the referenced XML name.

    Section: F.7.81.21.

    Args:
        modeLinkID: Handle to a modeLink element.

    Returns:
        Normalized XML name of the referenced mode or reset type, without source mutation.
    """
    return _reference_name(getModeLinkModeReferenceID(modeLinkID), "modeRef")


def getModeLinkModeReferenceID(modeLinkID: str) -> str:  # F.7.81.22
    """Return the reference element handle.

    Section: F.7.81.22.

    Args:
        modeLinkID: Handle to a modeLink element.

    Returns:
        Owned handle to the required reference element; typed source remains accessible for repair.
    """
    reference_id = _child_id(
        _definition(modeLinkID, ModeLinks.ModeLink), "mode_reference", ModeLinks.ModeLink.ModeReference
    )
    if reference_id is None:
        raise TgiError("Missing required mode_reference reference", TgiFaultCode.INVALID_ID)
    return reference_id


def getRegisterFileDefinitionAddressUnitBits(registerFileDefinitionID: str) -> int | None:  # F.7.81.23
    """Return the resolved address-unit value.

    Section: F.7.81.23.

    Args:
        registerFileDefinitionID: Handle to a registerFileDefinition element.

    Returns:
        Evaluated positive address units as a TGI Long, or None when absent.
    """
    return _definition_unit_value(getRegisterFileDefinitionAddressUnitBitsID(registerFileDefinitionID))


def getRegisterFileDefinitionAddressUnitBitsExpression(registerFileDefinitionID: str) -> str | None:  # F.7.81.24
    """Return the original address-unit expression.

    Section: F.7.81.24.

    Args:
        registerFileDefinitionID: Handle to a registerFileDefinition element.

    Returns:
        Stored expression text without evaluation, or None when absent.
    """
    return _definition_unit_source(getRegisterFileDefinitionAddressUnitBitsID(registerFileDefinitionID))


def getRegisterFileDefinitionAddressUnitBitsID(registerFileDefinitionID: str) -> str | None:  # F.7.81.25
    """Return the address-unit element handle.

    Section: F.7.81.25.

    Args:
        registerFileDefinitionID: Handle to a registerFileDefinition element.

    Returns:
        Handle to the owned addressUnitBits element, or None when absent.
    """
    return _child_id(
        _definition(registerFileDefinitionID, RegisterFileDefinitions.RegisterFileDefinition),
        "address_unit_bits",
        AddressUnitBits,
    )


def getResetTypeLinkExternalResetTypeRefByName(resetTypeLinkID: str) -> str:  # F.7.81.26
    """Return the referenced XML name.

    Section: F.7.81.26.

    Args:
        resetTypeLinkID: Handle to a resetTypeLink element.

    Returns:
        Normalized XML name of the referenced mode or reset type, without source mutation.
    """
    return _reference_name(getResetTypeLinkExternalResetTypeReferenceID(resetTypeLinkID), "resetTypeRef")


def getResetTypeLinkExternalResetTypeReferenceID(resetTypeLinkID: str) -> str:  # F.7.81.27
    """Return the reference element handle.

    Section: F.7.81.27.

    Args:
        resetTypeLinkID: Handle to a resetTypeLink element.

    Returns:
        Owned handle to the required reference element; typed source remains accessible for repair.
    """
    reference_id = _child_id(
        _definition(resetTypeLinkID, ResetTypeLinks.ResetTypeLink),
        "external_reset_type_reference",
        ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference,
    )
    if reference_id is None:
        raise TgiError("Missing required external_reset_type_reference reference", TgiFaultCode.INVALID_ID)
    return reference_id


def getResetTypeLinkResetTypeReferenceRefByName(resetTypeLinkID: str) -> str:  # F.7.81.28
    """Return the referenced XML name.

    Section: F.7.81.28.

    Args:
        resetTypeLinkID: Handle to a resetTypeLink element.

    Returns:
        Normalized XML name of the referenced mode or reset type, without source mutation.
    """
    return _reference_name(getResetTypeLinkResetTypeReferenceID(resetTypeLinkID), "resetTypeRef")


def getResetTypeLinkResetTypeReferenceID(resetTypeLinkID: str) -> str:  # F.7.81.29
    """Return the reference element handle.

    Section: F.7.81.29.

    Args:
        resetTypeLinkID: Handle to a resetTypeLink element.

    Returns:
        Owned handle to the required reference element; typed source remains accessible for repair.
    """
    reference_id = _child_id(
        _definition(resetTypeLinkID, ResetTypeLinks.ResetTypeLink),
        "reset_type_reference",
        ResetTypeLinks.ResetTypeLink.ResetTypeReference,
    )
    if reference_id is None:
        raise TgiError("Missing required reset_type_reference reference", TgiFaultCode.INVALID_ID)
    return reference_id


def getTypeDefinitionsAddressBlockDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.30
    """Return ordered owned address-block-definition handles.

    Section: F.7.81.30.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "address_block_definitions", AddressBlockDefinitions)
    if container is None:
        return []
    return _definition_list_ids(container, "address_block_definition", AddressBlockDefinitions.AddressBlockDefinition)


def getTypeDefinitionsBankDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.31
    """Return ordered owned bank-definition handles.

    Section: F.7.81.31.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "bank_definitions", BankDefinitions)
    if container is None:
        return []
    return _definition_list_ids(container, "bank_definition", BankDefinitions.BankDefinition)


def getTypeDefinitionsChoiceIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.32
    """Return ordered owned choice handles.

    Section: F.7.81.32.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "choices", Choices)
    if container is None:
        return []
    return _definition_list_ids(container, "choice", Choices.Choice)


def getTypeDefinitionsEnumerationDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.33
    """Return ordered owned enumeration-definition handles.

    Section: F.7.81.33.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered definition handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "enumeration_definitions", EnumerationDefinitions)
    if container is None:
        return []
    return _definition_list_ids(container, "enumeration_definition", EnumerationDefinitions.EnumerationDefinition)


def getTypeDefinitionsExternalTypeDefinitionsIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.34
    """Return ordered owned external type-definition handles.

    Section: F.7.81.34.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered external type-definition handles, or an empty list when absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    return _definition_list_ids(owner, "external_type_definitions", ExternalTypeDefinitions)


def getTypeDefinitionsFieldDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.35
    """Return ordered owned field-definition handles.

    Section: F.7.81.35.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "field_definitions", FieldDefinitions)
    if container is None:
        return []
    return _definition_list_ids(container, "field_definition", FieldDefinitions.FieldDefinition)


def getTypeDefinitionsMemoryMapDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.36
    """Return ordered owned memory-map-definition handles.

    Section: F.7.81.36.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "memory_map_definitions", MemoryMapDefinitions)
    if container is None:
        return []
    return _definition_list_ids(container, "memory_map_definition", MemoryMapDefinitions.MemoryMapDefinition)


def getTypeDefinitionsMemoryRemapDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.37
    """Return ordered owned memory-remap-definition handles.

    Section: F.7.81.37.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "memory_remap_definitions", MemoryRemapDefinitions)
    if container is None:
        return []
    return _definition_list_ids(container, "memory_remap_definition", MemoryRemapDefinitions.MemoryRemapDefinition)


def getTypeDefinitionsModeIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.38
    """Return ordered owned mode handles.

    Section: F.7.81.38.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions element.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "modes", TypeDefinitions.Modes)
    if container is None:
        return []
    return _definition_list_ids(container, "mode", TypeDefinitions.Modes.Mode)


def getTypeDefinitionsRegisterDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.39
    """Return ordered owned register-definition handles.

    Section: F.7.81.39.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "register_definitions", RegisterDefinitions)
    if container is None:
        return []
    return _definition_list_ids(container, "register_definition", RegisterDefinitions.RegisterDefinition)


def getTypeDefinitionsRegisterFileDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.40
    """Return ordered owned register-file-definition handles.

    Section: F.7.81.40.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "register_file_definitions", RegisterFileDefinitions)
    if container is None:
        return []
    return _definition_list_ids(container, "register_file_definition", RegisterFileDefinitions.RegisterFileDefinition)


def getTypeDefinitionsResetTypeIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.41
    """Return ordered owned reset-type handles.

    Section: F.7.81.41.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions element.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "reset_types", TypeDefinitions.ResetTypes)
    if container is None:
        return []
    return _definition_list_ids(container, "reset_type", TypeDefinitions.ResetTypes.ResetType)


def getTypeDefinitionsViewIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.42
    """Return ordered owned view handles.

    Section: F.7.81.42.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions element.

    Returns:
        Ordered member handles, or an empty list when the container is absent.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    container = _child(owner, "views", TypeDefinitions.Views)
    if container is None:
        return []
    return _definition_list_ids(container, "view", TypeDefinitions.Views.View)


def getViewLinkExternalViewReferenceRefByName(viewLinkID: str) -> str:  # F.7.81.43
    """Return the referenced view name.

    Section: F.7.81.43.

    Args:
        viewLinkID: Handle to a viewLink element.

    Returns:
        Normalized referenced view name without changing its stored source.
    """
    return _reference_name(getViewLinkExternalViewReferenceID(viewLinkID), "viewRef")


def getViewLinkExternalViewReferenceID(viewLinkID: str) -> str:  # F.7.81.44
    """Return the reference element handle.

    Section: F.7.81.44.

    Args:
        viewLinkID: Handle to a viewLink element.

    Returns:
        Owned handle to the required reference element, including typed source needing repair.
    """
    reference_id = _child_id(
        _definition(viewLinkID, ViewLinks.ViewLink), "external_view_reference", ViewLinks.ViewLink.ExternalViewReference
    )
    if reference_id is None:
        raise TgiError("Missing required external_view_reference reference", TgiFaultCode.INVALID_ID)
    return reference_id


def getViewLinkViewReferenceRefByID(viewLinkID: str) -> str:  # F.7.81.45
    """Return the local view targeted by the required view reference.

    Section: F.7.81.45.

    Args:
        viewLinkID: Handle to a viewLink element.

    Returns:
        Referenced view handle; missing targets raise NOT_FOUND and ambiguity INVALID_ARGUMENT.
    """
    reference_id = getViewLinkViewReferenceID(viewLinkID)
    getViewLinkViewReferenceRefByName(viewLinkID)
    target_id = resolve_attribute_reference(reference_id, "viewRef")
    if target_id is None:
        raise TgiError("Referenced view is absent", TgiFaultCode.NOT_FOUND)
    return target_id


def getViewLinkViewReferenceRefByName(viewLinkID: str) -> str:  # F.7.81.46
    """Return the referenced view name.

    Section: F.7.81.46.

    Args:
        viewLinkID: Handle to a viewLink element.

    Returns:
        Normalized referenced view name without changing its stored source.
    """
    return _reference_name(getViewLinkViewReferenceID(viewLinkID), "viewRef")


def getViewLinkViewReferenceID(viewLinkID: str) -> str:  # F.7.81.47
    """Return the reference element handle.

    Section: F.7.81.47.

    Args:
        viewLinkID: Handle to a viewLink element.

    Returns:
        Owned handle to the required reference element, including typed source needing repair.
    """
    reference_id = _child_id(
        _definition(viewLinkID, ViewLinks.ViewLink), "view_reference", ViewLinks.ViewLink.ViewReference
    )
    if reference_id is None:
        raise TgiError("Missing required view_reference reference", TgiFaultCode.INVALID_ID)
    return reference_id


# ---------------------------------------------------------------------------
# EXTENDED (F.7.82) – addition, removal, set operations
# Each function validates IDs and returns handles or booleans per spec style.
# ---------------------------------------------------------------------------


def _field_policy_ids(type_definitions_id: str) -> list[str]:
    """Traverse the field-access-policy collection omitted from Annex F BASE getters."""
    owner = _definition(type_definitions_id, TypeDefinitions)
    holder = _child(owner, "field_access_policy_definitions", FieldAccessPolicyDefinitions)
    return (
        []
        if holder is None
        else _definition_list_ids(
            holder, "field_access_policy_definition", FieldAccessPolicyDefinitions.FieldAccessPolicyDefinition
        )
    )


class _NamedDefinition(Protocol):
    """Generated named definition members."""

    name: str


def _add_definition_member[M: _NamedDefinition, H](
    type_definitions_id: str,
    child: M,
    holder_type: type[H],
    holder_attribute: str,
    member_attribute: str,
    ids_getter: Callable[[str], list[str]],
) -> str:
    """Append a generated definition after validating its holder and unique XML name."""
    owner = _definition(type_definitions_id, TypeDefinitions)
    ids_getter(type_definitions_id)
    holder = _child(owner, holder_attribute, holder_type)
    children = () if holder is None else _definition_list(holder, member_attribute, type(child))
    name = _definition_new_name(children, child.name)
    child.name = name
    if holder is None:
        holder = holder_type()
        setattr(owner, holder_attribute, holder)
    _list_attr(holder, member_attribute).append(child)
    ids_getter(type_definitions_id)
    return get_handle(child)


def _new_external_definition(name: str, vlnv: tuple[str, str, str, str]) -> ExternalTypeDefinitions:
    """Create a generated external definition with validated source VLNV."""
    name = _name(name, "Name")
    if not isinstance(vlnv, (list, tuple)):
        raise TgiError("vlnv must be a four-part array", TgiFaultCode.INVALID_ARGUMENT)
    parts = _xml_vlnv(vlnv)
    child = ExternalTypeDefinitions(
        name=name,
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=parts[0], library=parts[1], name=parts[2], version=parts[3]
        ),
    )
    setExternalTypeDefinitionsTypeDefinitionsRef(get_handle(child), vlnv)
    return child


def _append_external_definition(
    owner: TypeDefinitions | ComponentType.TypeDefinitions, child: ExternalTypeDefinitions
) -> str:
    """Append a unique external definition to its generated direct list."""
    children = _definition_list(owner, "external_type_definitions", ExternalTypeDefinitions)
    child.name = _definition_new_name(children, child.name)
    _list_attr(owner, "external_type_definitions").append(child)
    _definition_list_ids(owner, "external_type_definitions", ExternalTypeDefinitions)
    return get_handle(child)


def addComponentExternalTypeDefinitions(
    componentID: str, name: str, vlnv: tuple[str, str, str, str]
) -> str:  # F.7.82.1
    """Add a named external definition to a component's generated typeDefinitions holder.

    Section: F.7.82.1.

    Args:
        componentID: Component handle.
        name: Unique external-definition XML name.
        vlnv: Four-part source VLNV.

    Returns:
        Owned external-definition handle.
    """
    owner = _definition(componentID, ComponentType)
    holder = _child(owner, "type_definitions", ComponentType.TypeDefinitions)
    child = _new_external_definition(name, vlnv)
    if holder is None:
        holder = ComponentType.TypeDefinitions()
        owner.type_definitions = holder
        _child(owner, "type_definitions", ComponentType.TypeDefinitions)
    return _append_external_definition(holder, child)


def addEnumerationDefinition(
    typeDefID: str, name: str, enumeratedName: str, enumeratedExpression: str, *, width: str
) -> str:  # F.7.82.2
    """Add an enumeration definition and its first value to a TypeDefinitions document.

    Section: F.7.82.2.

    Clause 9.3 and memoryMap.xsd require an explicit width. Annex F omits that
    input and describes a component location absent from component.xsd.
    This local extension requires keyword-only width and uses the standalone
    TypeDefinitions document specified by clause 9.
    """
    _definition(typeDefID, TypeDefinitions)
    enumerated_name = _name(enumeratedName, "Name")
    width_source = _expression(width, "width", 1, (1 << 32) - 1)
    width_value = _integer(width_source, (1 << 32) - 1, True, minimum=1)
    _enumeration_value_source(enumeratedExpression, UnsignedBitVectorExpression(), width_value)
    definition_id = addTypeDefinitionsEnumerationDefinition(typeDefID, name, width)
    addEnumerationDefinitionEnumeratedValue(definition_id, enumerated_name, enumeratedExpression)
    return definition_id


def addEnumerationDefinitionEnumeratedValue(enumerationDefinitionID: str, name: str, value: str) -> str:  # F.7.82.3
    """Append a named enumerated value after validating its expression and width.

    Section: F.7.82.3.

    Args:
        enumerationDefinitionID: Handle to an enumerationDefinition element.
        name: Unique XML name of the enumerated value.
        value: Unsigned bit-vector expression source.

    Returns:
        Handle to the generated enumerated-value element.
    """
    owner = _definition(enumerationDefinitionID, EnumerationDefinitions.EnumerationDefinition)
    getEnumerationDefinitionEnumeratedValueIDs(enumerationDefinitionID)
    children = _definition_list(owner, "enumerated_value", EnumeratedValueType)
    name = _definition_new_name(children, name)
    width_id = getEnumerationDefinitionWidthID(enumerationDefinitionID)
    width_node = cast(UnsignedPositiveIntExpression, resolve_handle(width_id))
    width_source = _definition_expression_source(width_id, UnsignedPositiveIntExpression)
    _expression(width_source, "width", 1, (1 << 32) - 1, width_node)
    width = _integer(width_source, (1 << 32) - 1, True, minimum=1)
    child = _new_enumerated_value(name, value, width)
    _list_attr(owner, "enumerated_value").append(child)
    getEnumerationDefinitionEnumeratedValueIDs(enumerationDefinitionID)
    return get_handle(child)


def addExternalTypeDefinitionsModeLink(
    externalTypeDefinitionsID: str, externalModeRef: str, modeReference: str
) -> str:  # F.7.82.4
    """Add a generated link with required external and local references.

    Section: F.7.82.4.

    Args:
        externalTypeDefinitionsID: External-definition handle.
        externalModeRef: External mode XML name.
        modeReference: Local mode XML name.

    Returns:
        Owned mode-link handle.
    """
    owner = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    holder = _child(owner, "mode_links", ModeLinks)
    children = () if holder is None else _definition_list(holder, "mode_link", ModeLinks.ModeLink)
    external = _name(externalModeRef, "Name")
    local = _name(modeReference, "Name")
    for peer in children:
        for attribute, source in (("external_mode_reference", external), ("mode_reference", local)):
            reference = _child(
                peer,
                attribute,
                ModeLinks.ModeLink.ExternalModeReference
                if attribute.startswith("external")
                else ModeLinks.ModeLink.ModeReference,
            )
            if reference is None:
                raise TgiError("Missing required link reference", TgiFaultCode.INVALID_ID)
            if _reference_name(get_handle(reference), "modeRef") == source:
                raise TgiError("Duplicate link reference", TgiFaultCode.ALREADY_EXISTS)
    child = ModeLinks.ModeLink(
        external_mode_reference=ModeLinks.ModeLink.ExternalModeReference(mode_ref=external),
        mode_reference=ModeLinks.ModeLink.ModeReference(mode_ref=local),
    )
    setModeLinkExternalModeReference(get_handle(child), external)
    setModeLinkModeReference(get_handle(child), local)
    if holder is None:
        holder = ModeLinks()
        owner.mode_links = holder
    _list_attr(holder, "mode_link").append(child)
    getExternalTypeDefinitionsModeLinksIDs(externalTypeDefinitionsID)
    return get_handle(child)


def addExternalTypeDefinitionsViewLink(
    externalTypeDefinitionsID: str, externalViewRef: str, viewReference: str
) -> str:  # F.7.82.5
    """Add a generated link with required external and local references.

    Section: F.7.82.5.

    Args:
        externalTypeDefinitionsID: External-definition handle.
        externalViewRef: External view XML name.
        viewReference: Local view XML name.

    Returns:
        Owned view-link handle.
    """
    owner = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    holder = _child(owner, "view_links", ViewLinks)
    children = () if holder is None else _definition_list(holder, "view_link", ViewLinks.ViewLink)
    external = _name(externalViewRef, "Name")
    local = _name(viewReference, "Name")
    for peer in children:
        for attribute, source in (("external_view_reference", external), ("view_reference", local)):
            reference = _child(
                peer,
                attribute,
                ViewLinks.ViewLink.ExternalViewReference
                if attribute.startswith("external")
                else ViewLinks.ViewLink.ViewReference,
            )
            if reference is None:
                raise TgiError("Missing required link reference", TgiFaultCode.INVALID_ID)
            if _reference_name(get_handle(reference), "viewRef") == source:
                raise TgiError("Duplicate link reference", TgiFaultCode.ALREADY_EXISTS)
    child = ViewLinks.ViewLink(
        external_view_reference=ViewLinks.ViewLink.ExternalViewReference(view_ref=external),
        view_reference=ViewLinks.ViewLink.ViewReference(view_ref=local),
    )
    setViewLinkExternalViewReference(get_handle(child), external)
    setViewLinkViewReference(get_handle(child), local)
    if holder is None:
        holder = ViewLinks()
        owner.view_links = holder
    _list_attr(holder, "view_link").append(child)
    getExternalTypeDefinitionsViewLinkIDs(externalTypeDefinitionsID)
    return get_handle(child)


_FIELD_ENUM_CHOICE = "enumeration_definition_ref_or_enumerated_value"


def _field_enumeration_members(
    holder: EnumeratedValues,
) -> Sequence[EnumeratedValueType | EnumeratedValues.EnumerationDefinitionRef]:
    """Validate the reference-or-inline-value branch without normalizing tuple storage."""
    values = holder.enumeration_definition_ref_or_enumerated_value
    if not isinstance(values, (list, tuple)) or not (
        all(isinstance(value, EnumeratedValueType) for value in values)
        or (len(values) == 1 and isinstance(values[0], EnumeratedValues.EnumerationDefinitionRef))
    ):
        raise TgiError("Invalid field enumeration choice", TgiFaultCode.INVALID_ID)
    for value in values:
        _register_graph(value)
    _owned_list_ids(holder, values, _FIELD_ENUM_CHOICE)
    return values


def addFieldDefinitionsEnumeratedValue(fieldDefinitionID: str, name: str, expression: str) -> str:  # F.7.82.6
    """Append a generated inline value respecting the field's declared width.

    Section: F.7.82.6.
    """
    owner = _definition(fieldDefinitionID, FieldDefinitions.FieldDefinition)
    holder = _child(owner, "enumerated_values", EnumeratedValues)
    values = () if holder is None else _field_enumeration_members(holder)
    if values and isinstance(values[0], EnumeratedValues.EnumerationDefinitionRef):
        raise TgiError(
            "Inline values cannot coexist with an enumeration definition reference", TgiFaultCode.INVALID_ARGUMENT
        )
    name = _definition_new_name(values, name)
    width = _child(owner, "bit_width", UnsignedPositiveIntExpression)
    if width is None or not isinstance(width.value, str):
        raise TgiError("Invalid field-definition width", TgiFaultCode.INVALID_ID)
    _expression(width.value, "bitWidth", 1, (1 << 32) - 1, width)
    known_width = _integer(width.value, (1 << 32) - 1, True, minimum=1)
    child = _new_enumerated_value(name, expression, known_width)
    if holder is None:
        holder = EnumeratedValues()
        owner.enumerated_values = holder
        _child(owner, "enumerated_values", EnumeratedValues)
    _list_attr(holder, _FIELD_ENUM_CHOICE).append(child)
    _field_enumeration_members(holder)
    return get_handle(child)


def addTypeDefinitionsAddressBlockDefinition(
    typeDefinitionsID: str, name: str, range: str, width: str
) -> str:  # F.7.82.7
    """Add a generated AddressBlock definition with validated constant-expression sources.

    Section: F.7.82.7.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    range_source = _expression(range, "range", 1, (1 << 64) - 1)
    width_source = _expression(width, "width", 1, (1 << 32) - 1)
    child = AddressBlockDefinitions.AddressBlockDefinition(
        name=_name(name, "Name"),
        range=UnsignedPositiveLongintExpression(value=range_source),
        width=UnsignedPositiveIntExpression(value=width_source),
    )
    return _add_definition_member(
        typeDefinitionsID,
        child,
        AddressBlockDefinitions,
        "address_block_definitions",
        "address_block_definition",
        getTypeDefinitionsAddressBlockDefinitionIDs,
    )


def addTypeDefinitionsBankDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.8
    """Add a generated Bank definition with a unique XML name.

    Section: F.7.82.8.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    child = BankDefinitions.BankDefinition(name=_name(name, "Name"))
    return _add_definition_member(
        typeDefinitionsID,
        child,
        BankDefinitions,
        "bank_definitions",
        "bank_definition",
        getTypeDefinitionsBankDefinitionIDs,
    )


def addTypeDefinitionsChoice(typeDefinitionsID: str, name: str, enumerations: Sequence[str]) -> str:  # F.7.82.9
    """Add a generated choice with a nonempty ordered array of constant expressions.

    Section: F.7.82.9.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    if not isinstance(enumerations, (list, tuple)) or not enumerations:
        raise TgiError("enumerations must be a nonempty array", TgiFaultCode.INVALID_ARGUMENT)
    sources = [_constant_source(value) for value in enumerations]
    child = Choices.Choice(name=_name(name, "Name"))
    for source in sources:
        addChoiceEnumeration(get_handle(child), source)
    return _add_definition_member(typeDefinitionsID, child, Choices, "choices", "choice", getTypeDefinitionsChoiceIDs)


def addTypeDefinitionsEnumerationDefinition(typeDefinitionsID: str, name: str, width: str) -> str:  # F.7.82.10
    """Append a generated enumeration definition with a validated width.

    Section: F.7.82.10.

    Args:
        typeDefinitionsID: Handle to a typeDefinitions document.
        name: Unique XML name of the enumeration definition.
        width: Positive unsigned-int width expression source.

    Returns:
        Handle to the definition; add enumerated values to complete its required content.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    getTypeDefinitionsEnumerationDefinitionIDs(typeDefinitionsID)
    container = _child(owner, "enumeration_definitions", EnumerationDefinitions)
    children = (
        ()
        if container is None
        else _definition_list(container, "enumeration_definition", EnumerationDefinitions.EnumerationDefinition)
    )
    name = _definition_new_name(children, name)
    source = _expression(width, "width", 1, (1 << 32) - 1)
    child = EnumerationDefinitions.EnumerationDefinition(name=name, width=UnsignedPositiveIntExpression(value=source))
    setEnumerationDefinitionWidth(get_handle(child), width)
    if container is None:
        container = EnumerationDefinitions()
        owner.enumeration_definitions = container
    _list_attr(container, "enumeration_definition").append(child)
    getTypeDefinitionsEnumerationDefinitionIDs(typeDefinitionsID)
    return get_handle(child)


def addTypeDefinitionsExternalTypeDefinitions(
    typeDefinitionsID: str, name: str, vlnv: tuple[str, str, str, str]
) -> str:  # F.7.82.11
    """Add a generated external definition with a unique name and complete source VLNV.

    Section: F.7.82.11.

    Args:
        typeDefinitionsID: TypeDefinitions document handle.
        name: Unique external-definition XML name.
        vlnv: Four-part source VLNV.

    Returns:
        Owned external-definition handle.
    """
    owner = _definition(typeDefinitionsID, TypeDefinitions)
    child = _new_external_definition(name, vlnv)
    return _append_external_definition(owner, child)


def addTypeDefinitionsFieldAccessPolicyDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.12
    """Add a generated FieldAccessPolicy definition with a unique XML name.

    Section: F.7.82.12.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    child = FieldAccessPolicyDefinitions.FieldAccessPolicyDefinition(name=_name(name, "Name"))
    return _add_definition_member(
        typeDefinitionsID,
        child,
        FieldAccessPolicyDefinitions,
        "field_access_policy_definitions",
        "field_access_policy_definition",
        _field_policy_ids,
    )


def addTypeDefinitionsFieldDefinition(typeDefinitionsID: str, name: str, bitWidth: str) -> str:  # F.7.82.13
    """Add a generated Field definition with validated constant-expression sources.

    Section: F.7.82.13.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    source = _expression(bitWidth, "bitWidth", 1, (1 << 32) - 1)
    child = FieldDefinitions.FieldDefinition(
        name=_name(name, "Name"), bit_width=UnsignedPositiveIntExpression(value=source)
    )
    return _add_definition_member(
        typeDefinitionsID,
        child,
        FieldDefinitions,
        "field_definitions",
        "field_definition",
        getTypeDefinitionsFieldDefinitionIDs,
    )


def addTypeDefinitionsMemoryMapDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.14
    """Add a generated MemoryMap definition with a unique XML name.

    Section: F.7.82.14.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    child = MemoryMapDefinitions.MemoryMapDefinition(name=_name(name, "Name"))
    return _add_definition_member(
        typeDefinitionsID,
        child,
        MemoryMapDefinitions,
        "memory_map_definitions",
        "memory_map_definition",
        getTypeDefinitionsMemoryMapDefinitionIDs,
    )


def addTypeDefinitionsMemoryRemapDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.15
    """Add a generated MemoryRemap definition with a unique XML name.

    Section: F.7.82.15.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    child = MemoryRemapDefinitions.MemoryRemapDefinition(name=_name(name, "Name"))
    return _add_definition_member(
        typeDefinitionsID,
        child,
        MemoryRemapDefinitions,
        "memory_remap_definitions",
        "memory_remap_definition",
        getTypeDefinitionsMemoryRemapDefinitionIDs,
    )


def addTypeDefinitionsMode(typeDefinitionsID: str, name: str) -> str:  # F.7.82.16
    """Add a generated Mode definition with a unique XML name.

    Section: F.7.82.16.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    child = TypeDefinitions.Modes.Mode(name=_name(name, "Name"))
    return _add_definition_member(
        typeDefinitionsID, child, TypeDefinitions.Modes, "modes", "mode", getTypeDefinitionsModeIDs
    )


def addTypeDefinitionsRegisterDefinition(
    typeDefinitionsID: str, name: str, size: str, fieldName: str, fieldOffset: str, fieldWidth: str
) -> str:  # F.7.82.17
    """Add a generated Register definition with validated constant-expression sources.

    Section: F.7.82.17.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    size_source = _expression(size, "size", 1, (1 << 32) - 1)
    offset_source = _expression(fieldOffset, "fieldOffset", 0, (1 << 32) - 1)
    width_source = _expression(fieldWidth, "fieldWidth", 1, (1 << 32) - 1)
    size_value = _integer(size_source, (1 << 32) - 1, True, minimum=1)
    offset_value = _integer(offset_source, (1 << 32) - 1, True)
    width_value = _integer(width_source, (1 << 32) - 1, True, minimum=1)
    if (
        size_value is not None
        and offset_value is not None
        and width_value is not None
        and offset_value + width_value > size_value
    ):
        raise TgiError("Field exceeds register definition size", TgiFaultCode.INVALID_ARGUMENT)
    field = FieldType(
        name=_name(fieldName, "Name"),
        bit_offset=UnsignedIntExpression(value=offset_source),
        choice=[UnsignedPositiveIntExpression(value=width_source)],
    )
    child = RegisterDefinitions.RegisterDefinition(
        name=_name(name, "Name"), size=UnsignedPositiveIntExpression(value=size_source), field_value=[field]
    )
    return _add_definition_member(
        typeDefinitionsID,
        child,
        RegisterDefinitions,
        "register_definitions",
        "register_definition",
        getTypeDefinitionsRegisterDefinitionIDs,
    )


def addTypeDefinitionsRegisterFileDefinition(typeDefinitionsID: str, name: str, range: str) -> str:  # F.7.82.18
    """Add a generated RegisterFile definition with validated constant-expression sources.

    Section: F.7.82.18.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    source = _expression(range, "range", 1, (1 << 64) - 1)
    child = RegisterFileDefinitions.RegisterFileDefinition(
        name=_name(name, "Name"), range=UnsignedPositiveLongintExpression(value=source)
    )
    return _add_definition_member(
        typeDefinitionsID,
        child,
        RegisterFileDefinitions,
        "register_file_definitions",
        "register_file_definition",
        getTypeDefinitionsRegisterFileDefinitionIDs,
    )


def addTypeDefinitionsResetType(typeDefinitionsID: str, name: str) -> str:  # F.7.82.19
    """Add a generated ResetType definition with a unique XML name.

    Section: F.7.82.19.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    child = TypeDefinitions.ResetTypes.ResetType(name=_name(name, "Name"))
    return _add_definition_member(
        typeDefinitionsID,
        child,
        TypeDefinitions.ResetTypes,
        "reset_types",
        "reset_type",
        getTypeDefinitionsResetTypeIDs,
    )


def addTypeDefinitionsView(typeDefinitionsID: str, name: str) -> str:  # F.7.82.20
    """Add a generated View definition with a unique XML name.

    Section: F.7.82.20.
    """
    _definition(typeDefinitionsID, TypeDefinitions)
    child = TypeDefinitions.Views.View(name=_name(name, "Name"))
    return _add_definition_member(
        typeDefinitionsID, child, TypeDefinitions.Views, "views", "view", getTypeDefinitionsViewIDs
    )


def removeAddressBlockDefinitionAddressUnitBits(addressBlockDefinitionID: str) -> bool:  # F.7.82.21
    """Remove the owned address-unit element and invalidate its handle.

    Section: F.7.82.21.

    Args:
        addressBlockDefinitionID: Handle to an addressBlockDefinition element.

    Returns:
        True when removed, or False when the optional element is absent.
    """
    if getAddressBlockDefinitionAddressUnitBitsID(addressBlockDefinitionID) is None:
        return False
    return _remove_child(
        _definition(addressBlockDefinitionID, AddressBlockDefinitions.AddressBlockDefinition), "address_unit_bits"
    )


def removeBankDefinitionAddressUnitBits(bankDefinitionID: str) -> bool:  # F.7.82.22
    """Remove the owned address-unit element and invalidate its handle.

    Section: F.7.82.22.

    Args:
        bankDefinitionID: Handle to a bankDefinition element.

    Returns:
        True when removed, or False when the optional element is absent.
    """
    if getBankDefinitionAddressUnitBitsID(bankDefinitionID) is None:
        return False
    return _remove_child(_definition(bankDefinitionID, BankDefinitions.BankDefinition), "address_unit_bits")


def removeComponentExternalTypeDefinitions(externalTypeDefinitionsID: str) -> bool:  # F.7.82.23
    """Remove an actual component external-definition member and prune its empty holder.

    Section: F.7.82.23.

    Args:
        externalTypeDefinitionsID: Owned component external-definition handle.

    Returns:
        True after removal; the last member prunes the component holder.
    """
    child = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    holder = _register_owned_child(child, ComponentType.TypeDefinitions)
    if not isinstance(holder, ComponentType.TypeDefinitions):
        raise TgiError("External definition has no component typeDefinitions holder", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, ComponentType)
    if not isinstance(owner, ComponentType) or owner.type_definitions is not holder:
        raise TgiError("External definition holder has no component owner", TgiFaultCode.INVALID_ID)
    children = _definition_list(holder, "external_type_definitions", ExternalTypeDefinitions)
    if not any(member is child for member in children):
        raise TgiError("External definition is not in its owning list", TgiFaultCode.INVALID_ID)
    _definition_list_ids(holder, "external_type_definitions", ExternalTypeDefinitions)
    _list_attr(holder, "external_type_definitions")
    result = _remove_owned(
        externalTypeDefinitionsID, ExternalTypeDefinitions, ComponentType.TypeDefinitions, "external definition"
    )
    if not holder.external_type_definitions:
        _remove_child(owner, "type_definitions")
    return result


def removeEnumerationDefinitionEnumeratedValue(enumeratedValueID: str) -> bool:  # F.7.82.24
    """Remove an owned enumerated value and invalidate its subtree.

    Section: F.7.82.24.

    Args:
        enumeratedValueID: Handle to an enumeratedValue in an enumerationDefinition.

    Returns:
        True when the member and its value wrapper are removed.
    """
    child = _definition(enumeratedValueID, EnumeratedValueType)
    owner = _register_owned_child(child, EnumerationDefinitions.EnumerationDefinition)
    if not isinstance(owner, EnumerationDefinitions.EnumerationDefinition):
        raise TgiError("Enumerated value has no enumeration definition owner", TgiFaultCode.INVALID_ID)
    children = _definition_list(owner, "enumerated_value", EnumeratedValueType)
    if not any(member is child for member in children):
        raise TgiError("Enumerated value is not in its owning list", TgiFaultCode.INVALID_ID)
    getEnumerationDefinitionEnumeratedValueIDs(get_handle(owner))
    _list_attr(owner, "enumerated_value")
    return _remove_owned(
        enumeratedValueID, EnumeratedValueType, EnumerationDefinitions.EnumerationDefinition, "enumerated value"
    )


def removeExternalTypeDefinitionsModeLink(modeLinkID: str) -> bool:  # F.7.82.25
    """Remove an owned mode link and invalidate its generated subtree.

    Section: F.7.82.25.

    Args:
        modeLinkID: Handle to a modelink element in externalTypeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        modeLinkID,
        ModeLinks.ModeLink,
        ModeLinks,
        ExternalTypeDefinitions,
        "mode_links",
        "mode_link",
        getExternalTypeDefinitionsModeLinksIDs,
        "mode link",
    )


def removeExternalTypeDefinitionsResetTypeLink(resetTypeLinkID: str) -> bool:  # F.7.82.26
    """Remove an owned reset type link and invalidate its generated subtree.

    Section: F.7.82.26.

    Args:
        resetTypeLinkID: Handle to a resettypelink element in externalTypeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        resetTypeLinkID,
        ResetTypeLinks.ResetTypeLink,
        ResetTypeLinks,
        ExternalTypeDefinitions,
        "reset_type_links",
        "reset_type_link",
        getExternalTypeDefinitionsResetTypeLinkIDs,
        "reset type link",
    )


def removeExternalTypeDefinitionsViewLink(viewLinkID: str) -> bool:  # F.7.82.27
    """Remove an owned view link and invalidate its generated subtree.

    Section: F.7.82.27.

    Args:
        viewLinkID: Handle to a viewlink element in externalTypeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        viewLinkID,
        ViewLinks.ViewLink,
        ViewLinks,
        ExternalTypeDefinitions,
        "view_links",
        "view_link",
        getExternalTypeDefinitionsViewLinkIDs,
        "view link",
    )


def removeFieldDefinitionEnumerationDefinitionRef(fieldDefinitionID: str) -> bool:  # F.7.82.28
    """Remove a field definition's referenced enumeration and prune its empty holder.

    Section: F.7.82.28.
    """
    owner = _definition(fieldDefinitionID, FieldDefinitions.FieldDefinition)
    holder = _child(owner, "enumerated_values", EnumeratedValues)
    if holder is None:
        return False
    values = _field_enumeration_members(holder)
    if not values or not isinstance(values[0], EnumeratedValues.EnumerationDefinitionRef):
        return False
    _list_attr(holder, _FIELD_ENUM_CHOICE)
    result = detach_child_by_handle(get_handle(values[0]))
    _remove_child(owner, "enumerated_values")
    return result


def removeFieldDefinitionsEnumeratedValue(domainTypeDefID: str) -> bool:  # F.7.82.29
    """Remove an actual inline enumerated-value member of a field definition.

    Section: F.7.82.29.

    Annex F and WSDL name the input domainTypeDefID, but domainTypeDef cannot
    contain enumerated values. As the operation description specifies, this
    argument identifies the enumeratedValue to remove from a field definition.
    """
    child = _definition(domainTypeDefID, EnumeratedValueType)
    holder = _register_owned_child(child, EnumeratedValues)
    if not isinstance(holder, EnumeratedValues):
        raise TgiError("Value has no enumeratedValues holder", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, FieldDefinitions.FieldDefinition)
    if not isinstance(owner, FieldDefinitions.FieldDefinition) or owner.enumerated_values is not holder:
        raise TgiError("Value is not owned by a field definition", TgiFaultCode.INVALID_ID)
    values = _field_enumeration_members(holder)
    if not any(value is child for value in values):
        raise TgiError("Value is not in its owning field enumeration", TgiFaultCode.INVALID_ID)
    _list_attr(holder, _FIELD_ENUM_CHOICE)
    result = _remove_owned(domainTypeDefID, EnumeratedValueType, EnumeratedValues, "field enumerated value")
    if not holder.enumeration_definition_ref_or_enumerated_value:
        _remove_child(owner, "enumerated_values")
    return result


def removeMemoryRemapDefinitionAddressUnitBits(memoryRemapDefinitionID: str) -> bool:  # F.7.82.30
    """Remove the owned address-unit element and invalidate its handle.

    Section: F.7.82.30.

    Args:
        memoryRemapDefinitionID: Handle to a memoryRemapDefinition element.

    Returns:
        True when removed, or False when the optional element is absent.
    """
    if getMemoryRemapDefinitionAddressUnitBitsID(memoryRemapDefinitionID) is None:
        return False
    return _remove_child(
        _definition(memoryRemapDefinitionID, MemoryRemapDefinitions.MemoryRemapDefinition), "address_unit_bits"
    )


def removeRegisterFileDefinitionAddressUnitBits(registerFileDefinitionID: str) -> bool:  # F.7.82.31
    """Remove the owned address-unit element and invalidate its handle.

    Section: F.7.82.31.

    Args:
        registerFileDefinitionID: Handle to a registerFileDefinition element.

    Returns:
        True when removed, or False when the optional element is absent.
    """
    if getRegisterFileDefinitionAddressUnitBitsID(registerFileDefinitionID) is None:
        return False
    return _remove_child(
        _definition(registerFileDefinitionID, RegisterFileDefinitions.RegisterFileDefinition), "address_unit_bits"
    )


def removeTypeDefinitionsAddressBlockDefinition(addressBlockDefinitionID: str) -> bool:  # F.7.82.32
    """Remove an owned address block definition and invalidate its generated subtree.

    Section: F.7.82.32.

    Args:
        addressBlockDefinitionID: Handle to a address block definition element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        addressBlockDefinitionID,
        AddressBlockDefinitions.AddressBlockDefinition,
        AddressBlockDefinitions,
        TypeDefinitions,
        "address_block_definitions",
        "address_block_definition",
        getTypeDefinitionsAddressBlockDefinitionIDs,
        "address block definition",
    )


def removeTypeDefinitionsBankDefinition(bankDefinitionID: str) -> bool:  # F.7.82.33
    """Remove an owned bank definition and invalidate its generated subtree.

    Section: F.7.82.33.

    Args:
        bankDefinitionID: Handle to a bank definition element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        bankDefinitionID,
        BankDefinitions.BankDefinition,
        BankDefinitions,
        TypeDefinitions,
        "bank_definitions",
        "bank_definition",
        getTypeDefinitionsBankDefinitionIDs,
        "bank definition",
    )


def removeTypeDefinitionsChoice(choiceID: str) -> bool:  # F.7.82.34
    """Remove an owned choice and invalidate its generated subtree.

    Section: F.7.82.34.

    Args:
        choiceID: Handle to a choice element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        choiceID,
        Choices.Choice,
        Choices,
        TypeDefinitions,
        "choices",
        "choice",
        getTypeDefinitionsChoiceIDs,
        "choice",
    )


def removeTypeDefinitionsEnumerationDefinition(enumerationDefinitionID: str) -> bool:  # F.7.82.35
    """Remove an owned enumeration definition and prune an empty optional container.

    Section: F.7.82.35.

    Args:
        enumerationDefinitionID: Handle to an enumerationDefinition in typeDefinitions.

    Returns:
        True when the definition and its descendants are removed.
    """
    return _remove_definition_collection_member(
        enumerationDefinitionID,
        EnumerationDefinitions.EnumerationDefinition,
        EnumerationDefinitions,
        TypeDefinitions,
        "enumeration_definitions",
        "enumeration_definition",
        getTypeDefinitionsEnumerationDefinitionIDs,
        "enumeration definition",
    )


def removeTypeDefinitionsExternalTypeDefinitions(externalTypeDefinitionsID: str) -> bool:  # F.7.82.36
    """Remove an owned external definition and invalidate its reference/link subtree.

    Section: F.7.82.36.

    Args:
        externalTypeDefinitionsID: Handle to an externalTypeDefinitions element in typeDefinitions.

    Returns:
        True after removal; the direct root list is retained when empty.
    """
    child = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    owner = _register_owned_child(child, TypeDefinitions)
    if not isinstance(owner, TypeDefinitions):
        raise TgiError("External type definition has no typeDefinitions owner", TgiFaultCode.INVALID_ID)
    children = _definition_list(owner, "external_type_definitions", ExternalTypeDefinitions)
    if not any(member is child for member in children):
        raise TgiError("External type definition is not in its owning list", TgiFaultCode.INVALID_ID)
    getTypeDefinitionsExternalTypeDefinitionsIDs(get_handle(owner))
    _list_attr(owner, "external_type_definitions")
    return _remove_owned(
        externalTypeDefinitionsID, ExternalTypeDefinitions, TypeDefinitions, "external type definition"
    )


def removeTypeDefinitionsFieldAccessPolicyDefinition(fieldAccessPolicyDefinitionID: str) -> bool:  # F.7.82.37
    """Remove an owned field-access-policy definition and prune its empty holder.

    Section: F.7.82.37.
    """
    return _remove_definition_collection_member(
        fieldAccessPolicyDefinitionID,
        FieldAccessPolicyDefinitions.FieldAccessPolicyDefinition,
        FieldAccessPolicyDefinitions,
        TypeDefinitions,
        "field_access_policy_definitions",
        "field_access_policy_definition",
        _field_policy_ids,
        "field access policy definition",
    )


def removeTypeDefinitionsFieldDefinition(fieldDefinitionID: str) -> bool:  # F.7.82.38
    """Remove an owned field definition and invalidate its generated subtree.

    Section: F.7.82.38.

    Args:
        fieldDefinitionID: Handle to a field definition element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        fieldDefinitionID,
        FieldDefinitions.FieldDefinition,
        FieldDefinitions,
        TypeDefinitions,
        "field_definitions",
        "field_definition",
        getTypeDefinitionsFieldDefinitionIDs,
        "field definition",
    )


def removeTypeDefinitionsMemoryMapDefinition(memoryMapDefinitionID: str) -> bool:  # F.7.82.39
    """Remove an owned memory map definition and invalidate its generated subtree.

    Section: F.7.82.39.

    Args:
        memoryMapDefinitionID: Handle to a memory map definition element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        memoryMapDefinitionID,
        MemoryMapDefinitions.MemoryMapDefinition,
        MemoryMapDefinitions,
        TypeDefinitions,
        "memory_map_definitions",
        "memory_map_definition",
        getTypeDefinitionsMemoryMapDefinitionIDs,
        "memory map definition",
    )


def removeTypeDefinitionsMemoryRemapDefinition(memoryRemapDefinitionID: str) -> bool:  # F.7.82.40
    """Remove an owned memory remap definition and invalidate its generated subtree.

    Section: F.7.82.40.

    Args:
        memoryRemapDefinitionID: Handle to a memory remap definition element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        memoryRemapDefinitionID,
        MemoryRemapDefinitions.MemoryRemapDefinition,
        MemoryRemapDefinitions,
        TypeDefinitions,
        "memory_remap_definitions",
        "memory_remap_definition",
        getTypeDefinitionsMemoryRemapDefinitionIDs,
        "memory remap definition",
    )


def removeTypeDefinitionsMode(modeID: str) -> bool:  # F.7.82.41
    """Remove an owned mode and invalidate its generated subtree.

    Section: F.7.82.41.

    Args:
        modeID: Handle to a mode element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        modeID,
        TypeDefinitions.Modes.Mode,
        TypeDefinitions.Modes,
        TypeDefinitions,
        "modes",
        "mode",
        getTypeDefinitionsModeIDs,
        "mode",
    )


def removeTypeDefinitionsRegisterDefinition(registerDefinitionID: str) -> bool:  # F.7.82.42
    """Remove an owned register definition and invalidate its generated subtree.

    Section: F.7.82.42.

    Args:
        registerDefinitionID: Handle to a register definition element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        registerDefinitionID,
        RegisterDefinitions.RegisterDefinition,
        RegisterDefinitions,
        TypeDefinitions,
        "register_definitions",
        "register_definition",
        getTypeDefinitionsRegisterDefinitionIDs,
        "register definition",
    )


def removeTypeDefinitionsRegisterFileDefinition(registerFileDefinitionID: str) -> bool:  # F.7.82.43
    """Remove an owned register file definition and invalidate its generated subtree.

    Section: F.7.82.43.

    Args:
        registerFileDefinitionID: Handle to a register file definition element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        registerFileDefinitionID,
        RegisterFileDefinitions.RegisterFileDefinition,
        RegisterFileDefinitions,
        TypeDefinitions,
        "register_file_definitions",
        "register_file_definition",
        getTypeDefinitionsRegisterFileDefinitionIDs,
        "register file definition",
    )


def removeTypeDefinitionsResetType(resetTypeID: str) -> bool:  # F.7.82.44
    """Remove an owned reset type and invalidate its generated subtree.

    Section: F.7.82.44.

    Args:
        resetTypeID: Handle to a reset type element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        resetTypeID,
        TypeDefinitions.ResetTypes.ResetType,
        TypeDefinitions.ResetTypes,
        TypeDefinitions,
        "reset_types",
        "reset_type",
        getTypeDefinitionsResetTypeIDs,
        "reset type",
    )


def removeTypeDefinitionsView(viewID: str) -> bool:  # F.7.82.45
    """Remove an owned view and invalidate its generated subtree.

    Section: F.7.82.45.

    Args:
        viewID: Handle to a view element in typeDefinitions.

    Returns:
        True after removal; the last member also removes its optional holder.
    """
    return _remove_definition_collection_member(
        viewID,
        TypeDefinitions.Views.View,
        TypeDefinitions.Views,
        TypeDefinitions,
        "views",
        "view",
        getTypeDefinitionsViewIDs,
        "view",
    )


def setAddressBlockDefinitionAddressUnitBits(addressBlockDefinitionID: str, addressUnitBits: str) -> bool:  # F.7.82.46
    """Set address-unit expression text while preserving existing metadata.

    Section: F.7.82.46.

    Args:
        addressBlockDefinitionID: Handle to an addressBlockDefinition element.
        addressUnitBits: Positive unsigned-longint expression source.

    Returns:
        True when the expression is assigned; undeclared constants remain deferred.
    """
    return _set_definition_unit(
        _definition(addressBlockDefinitionID, AddressBlockDefinitions.AddressBlockDefinition), addressUnitBits
    )


def setBankDefinitionAddressUnitBits(bankDefinitionID: str, addressUnitBits: str) -> bool:  # F.7.82.47
    """Set address-unit expression text while preserving existing metadata.

    Section: F.7.82.47.

    Args:
        bankDefinitionID: Handle to a bankDefinition element.
        addressUnitBits: Positive unsigned-longint expression source.

    Returns:
        True when the expression is assigned; undeclared constants remain deferred.
    """
    return _set_definition_unit(_definition(bankDefinitionID, BankDefinitions.BankDefinition), addressUnitBits)


def setEnumerationDefinitionWidth(enumerationDefinitionID: str, width: str) -> bool:  # F.7.82.48
    """Update width source while preserving its wrapper and existing value fit.

    Section: F.7.82.48.

    Args:
        enumerationDefinitionID: Handle to an enumerationDefinition element.
        width: Positive unsigned-int width expression source.

    Returns:
        True when assigned; undeclared width or value constants remain deferred.
    """
    width_id = getEnumerationDefinitionWidthID(enumerationDefinitionID)
    node = cast(UnsignedPositiveIntExpression, resolve_handle(width_id))
    source = _expression(width, "width", 1, (1 << 32) - 1, node)
    number = _integer(source, (1 << 32) - 1, True, minimum=1)
    for child_id in getEnumerationDefinitionEnumeratedValueIDs(enumerationDefinitionID):
        child = cast(EnumeratedValueType, resolve_handle(child_id))
        if not isinstance(child.value, UnsignedBitVectorExpression) or not isinstance(child.value.value, str):
            raise TgiError("Invalid enumerated value content", TgiFaultCode.INVALID_ID)
        _enumeration_value_source(child.value.value, child.value, number)
    node.value = source
    return True


def setExternalTypeDefinitionsTypeDefinitionsRef(
    externalTypeDefinitionsID: str,
    typeDefinitionsRef: tuple[str, str, str, str],
) -> bool:  # F.7.82.49
    """Set a complete VLNV while preserving the generated library-reference wrapper.

    Section: F.7.82.49.

    Args:
        externalTypeDefinitionsID: Handle to an externalTypeDefinitions element.
        typeDefinitionsRef: Four XML strings giving vendor, library, name and version.

    Returns:
        True after assignment without requiring the referenced document to be registered.
    """
    owner = _definition(externalTypeDefinitionsID, ExternalTypeDefinitions)
    if not isinstance(typeDefinitionsRef, (list, tuple)):
        raise TgiError("typeDefinitionsRef must be a four-part VLNV array", TgiFaultCode.INVALID_ARGUMENT)
    _set_reference(owner, "type_definitions_ref", ConfigurableLibraryRefType, typeDefinitionsRef)
    getExternalTypeDefinitionsTypeDefinitionsRefByVLNV(externalTypeDefinitionsID)
    return True


def setMemoryRemapDefinitionAddressUnitBits(memoryRemapDefinitionID: str, addressUnitBits: str) -> bool:  # F.7.82.50
    """Set address-unit expression text while preserving existing metadata.

    Section: F.7.82.50.

    Args:
        memoryRemapDefinitionID: Handle to a memoryRemapDefinition element.
        addressUnitBits: Positive unsigned-longint expression source.

    Returns:
        True when the expression is assigned; undeclared constants remain deferred.
    """
    return _set_definition_unit(
        _definition(memoryRemapDefinitionID, MemoryRemapDefinitions.MemoryRemapDefinition), addressUnitBits
    )


def setModeLinkExternalModeReference(modeLinkID: str, modeRef: str) -> bool:  # F.7.82.51
    """Set a named reference while preserving its generated wrapper identity.

    Section: F.7.82.51.

    Args:
        modeLinkID: Handle to a modeLink element.
        modeRef: XML Name source for the reference attribute.

    Returns:
        True after assignment without requiring the external target to be registered.
    """
    return _set_link_reference(
        _definition(modeLinkID, ModeLinks.ModeLink),
        "external_mode_reference",
        ModeLinks.ModeLink.ExternalModeReference,
        "mode_ref",
        modeRef,
    )


def setModeLinkModeReference(modeLinkID: str, modeRef: str) -> bool:  # F.7.82.52
    """Set a named reference while preserving its generated wrapper identity.

    Section: F.7.82.52.

    Args:
        modeLinkID: Handle to a modeLink element.
        modeRef: XML Name source for the reference attribute.

    Returns:
        True after assignment; known duplicate local references are rejected.
    """
    return _set_link_reference(
        _definition(modeLinkID, ModeLinks.ModeLink),
        "mode_reference",
        ModeLinks.ModeLink.ModeReference,
        "mode_ref",
        modeRef,
        ModeLinks,
        "mode_link",
    )


def setRegisterFileDefinitionAddressUnitBits(registerFileDefinitionID: str, addressUnitBits: str) -> bool:  # F.7.82.53
    """Set address-unit expression text while preserving existing metadata.

    Section: F.7.82.53.

    Args:
        registerFileDefinitionID: Handle to a registerFileDefinition element.
        addressUnitBits: Positive unsigned-longint expression source.

    Returns:
        True when the expression is assigned; undeclared constants remain deferred.
    """
    return _set_definition_unit(
        _definition(registerFileDefinitionID, RegisterFileDefinitions.RegisterFileDefinition), addressUnitBits
    )


def setResetTypeLinkExternalResetTypeReference(resetTypeLinkID: str, resetTypeRef: str) -> bool:  # F.7.82.54
    """Set a named reference while preserving its generated wrapper identity.

    Section: F.7.82.54.

    Args:
        resetTypeLinkID: Handle to a resetTypeLink element.
        resetTypeRef: XML Name source for the reference attribute.

    Returns:
        True after assignment without requiring the external target to be registered.
    """
    return _set_link_reference(
        _definition(resetTypeLinkID, ResetTypeLinks.ResetTypeLink),
        "external_reset_type_reference",
        ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference,
        "reset_type_ref",
        resetTypeRef,
    )


def setResetTypeLinkResetTypeReference(resetTypeLinkID: str, resetTypeRef: str) -> bool:  # F.7.82.55
    """Set a named reference while preserving its generated wrapper identity.

    Section: F.7.82.55.

    Args:
        resetTypeLinkID: Handle to a resetTypeLink element.
        resetTypeRef: XML Name source for the reference attribute.

    Returns:
        True after assignment; known duplicate local references are rejected.
    """
    return _set_link_reference(
        _definition(resetTypeLinkID, ResetTypeLinks.ResetTypeLink),
        "reset_type_reference",
        ResetTypeLinks.ResetTypeLink.ResetTypeReference,
        "reset_type_ref",
        resetTypeRef,
        ResetTypeLinks,
        "reset_type_link",
    )


def setViewLinkExternalViewReference(viewLinkID: str, viewRef: str) -> bool:  # F.7.82.56
    """Set a view reference while preserving its generated wrapper identity.

    Section: F.7.82.56.

    Args:
        viewLinkID: Handle to a viewLink element.
        viewRef: XML Name source for the viewRef attribute.

    Returns:
        True after assignment without requiring the external view target to be registered.
    """
    return _set_link_reference(
        _definition(viewLinkID, ViewLinks.ViewLink),
        "external_view_reference",
        ViewLinks.ViewLink.ExternalViewReference,
        "view_ref",
        viewRef,
    )


def setViewLinkViewReference(viewLinkID: str, viewRef: str) -> bool:  # F.7.82.57
    """Set a view reference while preserving its generated wrapper identity.

    Section: F.7.82.57.

    Args:
        viewLinkID: Handle to a viewLink element.
        viewRef: XML Name source for the viewRef attribute.

    Returns:
        True after assignment; known duplicate local view references are rejected.
    """
    return _set_link_reference(
        _definition(viewLinkID, ViewLinks.ViewLink),
        "view_reference",
        ViewLinks.ViewLink.ViewReference,
        "view_ref",
        viewRef,
        ViewLinks,
        "view_link",
    )
