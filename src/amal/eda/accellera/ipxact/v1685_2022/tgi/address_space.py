# ruff: noqa: I001
"""Address space category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.11) and EXTENDED (F.7.12) Address space functions.
Only the 2022 schema is supported. Functions raise :class:`TgiError` with
``TgiFaultCode.INVALID_ID`` for invalid handles and ``TgiFaultCode.INVALID_ARGUMENT``
for semantic violations.

Returned numeric getters follow the project convention of returning ``int | None``
for resolved numeric value and separate *Expression* getters returning the (string)
expression as ``str | None``. ID getters return a child handle or ``None`` and list
traversal getters return an empty list if no children of the requested type exist.

Creation / mutation helpers create missing optional container elements where
allowed by the schema.
"""

from typing import Any
from unicodedata import category

from org.accellera.ipxact.v1685_2022 import AddressSpaces, ComponentType, FieldType
from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.executable_image import ExecutableImage
from org.accellera.ipxact.v1685_2022.file_set_ref import FileSetRef
from org.accellera.ipxact.v1685_2022.generator_ref import GeneratorRef
from org.accellera.ipxact.v1685_2022.linker_command_file import LinkerCommandFile
from org.accellera.ipxact.v1685_2022.local_address_bank_type import LocalAddressBankType
from org.accellera.ipxact.v1685_2022.local_memory_map_type import LocalMemoryMapType
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import (
    UnsignedLongintExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import (
    UnsignedPositiveIntExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import (
    UnsignedPositiveLongintExpression,
)

from ._model import _walk_model

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    get_parent_info,
    register_parent,
    detach_child_by_handle,
    registry,
)

__all__ = [  # BASE + EXTENDED exports
    # BASE (F.7.11)
    "getAddressSpaceAddressUnitBits",
    "getAddressSpaceAddressUnitBitsExpression",
    "getAddressSpaceAddressUnitBitsID",
    "getAddressSpaceLocalMemoryMapID",
    "getAddressSpaceRange",
    "getAddressSpaceRangeExpression",
    "getAddressSpaceRangeID",
    "getAddressSpaceSegmentIDs",
    "getAddressSpaceWidth",
    "getAddressSpaceWidthExpression",
    "getAddressSpaceWidthID",
    "getAliasOfAddressSpaceRefByName",
    "getAliasOfAddressSpaceRefID",
    "getLocalMemoryMapAddressBlockIDs",
    "getLocalMemoryMapBankIDs",
    "getRegionAddressOffset",
    "getRegionAddressOffsetExpression",
    "getRegionAddressOffsetID",
    "getRegionRange",
    "getRegionRangeExpression",
    "getRegionRangeID",
    "getSegmentAddressOffset",
    "getSegmentAddressOffsetExpression",
    "getSegmentAddressOffsetID",
    "getSegmentRange",
    "getSegmentRangeExpression",
    "getSegmentRangeID",
    # EXTENDED (F.7.12)
    "addAddressSpaceSegment",
    "addExecutableImageFileSetRef",
    "addLocalMemoryMapAddressBlock",
    "removeAddressSpaceAddressUnitBits",
    "removeAddressSpaceLocalMemoryMap",
    "removeAddressSpaceSegment",
    "removeExecutableImageFileSetRef",
    "removeLinkerCommandFileGenerator",
    "removeLocalMemoryMapAddressBlock",
    "removeLocalMemoryMapBank",
    "setAddressSpaceAddressUnitBits",
    "setAddressSpaceLocalMemoryMap",
    "setAddressSpaceRange",
    "setAddressSpaceWidth",
    "setSegmentAddressOffset",
    "setSegmentRange",
]


# ----------------------------------------------------------------------------
# Helpers (non-spec)
# ----------------------------------------------------------------------------


def _resolve_address_space(addressSpaceID: str) -> AddressSpaces.AddressSpace | None:
    """Resolve a handle to an ``addressSpace`` element.

    Helper (non-spec) used internally by Address space TGI functions.

    Args:
        addressSpaceID: Handle referencing an ``addressSpace`` element.

    Returns:
        AddressSpaces.AddressSpace | None: Resolved object or ``None`` if the
        handle does not reference the expected type.
    """
    obj = resolve_handle(addressSpaceID)
    if isinstance(obj, AddressSpaces.AddressSpace):  # type: ignore[attr-defined]
        return obj
    return None


def _resolve_segment(segmentID: str) -> AddressSpaces.AddressSpace.Segments.Segment | None:  # type: ignore[return-type]
    """Resolve a handle to a ``segment`` element.

    Helper (non-spec).

    Args:
        segmentID: Handle referencing a ``segment`` element of an addressSpace.

    Returns:
        AddressSpaces.AddressSpace.Segments.Segment | None: Resolved segment or
        ``None`` if the handle is invalid / different type.
    """
    obj = resolve_handle(segmentID)
    if isinstance(obj, AddressSpaces.AddressSpace.Segments.Segment):  # type: ignore[attr-defined]
        return obj
    return None


def _resolve_region(regionID: str) -> ComponentType.Cpus.Cpu.Regions.Region | None:
    """Resolve a CPU region handle without accepting address-space segments."""
    obj = resolve_handle(regionID)
    return obj if isinstance(obj, ComponentType.Cpus.Cpu.Regions.Region) else None


def _resolve_local_memory_map(localMemoryMapID: str) -> LocalMemoryMapType | None:
    """Resolve a handle to a ``localMemoryMap`` element.

    Helper (non-spec).

    Args:
        localMemoryMapID: Handle referencing a ``localMemoryMap``.

    Returns:
        LocalMemoryMapType | None: Resolved object or ``None`` when invalid.
    """
    obj = resolve_handle(localMemoryMapID)
    return obj if isinstance(obj, LocalMemoryMapType) else None


def _resolve_alias_of(aliasOfID: str) -> FieldType.AliasOf | None:
    obj = resolve_handle(aliasOfID)
    return obj if isinstance(obj, FieldType.AliasOf) else None


def _resolve_executable_image(executableImageID: str) -> ExecutableImage | None:
    obj = resolve_handle(executableImageID)
    return obj if isinstance(obj, ExecutableImage) else None


def _integer_value(expression: Any) -> int | None:
    """Evaluate a self-contained SystemVerilog integer expression."""
    value = getattr(expression, "value", None)
    if not isinstance(value, str) or not value.strip():
        return None
    return _integer_text(value)


def _integer_text(value: str) -> int | None:
    """Evaluate a self-contained integer expression from source text."""
    try:
        try:
            return int(value, 0) if value.lower().startswith(("0x", "0o", "0b")) else int(value)
        except ValueError:
            from amal.eda.systemverilog.expression_parser import SvExpressionParser

            result = SvExpressionParser().evaluate(value)
            return result if type(result) is int else None
    except ImportError, ValueError, TypeError, AttributeError:
        return None


def _expression_value(value: Any, argument: str, minimum: int, maximum: int) -> str:
    """Validate a typed setter input without modifying its target model."""
    if type(value) is int:
        if not minimum <= value <= maximum:
            raise TgiError(f"{argument} is outside the supported integer range", TgiFaultCode.INVALID_ARGUMENT)
        return str(value)
    if not isinstance(value, str) or not value.strip():
        raise TgiError(f"{argument} must be a non-empty expression string or integer", TgiFaultCode.INVALID_ARGUMENT)
    evaluated = _integer_text(value)
    if evaluated is not None and not minimum <= evaluated <= maximum:
        raise TgiError(f"{argument} is outside the supported integer range", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _name_value(value: Any, argument: str) -> str:
    """Validate an XML Schema ``xs:Name`` argument."""
    if not isinstance(value, str) or not value:
        raise TgiError(f"{argument} must be a non-empty xs:Name", TgiFaultCode.INVALID_ARGUMENT)

    def start(char: str) -> bool:
        return char in ":_" or category(char) in {"Lu", "Ll", "Lt", "Lm", "Lo", "Nl"}

    def continuation(char: str) -> bool:
        return start(char) or char in "-." or category(char) in {"Mn", "Mc", "Nd", "Pc"}

    if not start(value[0]) or any(not continuation(char) for char in value[1:]):
        raise TgiError(f"{argument} must be a valid xs:Name", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _set_expression(
    parent: Any,
    attribute: str,
    model_type: type,
    value: Any,
    argument: str,
    minimum: int,
    maximum: int,
) -> None:
    """Set an expression child in place when possible, preserving child handle identity."""
    current = getattr(parent, attribute, None)
    if current is not None and not isinstance(current, model_type):
        raise TgiError(f"Invalid {attribute} model on parent", TgiFaultCode.INVALID_ID)
    current_minimum = getattr(current, "minimum", None)
    current_maximum = getattr(current, "maximum", None)
    if current_minimum is not None:
        minimum = max(minimum, current_minimum)
    if current_maximum is not None:
        maximum = min(maximum, current_maximum)
    source = _expression_value(value, argument, minimum, maximum)
    if current is None:
        current = model_type(value=source)
        setattr(parent, attribute, current)
    else:
        current.value = source
    register_parent(current, parent, (attribute,), "single")


def _register_owned_child(child: Any, expected_parent: type | tuple[type, ...] | None = None) -> Any | None:
    """Register and return a child's direct owner from known TGI parent links or roots."""
    info = get_parent_info(get_handle(child))
    parent = resolve_handle(info.parent_handle) if info is not None else None
    if parent is not None and (expected_parent is None or isinstance(parent, expected_parent)):
        return parent
    for root_id in registry.iter_by_predicate(lambda _root: True):
        root = resolve_handle(root_id)
        if root is None:
            continue
        for obj, owner, attribute, container in _walk_model(root):
            if (
                obj is child
                and owner is not None
                and attribute is not None
                and (expected_parent is None or isinstance(owner, expected_parent))
            ):
                register_parent(child, owner, (attribute,), container)
                return owner
    return None


def _remove_owned(handle: str, expected: type, parent_type: type, label: str) -> bool:
    """Remove a typed child after discovering its owning schema container."""
    obj = resolve_handle(handle)
    if not isinstance(obj, expected):
        raise TgiError(f"Invalid {label} handle", TgiFaultCode.INVALID_ID)
    if _register_owned_child(obj, parent_type) is None:
        raise TgiError(f"{label} handle has no registered owning container", TgiFaultCode.INVALID_ID)
    if not detach_child_by_handle(handle):
        raise TgiError(f"Could not remove {label}", TgiFaultCode.INVALID_ID)
    return True


# ----------------------------------------------------------------------------
# BASE (F.7.11)
# ----------------------------------------------------------------------------


def getAddressSpaceAddressUnitBits(addressSpaceID: str) -> int | None:
    """Return the evaluated address unit size (IEEE 1685-2022 F.7.11.1).

    Section: F.7.11.1.

    Args:
        addressSpaceID: Handle referencing an ``addressSpace`` element.

    Returns:
        int | None: Evaluated ``addressUnitBits`` value, or ``None`` if it is
        absent or its expression cannot be evaluated.

    Raises:
        TgiError: If ``addressSpaceID`` is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    return _integer_value(getattr(as_, "address_unit_bits", None))


def getAddressSpaceAddressUnitBitsExpression(addressSpaceID: str) -> str | None:
    """Return source text for ``addressUnitBits`` (IEEE 1685-2022 F.7.11.2).

    Section: F.7.11.2.

    Args:
        addressSpaceID: Handle of the parent addressSpace.

    Returns:
        str | None: Original expression string, or ``None`` when absent.

    Raises:
        TgiError: If ``addressSpaceID`` is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    aub = getattr(as_, "address_unit_bits", None)
    return getattr(aub, "value", None) if aub is not None else None


def getAddressSpaceAddressUnitBitsID(addressSpaceID: str) -> str | None:
    """Return the ``addressUnitBits`` child handle (IEEE 1685-2022 F.7.11.3).

    Section: F.7.11.3.

    Args:
        addressSpaceID: Handle referencing an addressSpace.

    Returns:
        str | None: Child handle or ``None`` if element absent.

    Raises:
        TgiError: If the parent handle is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    aub = getattr(as_, "address_unit_bits", None)
    if aub is None:
        return None
    register_parent(aub, as_, ("address_unit_bits",), "single")
    return get_handle(aub)


def getAddressSpaceLocalMemoryMapID(addressSpaceID: str) -> str | None:
    """Return the ``localMemoryMap`` child handle (IEEE 1685-2022 F.7.11.4).

    Section: F.7.11.4.

    Args:
        addressSpaceID: Handle referencing an addressSpace.

    Returns:
        str | None: Handle of the ``localMemoryMap`` child or ``None`` if absent.

    Raises:
        TgiError: If the parent handle is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    lmm = getattr(as_, "local_memory_map", None)
    if lmm is None:
        return None
    register_parent(lmm, as_, ("local_memory_map",), "single")
    return get_handle(lmm)


def getAddressSpaceRange(addressSpaceID: str) -> int | None:
    """Return evaluated ``range`` (IEEE 1685-2022 F.7.11.5).

    Section: F.7.11.5.

    Args:
        addressSpaceID: Handle of the addressSpace.

    Returns:
        int | None: Evaluated range or ``None`` when unresolved.

    Raises:
        TgiError: If the addressSpace handle is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    return _integer_value(getattr(as_, "range", None))


def getAddressSpaceRangeExpression(addressSpaceID: str) -> str | None:
    """Return the source ``range`` expression (IEEE 1685-2022 F.7.11.6).

    Section: F.7.11.6.

    Args:
        addressSpaceID: Address space handle.

    Returns:
        str | None: Expression or ``None`` if absent.

    Raises:
        TgiError: If handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    r = getattr(as_, "range", None)
    return getattr(r, "value", None) if r is not None else None


def getAddressSpaceRangeID(addressSpaceID: str) -> str | None:
    """Return the ``range`` child handle (IEEE 1685-2022 F.7.11.7).

    Section: F.7.11.7.

    Args:
        addressSpaceID: Handle referencing an addressSpace.

    Returns:
        str | None: Child handle or ``None`` when absent.

    Raises:
        TgiError: If parent handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    r = getattr(as_, "range", None)
    if r is None:
        return None
    register_parent(r, as_, ("range",), "single")
    return get_handle(r)


def getAddressSpaceSegmentIDs(addressSpaceID: str) -> list[str]:
    """Return address-space segment handles (IEEE 1685-2022 F.7.11.8).

    Section: F.7.11.8.

    Args:
        addressSpaceID: Address space handle.

    Returns:
        list[str]: List (possibly empty) of segment handles.

    Raises:
        TgiError: If parent handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    segs = getattr(as_, "segments", None)
    if segs is None:
        return []
    register_parent(segs, as_, ("segments",), "single")
    result = []
    for segment in getattr(segs, "segment", []):
        register_parent(segment, segs, ("segment",), "list")
        result.append(get_handle(segment))
    return result


def getAddressSpaceWidth(addressSpaceID: str) -> int | None:
    """Return evaluated ``width`` (IEEE 1685-2022 F.7.11.9).

    Section: F.7.11.9.

    Args:
        addressSpaceID: Address space handle.

    Returns:
        int | None: Numeric width or ``None`` if absent or not evaluable.

    Raises:
        TgiError: If handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    return _integer_value(getattr(as_, "width", None))


def getAddressSpaceWidthExpression(addressSpaceID: str) -> str | None:
    """Return the source ``width`` expression (IEEE 1685-2022 F.7.11.10).

    Section: F.7.11.10.

    Args:
        addressSpaceID: Address space handle.

    Returns:
        str | None: Expression or ``None`` when absent.

    Raises:
        TgiError: If handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    w = getattr(as_, "width", None)
    return getattr(w, "value", None) if w is not None else None


def getAddressSpaceWidthID(addressSpaceID: str) -> str | None:
    """Return the ``width`` child handle (IEEE 1685-2022 F.7.11.11).

    Section: F.7.11.11.

    Args:
        addressSpaceID: Address space handle.

    Returns:
        str | None: Child handle or ``None`` if absent.

    Raises:
        TgiError: If parent handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    w = getattr(as_, "width", None)
    if w is None:
        return None
    register_parent(w, as_, ("width",), "single")
    return get_handle(w)


def getAliasOfAddressSpaceRefByName(aliasOfID: str) -> str | None:
    """Return the stored address-space reference name (IEEE 1685-2022 F.7.11.12).

    Section: F.7.11.12.

    Args:
        aliasOfID: Handle to a field ``aliasOf`` element.

    Returns:
        str | None: Referenced address-space name, or ``None`` if no such choice exists.

    Raises:
        TgiError: If ``aliasOfID`` does not reference an ``aliasOf`` model.
    """
    alias = _resolve_alias_of(aliasOfID)
    if alias is None:
        raise TgiError("Invalid aliasOf handle", TgiFaultCode.INVALID_ID)
    ref = next(
        (
            child
            for child in alias.address_space_ref_or_memory_map_ref_or_memory_remap_ref
            if isinstance(child, FieldType.AliasOf.AddressSpaceRef)
        ),
        None,
    )
    return ref.address_space_ref if ref is not None else None


def getAliasOfAddressSpaceRefID(aliasOfID: str) -> str | None:
    """Return the ``addressSpaceRef`` child handle (IEEE 1685-2022 F.7.11.13).

    Section: F.7.11.13.

    Args:
        aliasOfID: Handle to a field ``aliasOf`` element.

    Returns:
        str | None: Handle to its ``addressSpaceRef`` choice, or ``None`` when absent.

    Raises:
        TgiError: If ``aliasOfID`` does not reference an ``aliasOf`` model.
    """
    alias = _resolve_alias_of(aliasOfID)
    if alias is None:
        raise TgiError("Invalid aliasOf handle", TgiFaultCode.INVALID_ID)
    path = "address_space_ref_or_memory_map_ref_or_memory_remap_ref"
    ref = next(
        (child for child in getattr(alias, path, []) if isinstance(child, FieldType.AliasOf.AddressSpaceRef)),
        None,
    )
    if ref is None:
        return None
    register_parent(ref, alias, (path,), "list")
    return get_handle(ref)


def getLocalMemoryMapAddressBlockIDs(addressSpaceID: str) -> list[str]:
    """Return local address-block handles (IEEE 1685-2022 F.7.11.14).

    Section: F.7.11.14.

    Args:
        addressSpaceID: Handle referencing an ``addressSpace`` element.

    Returns:
        list[str]: Handles of contained ``addressBlock`` elements (empty if none).

    Raises:
        TgiError: If handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    lmm = as_.local_memory_map
    if lmm is None:
        return []
    register_parent(lmm, as_, ("local_memory_map",), "single")
    return _local_memory_map_child_ids(lmm, AddressBlock)


def getLocalMemoryMapBankIDs(addressSpaceID: str) -> list[str]:
    """Return local bank handles (IEEE 1685-2022 F.7.11.15).

    Section: F.7.11.15.

    Args:
        addressSpaceID: Handle referencing an ``addressSpace`` element.

    Returns:
        list[str]: Bank handles (empty list if none present).

    Raises:
        TgiError: If handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    lmm = as_.local_memory_map
    if lmm is None:
        return []
    register_parent(lmm, as_, ("local_memory_map",), "single")
    return _local_memory_map_child_ids(lmm, LocalAddressBankType)


def _local_memory_map_child_ids(local_memory_map: LocalMemoryMapType, expected: type) -> list[str]:
    """Return owned child handles from the generated mixed addressBlock/bank choice."""
    result = []
    for child in local_memory_map.address_block_or_bank:
        if isinstance(child, expected):
            register_parent(child, local_memory_map, ("address_block_or_bank",), "list")
            result.append(get_handle(child))
    return result


def getRegionAddressOffset(regionID: str) -> int | None:
    """Return an evaluated region offset (IEEE 1685-2022 F.7.11.16).

    Section: F.7.11.16.

    Args:
        regionID: Handle referencing a ``region``.

    Returns:
        int | None: Evaluated offset, or ``None`` when unresolved.

    Raises:
        TgiError: If region handle invalid.
    """
    seg = _resolve_region(regionID)
    if seg is None:
        raise TgiError("Invalid region handle", TgiFaultCode.INVALID_ID)
    return _integer_value(getattr(seg, "address_offset", None))


def getRegionAddressOffsetExpression(regionID: str) -> str | None:
    """Return source text for a region offset (IEEE 1685-2022 F.7.11.17).

    Section: F.7.11.17.

    Args:
        regionID: Region handle.

    Returns:
        str | None: Expression string or ``None`` if missing.

    Raises:
        TgiError: If handle invalid.
    """
    seg = _resolve_region(regionID)
    if seg is None:
        raise TgiError("Invalid region handle", TgiFaultCode.INVALID_ID)
    ao = getattr(seg, "address_offset", None)
    return getattr(ao, "value", None) if ao is not None else None


def getRegionAddressOffsetID(regionID: str) -> str | None:
    """Return the region offset child handle (IEEE 1685-2022 F.7.11.18).

    Section: F.7.11.18.

    Args:
        regionID: Region handle.

    Returns:
        str | None: Child handle or ``None`` when element absent.

    Raises:
        TgiError: If handle invalid.
    """
    seg = _resolve_region(regionID)
    if seg is None:
        raise TgiError("Invalid region handle", TgiFaultCode.INVALID_ID)
    ao = getattr(seg, "address_offset", None)
    if ao is None:
        return None
    register_parent(ao, seg, ("address_offset",), "single")
    return get_handle(ao)


def getRegionRange(regionID: str) -> int | None:
    """Return an evaluated region range (IEEE 1685-2022 F.7.11.19).

    Section: F.7.11.19.

    Args:
        regionID: Region handle.

    Returns:
        int | None: Evaluated range, or ``None`` when unresolved.

    Raises:
        TgiError: If handle invalid.
    """
    seg = _resolve_region(regionID)
    if seg is None:
        raise TgiError("Invalid region handle", TgiFaultCode.INVALID_ID)
    return _integer_value(getattr(seg, "range", None))


def getRegionRangeExpression(regionID: str) -> str | None:
    """Return source text for a region range (IEEE 1685-2022 F.7.11.20).

    Section: F.7.11.20.

    Args:
        regionID: Region handle.

    Returns:
        str | None: Expression or ``None`` if element absent.

    Raises:
        TgiError: If handle invalid.
    """
    seg = _resolve_region(regionID)
    if seg is None:
        raise TgiError("Invalid region handle", TgiFaultCode.INVALID_ID)
    r = getattr(seg, "range", None)
    return getattr(r, "value", None) if r is not None else None


def getRegionRangeID(regionID: str) -> str | None:
    """Return the region range child handle (IEEE 1685-2022 F.7.11.21).

    Section: F.7.11.21.

    Args:
        regionID: Region handle.

    Returns:
        str | None: Child handle or ``None`` when element absent.

    Raises:
        TgiError: If handle invalid.
    """
    seg = _resolve_region(regionID)
    if seg is None:
        raise TgiError("Invalid region handle", TgiFaultCode.INVALID_ID)
    r = getattr(seg, "range", None)
    if r is None:
        return None
    register_parent(r, seg, ("range",), "single")
    return get_handle(r)


def getSegmentAddressOffset(segmentID: str) -> int | None:
    """Return evaluated segment offset (IEEE 1685-2022 F.7.11.22).

    Section: F.7.11.22.

    Args:
        segmentID: Handle to a ``segment`` element.

    Returns:
        int | None: Evaluated offset, or ``None`` when unresolved.

    Raises:
        TgiError: If ``segmentID`` is invalid or has another model type.
    """
    segment = _resolve_segment(segmentID)
    if segment is None:
        raise TgiError("Invalid segment handle", TgiFaultCode.INVALID_ID)
    return _integer_value(getattr(segment, "address_offset", None))


def getSegmentAddressOffsetExpression(segmentID: str) -> str | None:
    """Return source text for segment offset (IEEE 1685-2022 F.7.11.23).

    Section: F.7.11.23.

    Args:
        segmentID: Handle to a ``segment`` element.

    Returns:
        str | None: Original offset expression, or ``None`` if absent.

    Raises:
        TgiError: If ``segmentID`` is invalid or has another model type.
    """
    segment = _resolve_segment(segmentID)
    if segment is None:
        raise TgiError("Invalid segment handle", TgiFaultCode.INVALID_ID)
    child = getattr(segment, "address_offset", None)
    if child is None:
        return None
    return getattr(child, "value", None)


def getSegmentAddressOffsetID(segmentID: str) -> str | None:
    """Return the segment offset child handle (IEEE 1685-2022 F.7.11.24).

    Section: F.7.11.24.

    Args:
        segmentID: Handle to a ``segment`` element.

    Returns:
        str | None: Handle to ``addressOffset``, or ``None`` if absent.

    Raises:
        TgiError: If ``segmentID`` is invalid or has another model type.
    """
    segment = _resolve_segment(segmentID)
    if segment is None:
        raise TgiError("Invalid segment handle", TgiFaultCode.INVALID_ID)
    child = getattr(segment, "address_offset", None)
    if child is None:
        return None
    register_parent(child, segment, ("address_offset",), "single")
    return get_handle(child)


def getSegmentRange(segmentID: str) -> int | None:
    """Return evaluated segment range (IEEE 1685-2022 F.7.11.25).

    Section: F.7.11.25.

    Args:
        segmentID: Handle to a ``segment`` element.

    Returns:
        int | None: Evaluated range, or ``None`` when unresolved.

    Raises:
        TgiError: If ``segmentID`` is invalid or has another model type.
    """
    segment = _resolve_segment(segmentID)
    if segment is None:
        raise TgiError("Invalid segment handle", TgiFaultCode.INVALID_ID)
    return _integer_value(getattr(segment, "range", None))


def getSegmentRangeExpression(segmentID: str) -> str | None:
    """Return source text for segment range (IEEE 1685-2022 F.7.11.26).

    Section: F.7.11.26.

    Args:
        segmentID: Handle to a ``segment`` element.

    Returns:
        str | None: Original range expression, or ``None`` if absent.

    Raises:
        TgiError: If ``segmentID`` is invalid or has another model type.
    """
    segment = _resolve_segment(segmentID)
    if segment is None:
        raise TgiError("Invalid segment handle", TgiFaultCode.INVALID_ID)
    child = getattr(segment, "range", None)
    if child is None:
        return None
    return getattr(child, "value", None)


def getSegmentRangeID(segmentID: str) -> str | None:
    """Return the segment range child handle (IEEE 1685-2022 F.7.11.27).

    Section: F.7.11.27.

    Args:
        segmentID: Handle to a ``segment`` element.

    Returns:
        str | None: Handle to ``range``, or ``None`` if absent.

    Raises:
        TgiError: If ``segmentID`` is invalid or has another model type.
    """
    segment = _resolve_segment(segmentID)
    if segment is None:
        raise TgiError("Invalid segment handle", TgiFaultCode.INVALID_ID)
    child = getattr(segment, "range", None)
    if child is None:
        return None
    register_parent(child, segment, ("range",), "single")
    return get_handle(child)


# ----------------------------------------------------------------------------
# EXTENDED (F.7.12)
# ----------------------------------------------------------------------------


def addAddressSpaceSegment(addressSpaceID: str, name: str, addressOffsetExpr: str, rangeExpr: str) -> str:
    """Append a segment (IEEE 1685-2022 F.7.12.1).

    Section: F.7.12.1.

    Args:
        addressSpaceID: Parent ``addressSpace`` handle.
        name: New segment name.
        addressOffsetExpr: Source expression for ``addressOffset``.
        rangeExpr: Source expression for positive ``range``.

    Returns:
        str: Handle of the newly created segment.

    Raises:
        TgiError: If the parent is invalid or an argument is not a valid typed value.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    name = _name_value(name, "name")
    offset = _expression_value(addressOffsetExpr, "addressOffset", 0, (1 << 64) - 1)
    range_ = _expression_value(rangeExpr, "range", 1, (1 << 64) - 1)
    seg = AddressSpaces.AddressSpace.Segments.Segment(  # type: ignore[attr-defined]
        name=name,
        address_offset=UnsignedLongintExpression(value=offset),
        range=UnsignedPositiveLongintExpression(value=range_),
    )
    if as_.segments is None:
        as_.segments = AddressSpaces.AddressSpace.Segments(segment=[])
    register_parent(as_.segments, as_, ("segments",), "single")
    as_.segments.segment.append(seg)
    register_parent(seg, as_.segments, ("segment",), "list")
    return get_handle(seg)


def addExecutableImageFileSetRef(executableImageID: str, localName: str) -> str:
    """Append an executable-image file-set reference (IEEE 1685-2022 F.7.12.2).

    Section: F.7.12.2.

    Args:
        executableImageID: Handle to an ``executableImage`` element.
        localName: Name of a file set in the containing component.

    Returns:
        str: Handle of the new ``fileSetRef``.

    Raises:
        TgiError: If the parent handle is invalid or ``localName`` is not an xs:Name.
    """
    image = _resolve_executable_image(executableImageID)
    if image is None:
        raise TgiError("Invalid executableImage handle", TgiFaultCode.INVALID_ID)
    local_name = _name_value(localName, "localName")
    group = image.file_set_ref_group
    if group is None:
        group = ExecutableImage.FileSetRefGroup(file_set_ref=[])
        image.file_set_ref_group = group
        register_parent(group, image, ("file_set_ref_group",), "single")
    ref = FileSetRef(local_name=local_name)
    group.file_set_ref.append(ref)
    register_parent(ref, group, ("file_set_ref",), "list")
    return get_handle(ref)


def addLocalMemoryMapAddressBlock(
    localMemoryMapID: str,
    name: str,
    baseAddressExpr: str,
    rangeExpr: str,
    widthExpr: str,
) -> str:
    """Append an inline local address block (IEEE 1685-2022 F.7.12.3).

    Section: F.7.12.3.

    Args:
        localMemoryMapID: Parent localMemoryMap handle.
        name: New address-block name.
        baseAddressExpr: Expression for baseAddress.
        rangeExpr: Expression for range.
        widthExpr: Expression for width.

    Returns:
        str: Handle of the newly created addressBlock.

    Raises:
        TgiError: If the parent is invalid or an argument is not a valid typed value.
    """
    lmm = _resolve_local_memory_map(localMemoryMapID)
    if lmm is None:
        raise TgiError("Invalid localMemoryMap handle", TgiFaultCode.INVALID_ID)
    name = _name_value(name, "name")
    base_address = _expression_value(baseAddressExpr, "baseAddress", 0, (1 << 64) - 1)
    range_ = _expression_value(rangeExpr, "range", 1, (1 << 64) - 1)
    width = _expression_value(widthExpr, "width", 1, (1 << 32) - 1)
    ab = AddressBlock(
        name=name,
        base_address=BaseAddress(value=base_address),
        choice=[
            UnsignedPositiveLongintExpression(value=range_),
            UnsignedPositiveIntExpression(value=width),
        ],
    )
    lmm.address_block_or_bank.append(ab)
    register_parent(ab, lmm, ("address_block_or_bank",), "list")
    return get_handle(ab)


def removeAddressSpaceAddressUnitBits(addressSpaceID: str) -> bool:
    """Remove ``addressUnitBits`` and its handle (IEEE 1685-2022 F.7.12.4).

    Section: F.7.12.4.

    Args:
        addressSpaceID: Address space handle.

    Returns:
        bool: ``True`` if removed, ``False`` if it was absent.

    Raises:
        TgiError: If handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    child = as_.address_unit_bits
    if child is None:
        return False
    register_parent(child, as_, ("address_unit_bits",), "single")
    return detach_child_by_handle(get_handle(child))


def removeAddressSpaceLocalMemoryMap(addressSpaceID: str) -> bool:
    """Remove ``localMemoryMap`` and its descendants (IEEE 1685-2022 F.7.12.5).

    Section: F.7.12.5.

    Args:
        addressSpaceID: Address space handle.

    Returns:
        bool: ``True`` if removed, else ``False``.

    Raises:
        TgiError: If handle invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    child = as_.local_memory_map
    if child is None:
        return False
    register_parent(child, as_, ("local_memory_map",), "single")
    return detach_child_by_handle(get_handle(child))


def removeAddressSpaceSegment(segmentID: str) -> bool:
    """Remove a segment and its descendants (IEEE 1685-2022 F.7.12.6).

    Section: F.7.12.6.

    Args:
        segmentID: Segment handle.

    Returns:
        bool: ``True`` after removing the segment.

    Raises:
        TgiError: If ``segmentID`` is invalid or has another model type.
    """
    return _remove_owned(
        segmentID,
        AddressSpaces.AddressSpace.Segments.Segment,
        AddressSpaces.AddressSpace.Segments,
        "segment",
    )


def removeExecutableImageFileSetRef(fileSetRefID: str) -> bool:
    """Remove an executable-image file-set reference (IEEE 1685-2022 F.7.12.7).

    Section: F.7.12.7.

    Args:
        fileSetRefID: Handle to the executable image's ``fileSetRef``.

    Returns:
        bool: ``True`` after removal.

    Raises:
        TgiError: If the handle is not a file-set reference in an executable image.
    """
    return _remove_owned(fileSetRefID, FileSetRef, ExecutableImage.FileSetRefGroup, "fileSetRef")


def removeLinkerCommandFileGenerator(generatorID: str) -> bool:
    """Remove a linker-command-file generator reference (IEEE 1685-2022 F.7.12.8).

    Section: F.7.12.8.

    Args:
        generatorID: Handle to a ``generatorRef`` in a linker command file.

    Returns:
        bool: ``True`` after removal.

    Raises:
        TgiError: If this is not a ``GeneratorRef`` owned by a ``linkerCommandFile``.
    """
    return _remove_owned(generatorID, GeneratorRef, LinkerCommandFile, "linker command file generator")


def removeLocalMemoryMapAddressBlock(addressBlockID: str) -> bool:
    """Remove a local address block and descendants (IEEE 1685-2022 F.7.12.9).

    Section: F.7.12.9.

    Args:
        addressBlockID: AddressBlock handle.

    Returns:
        bool: ``True`` after removal.

    Raises:
        TgiError: If this is not an address block owned by a local map.
    """
    return _remove_owned(addressBlockID, AddressBlock, LocalMemoryMapType, "local addressBlock")


def removeLocalMemoryMapBank(bankID: str) -> bool:
    """Remove a local bank and descendants (IEEE 1685-2022 F.7.12.10).

    Section: F.7.12.10.

    Args:
        bankID: Bank handle.

    Returns:
        bool: ``True`` after removal.

    Raises:
        TgiError: If this is not a local bank owned by a local map.
    """
    return _remove_owned(bankID, LocalAddressBankType, LocalMemoryMapType, "local bank")


def setAddressSpaceAddressUnitBits(addressSpaceID: str, value: int | str) -> bool:
    """Set or create ``addressUnitBits`` (IEEE 1685-2022 F.7.12.11).

    Section: F.7.12.11.

    Args:
        addressSpaceID: Address space handle.
        value: Source expression string or integer value.

    Returns:
        bool: ``True`` on success.

    Raises:
        TgiError: If the parent handle or typed expression value is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits

    _set_expression(as_, "address_unit_bits", AddressUnitBits, value, "addressUnitBitsExpression", 1, (1 << 64) - 1)
    return True


def setAddressSpaceLocalMemoryMap(
    addressSpaceID: str,
    name: str,
    addressBlockName: str,
    baseAddress: str,
    range: str,
    width: str,
) -> bool:
    """Set a local map with one default address block (IEEE 1685-2022 F.7.12.12).

    Section: F.7.12.12.

    The generated 2022 schema models a local address block inline as
    ``baseAddress`` followed by the ``range`` and ``width`` choice entries.
    The TGI text mentions an ``addressBlockDefinitionRef`` even though the
    operation has no definition-name or type-definitions input. This function
    therefore creates a schema-valid inline address block from its supplied
    values.

    Args:
        addressSpaceID: Parent addressSpace handle.
        name: Name for the localMemoryMap.
        addressBlockName: Name for its default addressBlock.
        baseAddress: Base address expression.
        range: Positive address range expression.
        width: Positive block width expression.

    Returns:
        bool: ``True`` on success.

    Raises:
        TgiError: If the parent or any name/expression argument is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    map_name = _name_value(name, "name")
    block_name = _name_value(addressBlockName, "addressBlockName")
    base_value = _expression_value(baseAddress, "baseAddress", 0, (1 << 64) - 1)
    range_value = _expression_value(range, "range", 1, (1 << 64) - 1)
    width_value = _expression_value(width, "width", 1, (1 << 32) - 1)
    block = AddressBlock(
        name=block_name,
        base_address=BaseAddress(value=base_value),
        choice=[
            UnsignedPositiveLongintExpression(value=range_value),
            UnsignedPositiveIntExpression(value=width_value),
        ],
    )
    local_map = as_.local_memory_map
    if local_map is None:
        local_map = LocalMemoryMapType(name=map_name, address_block_or_bank=[])
        as_.local_memory_map = local_map
        register_parent(local_map, as_, ("local_memory_map",), "single")
    else:
        register_parent(local_map, as_, ("local_memory_map",), "single")
        if not isinstance(local_map.address_block_or_bank, list):
            local_map.address_block_or_bank = list(local_map.address_block_or_bank)
        for child in list(local_map.address_block_or_bank):
            register_parent(child, local_map, ("address_block_or_bank",), "list")
            if not detach_child_by_handle(get_handle(child)):
                raise TgiError("Could not replace local memory map contents", TgiFaultCode.INVALID_ID)
        local_map.name = map_name
    local_map.address_block_or_bank.append(block)
    register_parent(block, local_map, ("address_block_or_bank",), "list")
    return True


def setAddressSpaceRange(addressSpaceID: str, value: int | str) -> bool:
    """Set the positive ``range`` expression (IEEE 1685-2022 F.7.12.13).

    Section: F.7.12.13.

    Args:
        addressSpaceID: Address space handle.
        value: Integer or expression string.

    Returns:
        bool: ``True`` on success.

    Raises:
        TgiError: If the parent or typed expression value is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    _set_expression(as_, "range", UnsignedPositiveLongintExpression, value, "value", 1, (1 << 64) - 1)
    return True


def setAddressSpaceWidth(addressSpaceID: str, value: int | str) -> bool:
    """Set the positive ``width`` expression (IEEE 1685-2022 F.7.12.14).

    Section: F.7.12.14.

    Args:
        addressSpaceID: Address space handle.
        value: Integer or expression string.

    Returns:
        bool: ``True`` on success.

    Raises:
        TgiError: If the parent or typed expression value is invalid.
    """
    as_ = _resolve_address_space(addressSpaceID)
    if as_ is None:
        raise TgiError("Invalid addressSpace handle", TgiFaultCode.INVALID_ID)
    _set_expression(as_, "width", UnsignedPositiveIntExpression, value, "value", 1, (1 << 32) - 1)
    return True


def setSegmentAddressOffset(segmentID: str, value: int | str) -> bool:
    """Set segment ``addressOffset`` (IEEE 1685-2022 F.7.12.15).

    Section: F.7.12.15.

    Args:
        segmentID: Segment handle.
        value: Integer or expression string.

    Returns:
        bool: ``True`` on success.

    Raises:
        TgiError: If the segment handle or typed expression value is invalid.
    """
    seg = _resolve_segment(segmentID)
    if seg is None:
        raise TgiError("Invalid segment handle", TgiFaultCode.INVALID_ID)
    _set_expression(seg, "address_offset", UnsignedLongintExpression, value, "value", 0, (1 << 64) - 1)
    return True


def setSegmentRange(segmentID: str, value: int | str) -> bool:
    """Set segment ``range`` (IEEE 1685-2022 F.7.12.16).

    Section: F.7.12.16.

    Args:
        segmentID: Segment handle.
        value: Integer or expression string.

    Returns:
        bool: ``True`` on success.

    Raises:
        TgiError: If the segment handle or typed expression value is invalid.
    """
    seg = _resolve_segment(segmentID)
    if seg is None:
        raise TgiError("Invalid segment handle", TgiFaultCode.INVALID_ID)
    _set_expression(seg, "range", UnsignedPositiveLongintExpression, value, "value", 1, (1 << 64) - 1)
    return True
