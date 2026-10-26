"""Type Definitions category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.81) and EXTENDED (F.7.82) functions for the
``typeDefinitions`` document describing reusable type definition collections.

Address-unit and enumeration-width getters validate generated definition
handles and preserve raw expression source; resolved values use SystemVerilog
constant evaluation. Other
BASE getters retain their existing neutral-value behavior for invalid handles.
EXTENDED mutators raise :class:`TgiError` using
``TgiFaultCode.INVALID_ID`` for unknown handles and
``TgiFaultCode.INVALID_ARGUMENT`` for semantic issues.
"""

from types import SimpleNamespace
from typing import Any, NoReturn, cast

from org.accellera.ipxact.v1685_2022 import (
    AddressBlockDefinitions,
    AddressUnitBits,
    BankDefinitions,
    ComplexBaseExpression,
    EnumerationDefinitions,
    MemoryRemapDefinitions,
    RegisterFileDefinitions,
    UnsignedPositiveIntExpression,
)
from org.accellera.ipxact.v1685_2022.type_definitions import TypeDefinitions

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    register_parent,
    resolve_handle,
)
from .miscellaneous import getExpression
from .port_map import _child, _child_id, _remove_child
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


def _resolve(handle: str) -> Any | None:  # generic resolver
    return resolve_handle(handle)


def _invalid_id() -> NoReturn:  # convenience
    raise TgiError("Invalid ID", TgiFaultCode.INVALID_ID)


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
# Address-unit and enumeration-width getters validate handles; other getters
# retain neutral returns
# for invalid handles. Structure-specific attribute names align with generated
# schema naming (snake_case).
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
    ed = _resolve(enumerationDefinitionID)
    if ed is None:
        return []
    result: list[str] = []
    # Enumeration definition schema has direct enumerated_value list
    for v in getattr(ed, "enumerated_value", []) or []:  # type: ignore[list-item]
        result.append(get_handle(v))
    return result


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
    etd = _resolve(externalTypeDefinitionsID)
    if etd is None:
        return []
    ml = getattr(etd, "mode_links", None)
    return [get_handle(m) for m in getattr(ml, "mode_link", [])] if ml else []


def getExternalTypeDefinitionsResetTypeLinkIDs(externalTypeDefinitionsID: str) -> list[str]:  # F.7.81.12
    etd = _resolve(externalTypeDefinitionsID)
    if etd is None:
        return []
    rl = getattr(etd, "reset_type_links", None)
    return [get_handle(r) for r in getattr(rl, "reset_type_link", [])] if rl else []


def getExternalTypeDefinitionsTypeDefinitionsRefByID(externalTypeDefinitionsID: str) -> str | None:  # F.7.81.13
    etd = _resolve(externalTypeDefinitionsID)
    if etd is None:
        return None
    ref = getattr(etd, "type_definitions_ref", None)
    return get_handle(ref) if ref else None


def getExternalTypeDefinitionsTypeDefinitionsRefByVLNV(
    externalTypeDefinitionsID: str,
) -> tuple[str | None, str | None, str | None, str | None]:  # F.7.81.14
    etd = _resolve(externalTypeDefinitionsID)
    if etd is None:
        return (None, None, None, None)
    ref = getattr(etd, "type_definitions_ref", None)
    if ref is None:
        return (None, None, None, None)
    return (
        getattr(ref, "vendor", None),
        getattr(ref, "library", None),
        getattr(ref, "name", None),
        getattr(ref, "version", None),
    )


def getExternalTypeDefinitionsViewLinkIDs(externalTypeDefinitionsID: str) -> list[str]:  # F.7.81.15
    etd = _resolve(externalTypeDefinitionsID)
    if etd is None:
        return []
    vl = getattr(etd, "view_links", None)
    return [get_handle(v) for v in getattr(vl, "view_link", [])] if vl else []


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


