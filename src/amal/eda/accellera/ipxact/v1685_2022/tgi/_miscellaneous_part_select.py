"""Part-select operations from IEEE 1685-2022 F.7.59 and F.7.60."""

from org.accellera.ipxact.v1685_2022.index import Index
from org.accellera.ipxact.v1685_2022.indices import Indices
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.part_select import PartSelect
from org.accellera.ipxact.v1685_2022.range import Range
from org.accellera.ipxact.v1685_2022.right import Right

from .address_space import _register_owned_child
from .component import _register_graph
from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    resolve_handle,
)
from .port_map import _integer, _parts, _source

__all__: list[str] = [
    "getPartSelectIndexIDs",
    "getPartSelectIndices",
    "getPartSelectIndicesExpression",
    "getPartSelectRange",
    "getPartSelectRangeExpression",
    "getPartSelectRangeLeftID",
    "getPartSelectRangeRightID",
    "addPartSelectIndex",
    "removePartSelectIndex",
    "setPartSelectRange",
    "removePartSelectRange",
]

_UINT32_MAX = (1 << 32) - 1


def _part_select(handle: str) -> PartSelect:
    part_select = resolve_handle(handle)
    if not isinstance(part_select, PartSelect):
        raise TgiError("Invalid partSelect handle", TgiFaultCode.INVALID_ID)
    _parts(part_select)
    _register_graph(part_select)
    return part_select


def _indices(part_select: PartSelect) -> tuple[Range | None, Indices | None, list[Index]]:
    range_node, indices_node = _parts(part_select)
    if indices_node is None:
        return range_node, None, []
    if not isinstance(indices_node, Indices) or not isinstance(indices_node.index, (list, tuple)):
        raise TgiError("Invalid indices model", TgiFaultCode.INVALID_ID)
    items = list(indices_node.index)
    if any(not isinstance(item, Index) or not isinstance(item.value, str) for item in items):
        raise TgiError("Invalid index model", TgiFaultCode.INVALID_ID)
    return range_node, indices_node, items


def _range(part_select: PartSelect) -> Range | None:
    range_node, _ = _parts(part_select)
    if range_node is None:
        return None
    if (
        not isinstance(range_node, Range)
        or not isinstance(range_node.left, Left)
        or not isinstance(range_node.left.value, str)
        or not isinstance(range_node.right, Right)
        or not isinstance(range_node.right.value, str)
    ):
        raise TgiError("Invalid range model", TgiFaultCode.INVALID_ID)
    return range_node


