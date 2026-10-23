"""CPU category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.21) and EXTENDED (F.7.22) CPU functions.

The schema exposes CPUs via ``component.cpus.cpu[*]`` each with required
``name``, ``range``, ``width`` and ``memoryMapRef`` elements plus optional
``addressUnitBits`` (expression), ``regions`` list, executableImage list and
parameter list. Regions have required ``name``, ``addressOffset`` and ``range``.

BASE functions provide traversal of CPUs and their regions plus getters for
scalar/textual values and numeric/expression/ID triplets where the underlying
schema uses an expression type. EXTENDED functions support adding/removing CPUs
and regions, setting/clearing optional scalars and assigning expression values.

Numeric getters evaluate self-contained SystemVerilog integer constants.
Unresolved expressions fault until a configured environment is available.
An omitted addressUnitBits has the standard effective default of eight bits;
its expression and handle getters still expose only explicit XML content.
Expression edits preserve generated wrappers and metadata. Required values
cannot be cleared; optional addressUnitBits has a separate removal operation.
"""

# ruff: noqa: I001

from typing import Any
import re

from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser
from org.accellera.ipxact.v1685_2022.executable_image import ExecutableImage
from . import component as component_api
from .address_space import _register_owned_child
from ._attribute_references import _root_for, _walk


from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)