def getModeLinkExternalModeReferenceRefByName(modeLinkID: str) -> str | None:  # F.7.81.19
    ml = _resolve(modeLinkID)
    ext = getattr(ml, "external_mode_reference", None)
    return getattr(ext, "name", None) if ext else None


def getModeLinkExternalModeReferenceID(modeLinkID: str) -> str | None:  # F.7.81.20
    ml = _resolve(modeLinkID)
    ext = getattr(ml, "external_mode_reference", None)
    return get_handle(ext) if ext else None


def getModeLinkModeReferenceRefByName(modeLinkID: str) -> str | None:  # F.7.81.21
    ml = _resolve(modeLinkID)
    ref = getattr(ml, "mode_reference", None)
    return getattr(ref, "name", None) if ref else None


def getModeLinkModeReferenceID(modeLinkID: str) -> str | None:  # F.7.81.22
    ml = _resolve(modeLinkID)
    ref = getattr(ml, "mode_reference", None)
    return get_handle(ref) if ref else None


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


def getResetTypeLinkExternalResetTypeRefByName(resetTypeLinkID: str) -> str | None:  # F.7.81.26
    rtl = _resolve(resetTypeLinkID)
    ext = getattr(rtl, "external_reset_type_reference", None)
    return getattr(ext, "name", None) if ext else None


def getResetTypeLinkExternalResetTypeReferenceID(resetTypeLinkID: str) -> str | None:  # F.7.81.27
    rtl = _resolve(resetTypeLinkID)
    ext = getattr(rtl, "external_reset_type_reference", None)
    return get_handle(ext) if ext else None


def getResetTypeLinkResetTypeReferenceRefByName(resetTypeLinkID: str) -> str | None:  # F.7.81.28
    rtl = _resolve(resetTypeLinkID)
    ref = getattr(rtl, "reset_type_reference", None)
    return getattr(ref, "name", None) if ref else None


def getResetTypeLinkResetTypeReferenceID(resetTypeLinkID: str) -> str | None:  # F.7.81.29
    rtl = _resolve(resetTypeLinkID)
    ref = getattr(rtl, "reset_type_reference", None)
    return get_handle(ref) if ref else None


def getTypeDefinitionsAddressBlockDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.30
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    abd = getattr(td, "address_block_definitions", None)
    return [get_handle(x) for x in getattr(abd, "address_block_definition", [])] if abd else []


def getTypeDefinitionsBankDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.31
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    bd = getattr(td, "bank_definitions", None)
    return [get_handle(x) for x in getattr(bd, "bank_definition", [])] if bd else []


def getTypeDefinitionsChoiceIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.32
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    choices = getattr(td, "choices", None)
    return [get_handle(c) for c in getattr(choices, "choice", [])] if choices else []


def getTypeDefinitionsEnumerationDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.33
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    eds = getattr(td, "enumeration_definitions", None)
    return [get_handle(e) for e in getattr(eds, "enumeration_definition", [])] if eds else []


def getTypeDefinitionsExternalTypeDefinitionsIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.34
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    ext_list = getattr(td, "external_type_definitions", None)
    if not ext_list:
        return []
    return [get_handle(e) for e in ext_list]


def getTypeDefinitionsFieldDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.35
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    fds = getattr(td, "field_definitions", None)
    return [get_handle(f) for f in getattr(fds, "field_definition", [])] if fds else []


def getTypeDefinitionsMemoryMapDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.36
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    mmd = getattr(td, "memory_map_definitions", None)
    return [get_handle(m) for m in getattr(mmd, "memory_map_definition", [])] if mmd else []


def getTypeDefinitionsMemoryRemapDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.37
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    mrd = getattr(td, "memory_remap_definitions", None)
    return [get_handle(m) for m in getattr(mrd, "memory_remap_definition", [])] if mrd else []


def getTypeDefinitionsModeIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.38
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    modes = getattr(td, "modes", None)
    return [get_handle(m) for m in getattr(modes, "mode", [])] if modes else []


def getTypeDefinitionsRegisterDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.39
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    rds = getattr(td, "register_definitions", None)
    return [get_handle(r) for r in getattr(rds, "register_definition", [])] if rds else []


def getTypeDefinitionsRegisterFileDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.40
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    rfds = getattr(td, "register_file_definitions", None)
    return [get_handle(rf) for rf in getattr(rfds, "register_file_definition", [])] if rfds else []


def getTypeDefinitionsResetTypeIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.41
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    rts = getattr(td, "reset_types", None)
    return [get_handle(rt) for rt in getattr(rts, "reset_type", [])] if rts else []


def getTypeDefinitionsViewIDs(typeDefinitionsID: str) -> list[str]:  # F.7.81.42
    td = _resolve(typeDefinitionsID)
    if td is None:
        return []
    views = getattr(td, "views", None)
    return [get_handle(v) for v in getattr(views, "view", [])] if views else []


def getViewLinkExternalViewReferenceRefByName(viewLinkID: str) -> str | None:  # F.7.81.43
    vl = _resolve(viewLinkID)
    ext = getattr(vl, "external_view_reference", None)
    return getattr(ext, "name", None) if ext else None


def getViewLinkExternalViewReferenceID(viewLinkID: str) -> str | None:  # F.7.81.44
    vl = _resolve(viewLinkID)
    ext = getattr(vl, "external_view_reference", None)
    return get_handle(ext) if ext else None


def getViewLinkViewReferenceRefByID(viewLinkID: str) -> str | None:  # F.7.81.45
    vl = _resolve(viewLinkID)
    ref = getattr(vl, "view_reference", None)
    return getattr(ref, "id", None) if ref else None


def getViewLinkViewReferenceRefByName(viewLinkID: str) -> str | None:  # F.7.81.46
    vl = _resolve(viewLinkID)
    ref = getattr(vl, "view_reference", None)
    return getattr(ref, "name", None) if ref else None


def getViewLinkViewReferenceID(viewLinkID: str) -> str | None:  # F.7.81.47
    vl = _resolve(viewLinkID)
    ref = getattr(vl, "view_reference", None)
    return get_handle(ref) if ref else None


# ---------------------------------------------------------------------------
# EXTENDED (F.7.82) – addition, removal, set operations
# Each function validates IDs and returns handles or booleans per spec style.
# ---------------------------------------------------------------------------


def _ensure_td(tdID: str) -> TypeDefinitions:
    td = resolve_handle(tdID)
    if not isinstance(td, TypeDefinitions):  # pragma: no cover - defensive
        _invalid_id()
    return cast(TypeDefinitions, td)


def addComponentExternalTypeDefinitions(componentID: str) -> str:  # F.7.82.1
    comp = _resolve(componentID)
    if comp is None:
        _invalid_id()
    if getattr(comp, "external_type_definitions", None) is None:
        comp.external_type_definitions = []  # type: ignore[attr-defined]
    etd = SimpleNamespace(name=None, type_definitions_ref=None, view_links=None, mode_links=None, reset_type_links=None)
    comp.external_type_definitions.append(etd)  # type: ignore[attr-defined]
    register_parent(etd, comp, ("external_type_definitions",), "list")
    return get_handle(etd)


def addEnumerationDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.2
    td = _ensure_td(typeDefinitionsID)
    if getattr(td, "enumeration_definitions", None) is None:
        td.enumeration_definitions = SimpleNamespace(enumeration_definition=[])  # type: ignore[attr-defined]
    ed = SimpleNamespace(name=name, width=SimpleNamespace(value="0"), enumerated_value=[])
    td.enumeration_definitions.enumeration_definition.append(ed)  # type: ignore[attr-defined]
    register_parent(ed, td, ("enumeration_definitions",), "list")
    return get_handle(ed)