def _unsigned32(source: str) -> int:
    value = _integer(source, _UINT32_MAX)
    if value is None:
        raise TgiError("Cannot evaluate unsigned 32-bit expression", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _normalize_choice(part_select: PartSelect) -> list[Range | Indices]:
    value = part_select.range_or_indices
    if value is None:
        children: list[Range | Indices] = []
    elif isinstance(value, tuple):
        children = list(value)
        part_select.range_or_indices = children
    elif isinstance(value, list):
        children = value
    else:
        children = [value]
        part_select.range_or_indices = children
    _register_graph(part_select)
    return children


def _compact_choice(part_select: PartSelect, children: list[Range | Indices]) -> None:
    children.sort(key=lambda child: 0 if isinstance(child, Indices) else 1)
    if not children:
        part_select.range_or_indices = None
    elif len(children) == 1:
        part_select.range_or_indices = children[0]
    else:
        part_select.range_or_indices = children
    _register_graph(part_select)


def _register_part_select_children(part_select: PartSelect) -> None:
    """Register child handles against their exact singleton or choice owner."""
    value = part_select.range_or_indices
    if isinstance(value, (list, tuple)):
        for child in value:
            register_parent(child, part_select, ("range_or_indices",), "list")
    elif isinstance(value, (Range, Indices)):
        register_parent(value, part_select, ("range_or_indices",), "single")
    _register_graph(part_select)


def getPartSelectIndexIDs(partSelectID: str) -> list[str]:
    """Return handles for the generated Index children of a partSelect."""
    part_select = _part_select(partSelectID)
    _, _, items = _indices(part_select)
    _register_part_select_children(part_select)
    return [get_handle(item) for item in items]


def getPartSelectIndices(partSelectID: str) -> list[int]:
    """Return evaluated unsigned 32-bit indices; unresolved symbols fault."""
    part_select = _part_select(partSelectID)
    _, _, items = _indices(part_select)
    return [_unsigned32(item.value) for item in items]


def getPartSelectIndicesExpression(partSelectID: str) -> list[str]:
    """Return each stored index expression without evaluating it."""
    part_select = _part_select(partSelectID)
    _, _, items = _indices(part_select)
    return [item.value for item in items]


def getPartSelectRange(partSelectID: str) -> list[int] | None:
    """Return evaluated left/right range endpoints, or None when absent."""
    part_select = _part_select(partSelectID)
    range_node = _range(part_select)
    if range_node is None:
        return None
    return [
        _unsigned32(range_node.left.value),
        _unsigned32(range_node.right.value),
    ]


def getPartSelectRangeExpression(partSelectID: str) -> list[str] | None:
    """Return raw left and right range expressions, or None when absent."""
    part_select = _part_select(partSelectID)
    range_node = _range(part_select)
    if range_node is None:
        return None
    return [range_node.left.value, range_node.right.value]


def getPartSelectRangeLeftID(partSelectID: str) -> str | None:
    """Return a handle to the actual generated Left child, when present."""
    part_select = _part_select(partSelectID)
    range_node = _range(part_select)
    return get_handle(range_node.left) if range_node is not None else None


def getPartSelectRangeRightID(partSelectID: str) -> str | None:
    """Return a handle to the actual generated Right child, when present."""
    part_select = _part_select(partSelectID)
    range_node = _range(part_select)
    return get_handle(range_node.right) if range_node is not None else None


def addPartSelectIndex(partSelectID: str, value: str) -> str:
    """Append an Index while retaining the range choice and index expressions."""
    part_select = _part_select(partSelectID)
    value = _source(value, maximum=_UINT32_MAX)
    _, indices_node, _ = _indices(part_select)
    children = _normalize_choice(part_select)
    if indices_node is None:
        indices_node = Indices(index=[])
        children.append(indices_node)
    elif isinstance(indices_node.index, tuple):
        indices_node.index = list(indices_node.index)
    new_index = Index(value=value)
    indices_node.index.append(new_index)
    _compact_choice(part_select, children)
    return get_handle(new_index)


def removePartSelectIndex(indexID: str) -> bool:
    """Remove exactly the owned Index and prune an empty Indices branch."""
    index = resolve_handle(indexID)
    if not isinstance(index, Index):
        raise TgiError("Invalid index handle", TgiFaultCode.INVALID_ID)
    parent_info = get_parent_info(indexID)
    holder = resolve_handle(parent_info.parent_handle) if parent_info is not None else None
    if not isinstance(holder, Indices):
        holder = _register_owned_child(index, Indices)
    if not isinstance(holder, Indices):
        raise TgiError("Index has no owning Indices container", TgiFaultCode.INVALID_ID)
    if not isinstance(holder.index, (list, tuple)) or not any(item is index for item in holder.index):
        raise TgiError("Index has no owning list entry", TgiFaultCode.INVALID_ID)
    part_info = get_parent_info(get_handle(holder))
    part_select = resolve_handle(part_info.parent_handle) if part_info is not None else None
    if not isinstance(part_select, PartSelect):
        part_select = _register_owned_child(holder, PartSelect)
    if not isinstance(part_select, PartSelect):
        raise TgiError("Indices has no owning partSelect", TgiFaultCode.INVALID_ID)
    children = _normalize_choice(part_select)
    if holder not in children:
        raise TgiError("Indices is not a partSelect child", TgiFaultCode.INVALID_ID)
    if isinstance(holder.index, tuple):
        holder.index = list(holder.index)
    _register_graph(part_select)
    if not detach_child_by_handle(indexID):
        raise TgiError("Could not remove index", TgiFaultCode.INVALID_ID)
    if not holder.index:
        holder_handle = get_handle(holder)
        _register_part_select_children(part_select)
        if not detach_child_by_handle(holder_handle):
            raise TgiError("Could not remove empty Indices", TgiFaultCode.INVALID_ID)
    _compact_choice(part_select, children)
    return True


def setPartSelectRange(partSelectID: str, left: str, right: str) -> bool:
    """Set range bounds while keeping existing child wrappers and sibling indices."""
    part_select = _part_select(partSelectID)
    old_range = _range(part_select)
    left_value = _source(left, old_range.left if old_range is not None else None, _UINT32_MAX)
    right_value = _source(right, old_range.right if old_range is not None else None, _UINT32_MAX)
    children = _normalize_choice(part_select)
    if old_range is None:
        new_range = Range(left=Left(value=left_value), right=Right(value=right_value))
        children.append(new_range)
    else:
        old_range.left.value = left_value
        old_range.right.value = right_value
    _compact_choice(part_select, children)
    return True


def removePartSelectRange(partSelectID: str) -> bool:
    """Remove the owned Range branch and invalidate its Range/Left/Right handles."""
    part_select = _part_select(partSelectID)
    range_node = _range(part_select)
    if range_node is None:
        return False
    children = _normalize_choice(part_select)
    range_handle = get_handle(range_node)
    if range_node not in children or not detach_child_by_handle(range_handle):
        raise TgiError("Could not remove range", TgiFaultCode.INVALID_ID)
    _compact_choice(part_select, children)
    return True
