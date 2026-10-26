"""Shared validation of generated address-space and memory-map reference choices."""

from org.accellera.ipxact.v1685_2022 import MemoryRemapRef

from ._model import _owned_list_ids
from .component import _register_graph
from .core import TgiError, TgiFaultCode, detach_child_by_handle, get_handle

_REFERENCE_CHOICE = "address_space_ref_or_memory_map_ref_or_memory_remap_ref"


def _reference_choice[A, M](
    owner: object, address_type: type[A], map_type: type[M]
) -> tuple[A | None, M | None, MemoryRemapRef | None]:
    """Validate the generated address-space or memory-map/remap reference choice."""
    values = getattr(owner, _REFERENCE_CHOICE)
    if not isinstance(values, (list, tuple)):
        raise TgiError("Invalid field reference choice", TgiFaultCode.INVALID_ID)
    if not values:
        return None, None, None
    if len(values) == 1 and isinstance(values[0], address_type):
        result = (values[0], None, None)
    elif (
        len(values) in (1, 2)
        and isinstance(values[0], map_type)
        and (len(values) == 1 or isinstance(values[1], MemoryRemapRef))
    ):
        result = (None, values[0], values[1] if len(values) == 2 else None)
    else:
        raise TgiError("Invalid field reference choice", TgiFaultCode.INVALID_ID)
    _owned_list_ids(owner, values, _REFERENCE_CHOICE)
    return result


def _update_reference[T](current: T | None, replacement: T, attribute: str) -> T:
    """Preserve an existing named wrapper while updating only its source."""
    if current is None:
        return replacement
    setattr(current, attribute, getattr(replacement, attribute))
    return current


def _set_reference_choice[A, M](
    owner: object, replacement: A | M | MemoryRemapRef, attribute: str, address_type: type[A], map_type: type[M]
) -> bool:
    """Update a reference choice, invalidating only alternatives removed from it."""
    address, memory_map, remap = _reference_choice(owner, address_type, map_type)
    if attribute == "address_space_ref":
        kept = [_update_reference(address, replacement, attribute)]
    elif attribute == "memory_map_ref":
        kept = [_update_reference(memory_map, replacement, attribute)]
        if remap is not None:
            kept.append(remap)
    else:
        if memory_map is None:
            raise TgiError("memoryRemapRef requires a memoryMapRef", TgiFaultCode.INVALID_ARGUMENT)
        kept = [memory_map, _update_reference(remap, replacement, attribute)]
    old = list(getattr(owner, _REFERENCE_CHOICE))
    setattr(owner, _REFERENCE_CHOICE, old)
    for child in tuple(old):
        if not any(child is retained for retained in kept):
            _register_graph(child)
            detach_child_by_handle(get_handle(child))
    setattr(owner, _REFERENCE_CHOICE, kept)
    _owned_list_ids(owner, kept, _REFERENCE_CHOICE)
    for child in kept:
        _register_graph(child)
    return True