def addEnumerationDefinitionEnumeratedValue(enumerationDefinitionID: str, name: str, value: str) -> str:  # F.7.82.3
    ed = _resolve(enumerationDefinitionID)
    if ed is None:
        _invalid_id()
    if getattr(ed, "enumerated_value", None) is None:
        ed.enumerated_value = []  # type: ignore[attr-defined]
    ev = SimpleNamespace(name=name, value=SimpleNamespace(value=value))
    ed.enumerated_value.append(ev)  # type: ignore[attr-defined]
    register_parent(ev, ed, ("enumerated_value",), "list")
    return get_handle(ev)


def addExternalTypeDefinitionsModeLink(externalTypeDefinitionsID: str, name: str) -> str:  # F.7.82.4
    etd = _resolve(externalTypeDefinitionsID)
    if etd is None:
        _invalid_id()
    if getattr(etd, "mode_links", None) is None:
        etd.mode_links = SimpleNamespace(mode_link=[])  # type: ignore[attr-defined]
    ml = SimpleNamespace(name=name, external_mode_reference=None, mode_reference=None)
    etd.mode_links.mode_link.append(ml)  # type: ignore[attr-defined]
    register_parent(ml, etd, ("mode_links",), "list")
    return get_handle(ml)


def addExternalTypeDefinitionsViewLink(externalTypeDefinitionsID: str, name: str) -> str:  # F.7.82.5
    etd = _resolve(externalTypeDefinitionsID)
    if etd is None:
        _invalid_id()
    if getattr(etd, "view_links", None) is None:
        etd.view_links = SimpleNamespace(view_link=[])  # type: ignore[attr-defined]
    vl = SimpleNamespace(name=name, external_view_reference=None, view_reference=None)
    etd.view_links.view_link.append(vl)  # type: ignore[attr-defined]
    register_parent(vl, etd, ("view_links",), "list")
    return get_handle(vl)


def addFieldDefinitionsEnumeratedValue(fieldDefinitionsID: str, name: str, value: str) -> str:  # F.7.82.6
    fd = _resolve(fieldDefinitionsID)
    if fd is None:
        _invalid_id()
    if getattr(fd, "enumerated_values", None) is None:
        fd.enumerated_values = SimpleNamespace(enumerated_value=[])  # type: ignore[attr-defined]
    ev = SimpleNamespace(name=name, value=SimpleNamespace(value=value))
    fd.enumerated_values.enumerated_value.append(ev)  # type: ignore[attr-defined]
    register_parent(ev, fd, ("enumerated_values",), "list")
    return get_handle(ev)


def addTypeDefinitionsAddressBlockDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.7
    td = _ensure_td(typeDefinitionsID)
    if td.address_block_definitions is None:
        td.address_block_definitions = SimpleNamespace(address_block_definition=[])  # type: ignore[attr-defined]
    abd = SimpleNamespace(name=name)
    td.address_block_definitions.address_block_definition.append(abd)  # type: ignore[attr-defined]
    register_parent(abd, td, ("address_block_definitions",), "list")
    return get_handle(abd)


def addTypeDefinitionsBankDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.8
    td = _ensure_td(typeDefinitionsID)
    if td.bank_definitions is None:
        td.bank_definitions = SimpleNamespace(bank_definition=[])  # type: ignore[attr-defined]
    bd = SimpleNamespace(name=name)
    td.bank_definitions.bank_definition.append(bd)  # type: ignore[attr-defined]
    register_parent(bd, td, ("bank_definitions",), "list")
    return get_handle(bd)


def addTypeDefinitionsChoice(typeDefinitionsID: str, name: str) -> str:  # F.7.82.9
    td = _ensure_td(typeDefinitionsID)
    if td.choices is None:
        td.choices = SimpleNamespace(choice=[])  # type: ignore[attr-defined]
    ch = SimpleNamespace(name=name)
    td.choices.choice.append(ch)  # type: ignore[attr-defined]
    register_parent(ch, td, ("choices",), "list")
    return get_handle(ch)


def addTypeDefinitionsEnumerationDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.10
    return addEnumerationDefinition(typeDefinitionsID, name)


def addTypeDefinitionsExternalTypeDefinitions(typeDefinitionsID: str, name: str) -> str:  # F.7.82.11
    td = _ensure_td(typeDefinitionsID)
    if td.external_type_definitions is None:
        td.external_type_definitions = SimpleNamespace(external_type_definitions=[])  # type: ignore[attr-defined]
    ext = SimpleNamespace(name=name)
    td.external_type_definitions.external_type_definitions.append(ext)  # type: ignore[attr-defined]
    register_parent(ext, td, ("external_type_definitions",), "list")
    return get_handle(ext)


def addTypeDefinitionsFieldAccessPolicyDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.12
    td = _ensure_td(typeDefinitionsID)
    if td.field_access_policy_definitions is None:
        td.field_access_policy_definitions = SimpleNamespace(field_access_policy_definition=[])  # type: ignore[attr-defined]
    fap = SimpleNamespace(name=name)
    td.field_access_policy_definitions.field_access_policy_definition.append(fap)  # type: ignore[attr-defined]
    register_parent(fap, td, ("field_access_policy_definitions",), "list")
    return get_handle(fap)


def addTypeDefinitionsFieldDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.13
    td = _ensure_td(typeDefinitionsID)
    if td.field_definitions is None:
        td.field_definitions = SimpleNamespace(field_definition=[])  # type: ignore[attr-defined]
    fld = SimpleNamespace(name=name)
    td.field_definitions.field_definition.append(fld)  # type: ignore[attr-defined]
    register_parent(fld, td, ("field_definitions",), "list")
    return get_handle(fld)


def addTypeDefinitionsMemoryMapDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.14
    td = _ensure_td(typeDefinitionsID)
    if td.memory_map_definitions is None:
        td.memory_map_definitions = SimpleNamespace(memory_map_definition=[])  # type: ignore[attr-defined]
    mmd = SimpleNamespace(name=name)
    td.memory_map_definitions.memory_map_definition.append(mmd)  # type: ignore[attr-defined]
    register_parent(mmd, td, ("memory_map_definitions",), "list")
    return get_handle(mmd)


def addTypeDefinitionsMemoryRemapDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.15
    td = _ensure_td(typeDefinitionsID)
    if td.memory_remap_definitions is None:
        td.memory_remap_definitions = SimpleNamespace(memory_remap_definition=[])  # type: ignore[attr-defined]
    mrd = SimpleNamespace(name=name)
    td.memory_remap_definitions.memory_remap_definition.append(mrd)  # type: ignore[attr-defined]
    register_parent(mrd, td, ("memory_remap_definitions",), "list")
    return get_handle(mrd)


def addTypeDefinitionsMode(typeDefinitionsID: str, name: str) -> str:  # F.7.82.16
    td = _ensure_td(typeDefinitionsID)
    if td.modes is None:
        td.modes = SimpleNamespace(mode=[])  # type: ignore[attr-defined]
    mode = SimpleNamespace(name=name)
    td.modes.mode.append(mode)  # type: ignore[attr-defined]
    register_parent(mode, td, ("modes",), "list")
    return get_handle(mode)


def addTypeDefinitionsRegisterDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.17
    td = _ensure_td(typeDefinitionsID)
    if td.register_definitions is None:
        td.register_definitions = SimpleNamespace(register_definition=[])  # type: ignore[attr-defined]
    reg = SimpleNamespace(name=name)
    td.register_definitions.register_definition.append(reg)  # type: ignore[attr-defined]
    register_parent(reg, td, ("register_definitions",), "list")
    return get_handle(reg)


