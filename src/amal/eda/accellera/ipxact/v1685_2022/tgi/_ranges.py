"""Typed range and part-select choice operations shared by TGI categories."""

from collections.abc import Sequence
from typing import Protocol

from org.accellera.ipxact.v1685_2022 import Indices, PartSelect
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.range import Range
from org.accellera.ipxact.v1685_2022.right import Right

from ._expressions import _source
from .core import TgiError, TgiFaultCode, detach_child_by_handle, get_handle, register_parent, resolve_handle


class _RangeOwner(Protocol):
    """Generated objects exposing an optional range child."""

    range: Range | None


def _range_endpoint[T: (Left, Right)](owner: _RangeOwner, attribute: str, expected: type[T]) -> T | None:
    """Resolve a typed endpoint and restore immediate range ownership."""
    if owner.range is None:
        return None
    if not isinstance(owner.range, Range):
        raise TgiError("Invalid range element", TgiFaultCode.INVALID_ID)
    register_parent(owner.range, owner, ("range",), "single")
    endpoint = getattr(owner.range, attribute)
    if endpoint is None:
        return None
    if not isinstance(endpoint, expected):
        raise TgiError("Invalid range endpoint", TgiFaultCode.INVALID_ID)
    register_parent(endpoint, owner.range, (attribute,), "single")
    return endpoint


def _range_sources(left_id: str | None, right_id: str | None) -> tuple[str | None, str | None]:
    """Return stored endpoint sources without evaluating unresolved expressions."""
    from .miscellaneous import getExpression

    return (None if left_id is None else getExpression(left_id), None if right_id is None else getExpression(right_id))


def _range_value(endpoint_id: str | None) -> int | None:
    """Evaluate an unsigned 32-bit range endpoint within declared bounds."""
    from .miscellaneous import getExpressionIntValue

    if endpoint_id is None:
        return None
    value = getExpressionIntValue(endpoint_id)
    endpoint = resolve_handle(endpoint_id)
    if not isinstance(endpoint, (Left, Right)):
        raise TgiError("Invalid range endpoint", TgiFaultCode.INVALID_ID)
    minimum, maximum = endpoint.minimum, endpoint.maximum
    if (
        not 0 <= value < (1 << 32)
        or (minimum is not None and value < minimum)
        or (maximum is not None and value > maximum)
        or (minimum is not None and maximum is not None and minimum > maximum)
    ):
        raise TgiError("Range endpoint outside unsigned integer bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _set_range(owner: _RangeOwner, sources: Sequence[str]) -> bool:
    """Set ordered endpoint sources after validating both, preserving metadata."""
    from .miscellaneous import _expression_source, setExpressionValue

    if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)) or len(sources) != 2:
        raise TgiError("Range requires two expression strings", TgiFaultCode.INVALID_ARGUMENT)
    left = _range_endpoint(owner, "left", Left)
    right = _range_endpoint(owner, "right", Right)
    new_left = left if left is not None else Left(value="")
    new_right = right if right is not None else Right(value="")
    for endpoint, source in ((new_left, sources[0]), (new_right, sources[1])):
        if endpoint.minimum is not None and endpoint.maximum is not None and endpoint.minimum > endpoint.maximum:
            raise TgiError("Range endpoint bounds are reversed", TgiFaultCode.INVALID_ARGUMENT)
        _expression_source(source, endpoint)
    for endpoint, source in ((new_left, sources[0]), (new_right, sources[1])):
        setExpressionValue(get_handle(endpoint), source)
    if owner.range is None:
        owner.range = Range(left=new_left, right=new_right)
    else:
        owner.range.left = new_left
        owner.range.right = new_right
    register_parent(owner.range, owner, ("range",), "single")
    register_parent(new_left, owner.range, ("left",), "single")
    register_parent(new_right, owner.range, ("right",), "single")
    return True


def _remove_range(owner: _RangeOwner) -> bool:
    """Detach a typed range and invalidate its removed descendant handles."""
    if owner.range is None:
        return False
    if not isinstance(owner.range, Range):
        raise TgiError("Invalid range element", TgiFaultCode.INVALID_ID)
    register_parent(owner.range, owner, ("range",), "single")
    return detach_child_by_handle(get_handle(owner.range))


def _array(value: Sequence[str], argument: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TgiError(f"{argument} must be a sequence", TgiFaultCode.INVALID_ARGUMENT)
    return list(value)


def _range_plan(value: Sequence[str], current: Range | None) -> tuple[str, str]:
    values = _array(value, "range")
    if len(values) != 2:
        raise TgiError("range must contain left and right", TgiFaultCode.INVALID_ARGUMENT)
    if current is not None and (
        not isinstance(current, Range) or not isinstance(current.left, Left) or not isinstance(current.right, Right)
    ):
        raise TgiError("Invalid range model", TgiFaultCode.INVALID_ID)
    return (
        _source(values[0], current.left if current else None),
        _source(values[1], current.right if current else None),
    )


def _apply_range(current: Range | None, values: tuple[str, str]) -> Range:
    if current is None:
        return Range(left=Left(value=values[0]), right=Right(value=values[1]))
    current.left.value, current.right.value = values
    return current


def _parts(part_select: PartSelect | None) -> tuple[Range | None, Indices | None]:
    if part_select is None:
        return None, None
    if not isinstance(part_select, PartSelect):
        raise TgiError("Invalid partSelect model", TgiFaultCode.INVALID_ID)
    value = part_select.range_or_indices
    if value is None:
        return None, None
    children = list(value) if isinstance(value, (list, tuple)) else [value]
    ranges = [item for item in children if isinstance(item, Range)]
    indices = [item for item in children if isinstance(item, Indices)]
    if len(ranges) > 1 or len(indices) > 1 or len(ranges) + len(indices) != len(children):
        raise TgiError("Invalid partSelect children", TgiFaultCode.INVALID_ID)
    return (ranges[0] if ranges else None, indices[0] if indices else None)
