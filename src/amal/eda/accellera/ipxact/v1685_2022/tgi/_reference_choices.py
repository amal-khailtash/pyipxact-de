"""Shared validation of generated address-space and memory-map reference choices."""

from org.accellera.ipxact.v1685_2022 import MemoryRemapRef

from ._model import _owned_list_ids
from .core import TgiError, TgiFaultCode

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