def addTypeDefinitionsRegisterFileDefinition(typeDefinitionsID: str, name: str) -> str:  # F.7.82.18
    td = _ensure_td(typeDefinitionsID)
    if td.register_file_definitions is None:
        td.register_file_definitions = SimpleNamespace(register_file_definition=[])  # type: ignore[attr-defined]
    rfd = SimpleNamespace(name=name)
    td.register_file_definitions.register_file_definition.append(rfd)  # type: ignore[attr-defined]
    register_parent(rfd, td, ("register_file_definitions",), "list")
    return get_handle(rfd)


def addTypeDefinitionsResetType(typeDefinitionsID: str, name: str) -> str:  # F.7.82.19
    td = _ensure_td(typeDefinitionsID)
    if td.reset_types is None:
        td.reset_types = SimpleNamespace(reset_type=[])  # type: ignore[attr-defined]
    rt = SimpleNamespace(name=name)
    td.reset_types.reset_type.append(rt)  # type: ignore[attr-defined]
    register_parent(rt, td, ("reset_types",), "list")
    return get_handle(rt)


def addTypeDefinitionsView(typeDefinitionsID: str, name: str) -> str:  # F.7.82.20
    td = _ensure_td(typeDefinitionsID)
    if td.views is None:
        td.views = SimpleNamespace(view=[])  # type: ignore[attr-defined]
    view = SimpleNamespace(name=name)
    td.views.view.append(view)  # type: ignore[attr-defined]
    register_parent(view, td, ("views",), "list")
    return get_handle(view)


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


def removeComponentExternalTypeDefinitions(componentID: str) -> bool:  # F.7.82.23
    comp = _resolve(componentID)
    if comp is None:
        _invalid_id()
    if getattr(comp, "external_type_definitions", None) is None:
        return False
    comp.external_type_definitions = None  # type: ignore[attr-defined]
    return True


def removeEnumerationDefinitionEnumeratedValue(enumeratedValueID: str) -> bool:  # F.7.82.24
    return detach_child_by_handle(enumeratedValueID)


def removeExternalTypeDefinitionsModeLink(modeLinkID: str) -> bool:  # F.7.82.25
    return detach_child_by_handle(modeLinkID)


def removeExternalTypeDefinitionsResetTypeLink(resetTypeLinkID: str) -> bool:  # F.7.82.26
    return detach_child_by_handle(resetTypeLinkID)


def removeExternalTypeDefinitionsViewLink(viewLinkID: str) -> bool:  # F.7.82.27
    return detach_child_by_handle(viewLinkID)


def removeFieldDefinitionEnumerationDefinitionRef(fieldDefinitionID: str) -> bool:  # F.7.82.28
    fd = _resolve(fieldDefinitionID)
    if fd is None:
        _invalid_id()
    if getattr(fd, "enumeration_definition_ref", None) is None:
        return False
    fd.enumeration_definition_ref = None  # type: ignore[attr-defined]
    return True


def removeFieldDefinitionsEnumeratedValue(enumeratedValueID: str) -> bool:  # F.7.82.29
    return detach_child_by_handle(enumeratedValueID)


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
    return detach_child_by_handle(addressBlockDefinitionID)


def removeTypeDefinitionsBankDefinition(bankDefinitionID: str) -> bool:  # F.7.82.33
    return detach_child_by_handle(bankDefinitionID)


def removeTypeDefinitionsChoice(choiceID: str) -> bool:  # F.7.82.34
    return detach_child_by_handle(choiceID)


def removeTypeDefinitionsEnumerationDefinition(enumerationDefinitionID: str) -> bool:  # F.7.82.35
    return detach_child_by_handle(enumerationDefinitionID)


def removeTypeDefinitionsExternalTypeDefinitions(externalTypeDefinitionsID: str) -> bool:  # F.7.82.36
    return detach_child_by_handle(externalTypeDefinitionsID)


def removeTypeDefinitionsFieldAccessPolicyDefinition(fieldAccessPolicyDefinitionID: str) -> bool:  # F.7.82.37
    return detach_child_by_handle(fieldAccessPolicyDefinitionID)