__all__: list[str] = [
    # BASE (F.7.21)
    "getComponentCpuIDs",
    "getCpuName",
    "getCpuDisplayName",
    "getCpuShortDescription",
    "getCpuDescription",
    "getCpuMemoryMapRef",
    "getCpuExecutableImageIDs",
    "getCpuMemoryMapRefByID",
    "getCpuMemoryMapRefByName",
    "getCpuRange",
    "getCpuRangeExpression",
    "getCpuRangeID",
    "getCpuWidth",
    "getCpuWidthExpression",
    "getCpuWidthID",
    "getCpuAddressUnitBits",
    "getCpuAddressUnitBitsExpression",
    "getCpuAddressUnitBitsID",
    "getCpuRegionIDs",
    "getCpuRegionName",
    "getCpuRegionDisplayName",
    "getCpuRegionShortDescription",
    "getCpuRegionDescription",
    "getCpuRegionAddressOffset",
    "getCpuRegionAddressOffsetExpression",
    "getCpuRegionAddressOffsetID",
    "getCpuRegionRange",
    "getCpuRegionRangeExpression",
    "getCpuRegionRangeID",
    # EXTENDED (F.7.22)
    "addCpuExecutableImage",
    "removeCpuExecutableImage",
    "setRegionAddressOffset",
    "setRegionRange",
    "addComponentCpu",
    "removeComponentCpu",
    "setCpuRange",
    "setCpuWidth",
    "setCpuAddressUnitBits",
    "setCpuMemoryMapRef",
    "removeCpuAddressUnitBits",
    "addCpuRegion",
    "removeCpuRegion",
    "setCpuRegionAddressOffset",
    "setCpuRegionRange",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_component(componentID: str) -> ComponentType:
    obj = resolve_handle(componentID)
    if not isinstance(obj, ComponentType):
        raise TgiError("Invalid component handle", TgiFaultCode.INVALID_ID)
    return obj


def _resolve_cpu(cpuID: str) -> ComponentType.Cpus.Cpu:
    obj = resolve_handle(cpuID)
    if not isinstance(obj, ComponentType.Cpus.Cpu):  # type: ignore[arg-type]
        raise TgiError("Invalid cpu handle", TgiFaultCode.INVALID_ID)
    return obj


def _resolve_region(regionID: str) -> ComponentType.Cpus.Cpu.Regions.Region:
    obj = resolve_handle(regionID)
    if not isinstance(obj, ComponentType.Cpus.Cpu.Regions.Region):  # type: ignore[arg-type]
        raise TgiError("Invalid cpu region handle", TgiFaultCode.INVALID_ID)
    return obj


def _text(obj: Any, attr: str) -> str | None:
    val = getattr(obj, attr, None)
    if val is None:
        return None
    return getattr(val, "value", val)


def _int_expr(expr: Any, minimum: int = 0) -> int | None:
    if expr is None:
        return None
    return _numeric(expr.value, minimum, (1 << 64) - 1, False)


def _xml_text(value: str) -> str:
    from lxml import etree

    if not isinstance(value, str):
        raise TgiError("Expected expression string", TgiFaultCode.INVALID_ARGUMENT)
    try:
        etree.Element("text").text = value
    except (ValueError, TypeError) as error:
        raise TgiError("Invalid XML text", TgiFaultCode.INVALID_ARGUMENT) from error
    return value


def _name(value: str) -> str:
    from lxml import etree
    from .name_group import _name_schema

    _xml_text(value)
    value = re.sub(r"[\t\n\r ]+", " ", value).strip(" ")
    element = etree.Element("name")
    element.text = value
    if not _name_schema("Name").validate(element):
        raise TgiError("Invalid XML Name", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _numeric(source: str, minimum: int, maximum: int, deferred: bool) -> int | None:
    try:
        value = SvExpressionParser().evaluate(source)
    except SvExpressionError as error:
        diagnostics = re.findall(r"error:\s*(.+)", str(error))
        if deferred and diagnostics and all("use of undeclared identifier" in item for item in diagnostics):
            return None
        raise TgiError("Cannot evaluate integer expression", TgiFaultCode.INVALID_ARGUMENT) from error
    if type(value) is not int or not minimum <= value <= maximum:
        raise TgiError("Expression outside unsigned integer bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _source(source: str, minimum: int, maximum: int) -> str:
    from .component import _require_text

    _xml_text(source)
    _require_text(source, "expression")
    if not source.strip():
        raise TgiError("Empty expression", TgiFaultCode.INVALID_ARGUMENT)
    _numeric(source, minimum, maximum, True)
    return source


def _update(parent: Any, attr: str, cls: type, source: str, minimum: int, maximum: int) -> None:
    current = getattr(parent, attr)
    if current is not None:
        if not isinstance(current, cls):
            raise TgiError("Invalid expression model", TgiFaultCode.INVALID_ID)
        minimum = max(minimum, current.minimum if current.minimum is not None else minimum)
        maximum = min(maximum, current.maximum if current.maximum is not None else maximum)
    source = _source(source, minimum, maximum)
    if current is None:
        current = cls(value=source)
        setattr(parent, attr, current)
    else:
        current.value = source
    register_parent(current, parent, (attr,), "single")


def _unique(items: Any, name: str) -> None:
    if any(item.name == name for item in items):
        raise TgiError("Duplicate name", TgiFaultCode.ALREADY_EXISTS)


# ---------------------------------------------------------------------------
# BASE (F.7.21)
# ---------------------------------------------------------------------------


def getComponentCpuIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return component cpu ids.

    Args:
        componentOrComponentInstanceID: Handle to a component or component instance.

    Returns:
        Child handles in source order; an empty list when no children exist.

    Section: F.7.29.8.
    """
    return component_api.getComponentCpuIDs(componentOrComponentInstanceID)


def getCpuName(cpuID: str) -> str | None:
    """Return cpu name.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.63.3.
    """
    return _text(_resolve_cpu(cpuID), "name")


def getCpuDisplayName(cpuID: str) -> str | None:
    """Return cpu display name.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.63.2.
    """
    return _text(_resolve_cpu(cpuID), "display_name")


def getCpuShortDescription(cpuID: str) -> str | None:
    """Return cpu short description.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.63.4.
    """
    return _text(_resolve_cpu(cpuID), "short_description")


def getCpuDescription(cpuID: str) -> str | None:
    """Return cpu description.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.63.1.
    """
    return _text(_resolve_cpu(cpuID), "description")


def getCpuMemoryMapRef(cpuID: str) -> str | None:
    """Return cpu memory map ref.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.21.6.
    """
    return getattr(_resolve_cpu(cpuID), "memory_map_ref", None)


def getCpuExecutableImageIDs(cpuID: str) -> list[str]:
    """Return ordered executable-image handles with parsed ownership.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Child handles in source order; an empty list when no children exist.

    Section: F.7.21.4.
    """
    cpu = _resolve_cpu(cpuID)
    for image in cpu.executable_image:
        register_parent(image, cpu, ("executable_image",), "list")
    return [get_handle(image) for image in cpu.executable_image]


def getCpuMemoryMapRefByID(cpuID: str) -> str | None:
    """Return cpu memory map ref by id.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stable owned child handle, or None when the child or reference target is absent.

    Section: F.7.21.5.
    """
    cpu = _resolve_cpu(cpuID)
    root = _root_for(cpu)
    if not isinstance(root, ComponentType) or root.memory_maps is None:
        return None
    matches = [item for item in root.memory_maps.memory_map if item.name == cpu.memory_map_ref]
    if len(matches) > 1:
        raise TgiError("Ambiguous memory map reference", TgiFaultCode.INVALID_ARGUMENT)
    if not matches:
        return None
    component_api._register_graph(root)
    return get_handle(matches[0])


def getCpuMemoryMapRefByName(cpuID: str) -> str | None:
    """Return stored memory-map reference name without target lookup.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.21.6.
    """
    return _resolve_cpu(cpuID).memory_map_ref


def getCpuRange(cpuID: str) -> int:
    """Return cpu range.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Evaluated unsigned integer. Unresolved or invalid expressions raise INVALID_ARGUMENT.

    Section: F.7.21.7.
    """
    return _numeric(_resolve_cpu(cpuID).range.value, 1, (1 << 64) - 1, False)


def getCpuRangeExpression(cpuID: str) -> str | None:
    """Return stored range source text without evaluation.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Exact stored expression source, or None when the XML child is absent.

    Section: F.7.21.8.
    """
    return _text(_resolve_cpu(cpuID), "range")


def getCpuRangeID(cpuID: str) -> str | None:
    """Return a stable range handle with parsed ownership.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stable owned child handle, or None when the child or reference target is absent.

    Section: F.7.21.9.
    """
    cpu = _resolve_cpu(cpuID)
    expr = cpu.range
    if expr is None:
        return None
    register_parent(expr, cpu, ("range",), "single")
    return get_handle(expr)


def getCpuWidth(cpuID: str) -> int:
    """Return cpu width.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Evaluated unsigned integer. Unresolved or invalid expressions raise INVALID_ARGUMENT.

    Section: F.7.21.11.
    """
    return _numeric(_resolve_cpu(cpuID).width.value, 1, (1 << 32) - 1, False)


def getCpuWidthExpression(cpuID: str) -> str | None:
    """Return stored width source text without evaluation.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Exact stored expression source, or None when the XML child is absent.

    Section: F.7.21.12.
    """
    return _text(_resolve_cpu(cpuID), "width")


def getCpuWidthID(cpuID: str) -> str | None:
    """Return a stable width handle with parsed ownership.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stable owned child handle, or None when the child or reference target is absent.

    Section: F.7.21.13.
    """
    cpu = _resolve_cpu(cpuID)
    expr = cpu.width
    if expr is None:
        return None
    register_parent(expr, cpu, ("width",), "single")
    return get_handle(expr)


def getCpuAddressUnitBits(cpuID: str) -> int:
    """Return cpu address unit bits.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Evaluated positive integer, defaulting to 8 when absent. Unresolved expressions raise INVALID_ARGUMENT.

    Section: F.7.21.1.
    """
    expr = _resolve_cpu(cpuID).address_unit_bits
    return 8 if expr is None else _numeric(expr.value, 1, (1 << 64) - 1, False)


def getCpuAddressUnitBitsExpression(cpuID: str) -> str | None:
    """Return stored address_unit_bits source text without evaluation.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Exact stored expression source, or None when the XML child is absent.

    Section: F.7.21.2.
    """
    return _text(_resolve_cpu(cpuID), "address_unit_bits")


def getCpuAddressUnitBitsID(cpuID: str) -> str | None:
    """Return a stable address_unit_bits handle with parsed ownership.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Stable owned child handle, or None when the child or reference target is absent.

    Section: F.7.21.3.
    """
    cpu = _resolve_cpu(cpuID)
    expr = cpu.address_unit_bits
    if expr is None:
        return None
    register_parent(expr, cpu, ("address_unit_bits",), "single")
    return get_handle(expr)


def getCpuRegionIDs(cpuID: str) -> list[str]:
    """Return cpu region ids.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        Child handles in source order; an empty list when no children exist.

    Section: F.7.21.10.
    """
    cpu = _resolve_cpu(cpuID)
    if cpu.regions is None:
        return []
    register_parent(cpu.regions, cpu, ("regions",), "single")
    for region in cpu.regions.region:
        register_parent(region, cpu.regions, ("region",), "list")
    return [get_handle(region) for region in cpu.regions.region]


def getCpuRegionName(regionID: str) -> str | None:
    """Return cpu region name.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.63.3.
    """
    return _text(_resolve_region(regionID), "name")


def getCpuRegionDisplayName(regionID: str) -> str | None:
    """Return cpu region display name.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.63.2.
    """
    return _text(_resolve_region(regionID), "display_name")


def getCpuRegionShortDescription(regionID: str) -> str | None:
    """Return cpu region short description.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.63.4.
    """
    return _text(_resolve_region(regionID), "short_description")


def getCpuRegionDescription(regionID: str) -> str | None:
    """Return cpu region description.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Stored lexical text, or None when optional content is absent.

    Section: F.7.63.1.
    """
    return _text(_resolve_region(regionID), "description")


def getCpuRegionAddressOffset(regionID: str) -> int | None:
    """Return cpu region address offset.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Evaluated unsigned integer. Unresolved or invalid expressions raise INVALID_ARGUMENT.

    Section: F.7.11.16.
    """
    return _int_expr(getattr(_resolve_region(regionID), "address_offset", None))


def getCpuRegionAddressOffsetExpression(regionID: str) -> str | None:
    """Return cpu region address offset expression.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Exact stored expression source, or None when the XML child is absent.

    Section: F.7.11.17.
    """
    return _text(_resolve_region(regionID), "address_offset")


def getCpuRegionAddressOffsetID(regionID: str) -> str:
    """Return cpu region address offset id.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Stable owned child handle, or None when the child or reference target is absent.

    Section: F.7.11.18.
    """
    region = _resolve_region(regionID)
    register_parent(region.address_offset, region, ("address_offset",), "single")
    return get_handle(region.address_offset)


def getCpuRegionRange(regionID: str) -> int | None:
    """Return cpu region range.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Evaluated unsigned integer. Unresolved or invalid expressions raise INVALID_ARGUMENT.

    Section: F.7.11.19.
    """
    return _int_expr(getattr(_resolve_region(regionID), "range", None), 1)


def getCpuRegionRangeExpression(regionID: str) -> str | None:
    """Return cpu region range expression.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Exact stored expression source, or None when the XML child is absent.

    Section: F.7.11.20.
    """
    return _text(_resolve_region(regionID), "range")


def getCpuRegionRangeID(regionID: str) -> str:
    """Return cpu region range id.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        Stable owned child handle, or None when the child or reference target is absent.

    Section: F.7.11.21.
    """
    region = _resolve_region(regionID)
    register_parent(region.range, region, ("range",), "single")
    return get_handle(region.range)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.22)
# ---------------------------------------------------------------------------


def addCpuExecutableImage(cpuID: str, name: str, imageId: str) -> str:
    """Add a typed CPU executable image.

    Args:
        cpuID: Handle to a CPU element.
        name: Unique XML Name of the new element.
        imageId: Component-wide unique image identifier, normalized as xs:token.

    Returns:
        Handle to the newly owned generated element.

    Section: F.7.22.1.
    """
    cpu = _resolve_cpu(cpuID)
    name = _name(name)
    _xml_text(imageId)
    component_api._require_text(imageId, "imageId")
    imageId = re.sub(r"[\t\n\r ]+", " ", imageId).strip(" ")
    images = [obj for obj, _ in _walk(_root_for(cpu)) if isinstance(obj, ExecutableImage)]
    if any(image.name == name or image.image_id == imageId for image in images):
        raise TgiError("Duplicate executable image name or imageId", TgiFaultCode.ALREADY_EXISTS)
    image = ExecutableImage(name=name, image_id=imageId)
    return component_api._append_child(cpu, "executable_image", image)


def addComponentCpu(componentID: str, name: str, memoryMapRef: str, range: str, width: str) -> str:
    """Add a typed CPU through the component factory.

    Args:
        componentID: Handle to a component.
        name: Unique XML Name of the new element.
        memoryMapRef: XML Name of a memory map in the containing component.
        range: Positive unsigned 64-bit expression source.
        width: Positive unsigned 32-bit expression source.

    Returns:
        Handle to the newly owned generated element.

    Section: F.7.30.7.
    """
    name = _name(name)
    memoryMapRef = _name(memoryMapRef)
    range = _source(range, 1, (1 << 64) - 1)
    width = _source(width, 1, (1 << 32) - 1)
    return component_api.addComponentCpu(componentID, name, memoryMapRef, range, width)


def removeCpuExecutableImage(executableImageID: str) -> bool:
    """Remove the owned CPU executable image and its descendant handles.

    Args:
        executableImageID: Handle to an executable image owned by a CPU.

    Returns:
        True when removed; False when optional content is already absent.

    Section: F.7.22.4.
    """
    image = resolve_handle(executableImageID)
    owner = _register_owned_child(image, ComponentType.Cpus.Cpu) if isinstance(image, ExecutableImage) else None
    if owner is None:
        raise TgiError("Invalid CPU executable image", TgiFaultCode.INVALID_ID)
    component_api._list_attr(owner, "executable_image")
    return component_api._remove_child(executableImageID, ExecutableImage, "executable image")


def removeComponentCpu(cpuID: str) -> bool:
    """Remove the owned CPU through the component API.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        True when removed; False when optional content is already absent.

    Section: F.7.30.36.
    """
    region = _resolve_cpu(cpuID)
    root = _root_for(region)
    if isinstance(root, ComponentType) and root.cpus is not None:
        component_api._list_attr(root.cpus, "cpu")
    return component_api.removeComponentCpu(cpuID)


def setCpuRange(cpuID: str, range: str) -> bool:
    """Set cpu range while preserving expression identity.

    Args:
        cpuID: Handle to a CPU element.
        range: Positive unsigned 64-bit expression source.

    Returns:
        True after successful validation and mutation.

    Section: F.7.22.8.
    """
    _update(_resolve_cpu(cpuID), "range", UnsignedPositiveLongintExpression, range, 1, (1 << 64) - 1)
    return True


def setCpuWidth(cpuID: str, width: str) -> bool:
    """Set cpu width while preserving expression identity.

    Args:
        cpuID: Handle to a CPU element.
        width: Positive unsigned 32-bit expression source.

    Returns:
        True after successful validation and mutation.

    Section: F.7.22.9.
    """
    _update(_resolve_cpu(cpuID), "width", UnsignedPositiveIntExpression, width, 1, (1 << 32) - 1)
    return True


def setCpuAddressUnitBits(cpuID: str, addressUnitBits: str) -> bool:
    """Set cpu address unit bits while preserving expression identity.

    Args:
        cpuID: Handle to a CPU element.
        addressUnitBits: Positive unsigned 64-bit address-unit-size expression source.

    Returns:
        True after successful validation and mutation.

    Section: F.7.22.6.
    """
    _update(_resolve_cpu(cpuID), "address_unit_bits", AddressUnitBits, addressUnitBits, 1, (1 << 64) - 1)
    return True


def setCpuMemoryMapRef(cpuID: str, value: str) -> bool:
    """Set cpu memory map ref while preserving expression identity.

    Args:
        cpuID: Handle to a CPU element.
        value: XML Name of the referenced memory map.

    Returns:
        True after successful validation and mutation.

    Section: F.7.22.7.
    """
    cpu = _resolve_cpu(cpuID)
    value = _name(value)
    cpu.memory_map_ref = value
    return True


def removeCpuAddressUnitBits(cpuID: str) -> bool:
    """Remove the owned addressUnitBits expression and invalidate its handle.

    Args:
        cpuID: Handle to a CPU element.

    Returns:
        True when removed; False when optional content is already absent.

    Section: F.7.22.3.
    """
    cpu = _resolve_cpu(cpuID)
    if cpu.address_unit_bits is None:
        return False
    register_parent(cpu.address_unit_bits, cpu, ("address_unit_bits",), "single")
    return detach_child_by_handle(get_handle(cpu.address_unit_bits))


def addCpuRegion(cpuID: str, name: str, addressOffset: str, range: str) -> str:
    """Add a typed CPU region.

    Args:
        cpuID: Handle to a CPU element.
        name: Unique XML Name of the new element.
        addressOffset: Unsigned 64-bit address offset expression source.
        range: Positive unsigned 64-bit expression source.

    Returns:
        Handle to the newly owned generated element.

    Section: F.7.22.2.
    """
    cpu = _resolve_cpu(cpuID)
    name = _name(name)
    _unique(cpu.regions.region if cpu.regions else [], name)
    offset = _source(addressOffset, 0, (1 << 64) - 1)
    size = _source(range, 1, (1 << 64) - 1)
    region = ComponentType.Cpus.Cpu.Regions.Region(
        name=name,
        address_offset=UnsignedLongintExpression(value=offset),
        range=UnsignedPositiveLongintExpression(value=size),
    )
    if cpu.regions is None:
        cpu.regions = ComponentType.Cpus.Cpu.Regions()
    register_parent(cpu.regions, cpu, ("regions",), "single")
    return component_api._append_child(cpu.regions, "region", region)


def removeCpuRegion(regionID: str) -> bool:
    """Remove the owned CPU region and its descendant handles.

    Args:
        regionID: Handle to a CPU region.

    Returns:
        True when removed; False when optional content is already absent.

    Section: F.7.22.5.
    """
    region = _resolve_region(regionID)
    holder = _register_owned_child(region, ComponentType.Cpus.Cpu.Regions)
    if holder is None:
        raise TgiError("Region has no owning CPU", TgiFaultCode.INVALID_ID)
    _register_owned_child(holder, ComponentType.Cpus.Cpu)
    component_api._list_attr(holder, "region")
    return component_api._remove_child(regionID, ComponentType.Cpus.Cpu.Regions.Region, "region")


def setRegionAddressOffset(regionID: str, addressOffset: str) -> bool:
    """Set region address offset while preserving expression identity.

    Args:
        regionID: Handle to a CPU region.
        addressOffset: Unsigned 64-bit address offset expression source.

    Returns:
        True after successful validation and mutation.

    Section: F.7.22.10.
    """
    _update(_resolve_region(regionID), "address_offset", UnsignedLongintExpression, addressOffset, 0, (1 << 64) - 1)
    return True


def setCpuRegionAddressOffset(regionID: str, value: str) -> bool:
    """Set cpu region address offset while preserving expression identity.

    Args:
        regionID: Handle to a CPU region.
        value: Expression source text for this compatibility setter.

    Returns:
        True after successful validation and mutation.

    Section: F.7.22.10.
    """
    return setRegionAddressOffset(regionID, value)


def setRegionRange(regionID: str, range: str) -> bool:
    """Set region range while preserving expression identity.

    Args:
        regionID: Handle to a CPU region.
        range: Positive unsigned 64-bit expression source.

    Returns:
        True after successful validation and mutation.

    Section: F.7.22.11.
    """
    _update(_resolve_region(regionID), "range", UnsignedPositiveLongintExpression, range, 1, (1 << 64) - 1)
    return True


def setCpuRegionRange(regionID: str, value: str) -> bool:
    """Set cpu region range while preserving expression identity.

    Args:
        regionID: Handle to a CPU region.
        value: Expression source text for this compatibility setter.

    Returns:
        True after successful validation and mutation.

    Section: F.7.22.11.
    """
    return setRegionRange(regionID, value)
