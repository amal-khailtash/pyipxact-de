"""Typed range and part-select choice operations shared by TGI categories."""

from collections.abc import Sequence

from org.accellera.ipxact.v1685_2022 import Indices, Left, PartSelect, Range, Right

from ._expressions import _source
from .core import TgiError, TgiFaultCode


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