def removeTypeDefinitionsFieldDefinition(fieldDefinitionID: str) -> bool:  # F.7.82.38
    return detach_child_by_handle(fieldDefinitionID)


def removeTypeDefinitionsMemoryMapDefinition(memoryMapDefinitionID: str) -> bool:  # F.7.82.39
    return detach_child_by_handle(memoryMapDefinitionID)


def removeTypeDefinitionsMemoryRemapDefinition(memoryRemapDefinitionID: str) -> bool:  # F.7.82.40
    return detach_child_by_handle(memoryRemapDefinitionID)


def removeTypeDefinitionsMode(modeID: str) -> bool:  # F.7.82.41
    return detach_child_by_handle(modeID)


def removeTypeDefinitionsRegisterDefinition(registerDefinitionID: str) -> bool:  # F.7.82.42
    return detach_child_by_handle(registerDefinitionID)


def removeTypeDefinitionsRegisterFileDefinition(registerFileDefinitionID: str) -> bool:  # F.7.82.43
    return detach_child_by_handle(registerFileDefinitionID)


def removeTypeDefinitionsResetType(resetTypeID: str) -> bool:  # F.7.82.44
    return detach_child_by_handle(resetTypeID)


def removeTypeDefinitionsView(viewID: str) -> bool:  # F.7.82.45
    return detach_child_by_handle(viewID)


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


def setEnumerationDefinitionWidth(enumerationDefinitionID: str, value: int | str) -> bool:  # F.7.82.48
    ed = _resolve(enumerationDefinitionID)
    if ed is None:
        _invalid_id()
    node = getattr(ed, "width", None)
    if node is None:
        ed.width = SimpleNamespace(value=SimpleNamespace(value=value))  # type: ignore[attr-defined]
    else:
        node.value = SimpleNamespace(value=value)  # type: ignore[attr-defined]
    return True


def setExternalTypeDefinitionsTypeDefinitionsRef(
    externalTypeDefinitionsID: str,
    vlnv: tuple[str, str, str, str],
) -> bool:  # F.7.82.49
    etd = _resolve(externalTypeDefinitionsID)
    if etd is None:
        _invalid_id()
    etd.type_definitions_ref = SimpleNamespace(  # type: ignore[attr-defined]
        vendor=vlnv[0], library=vlnv[1], name=vlnv[2], version=vlnv[3]
    )
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


def setModeLinkExternalModeReference(modeLinkID: str, name: str) -> bool:  # F.7.82.51
    ml = _resolve(modeLinkID)
    if ml is None:
        _invalid_id()
    ml.external_mode_reference = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    return True


def setModeLinkModeReference(modeLinkID: str, name: str) -> bool:  # F.7.82.52
    ml = _resolve(modeLinkID)
    if ml is None:
        _invalid_id()
    ml.mode_reference = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    return True


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


def setResetTypeLinkExternalResetTypeReference(resetTypeLinkID: str, name: str) -> bool:  # F.7.82.54
    rtl = _resolve(resetTypeLinkID)
    if rtl is None:
        _invalid_id()
    rtl.external_reset_type_reference = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    return True


def setResetTypeLinkResetTypeReference(resetTypeLinkID: str, name: str) -> bool:  # F.7.82.55
    rtl = _resolve(resetTypeLinkID)
    if rtl is None:
        _invalid_id()
    rtl.reset_type_reference = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    return True


def setViewLinkExternalViewReference(viewLinkID: str, name: str) -> bool:  # F.7.82.56
    vl = _resolve(viewLinkID)
    if vl is None:
        _invalid_id()
    vl.external_view_reference = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    return True


def setViewLinkViewReference(viewLinkID: str, name: str) -> bool:  # F.7.82.57
    vl = _resolve(viewLinkID)
    if vl is None:
        _invalid_id()
    vl.view_reference = SimpleNamespace(name=name)  # type: ignore[attr-defined]
    return True
