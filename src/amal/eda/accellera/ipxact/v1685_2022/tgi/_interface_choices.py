"""Typed memory-map and transparent-bridge choices on indirect interfaces."""

from collections.abc import Sequence

from org.accellera.ipxact.v1685_2022 import IndirectInterface, TransparentBridge

from .core import TgiError, TgiFaultCode
from .port_map import _name

_INTERFACE_CHOICE = "memory_map_ref_or_transparent_bridge"


def _indirect_interface_choice(owner: IndirectInterface) -> tuple[str | None, Sequence[TransparentBridge]]:
    """Read a generated indirect interface choice without normalizing its storage."""
    values = owner.memory_map_ref_or_transparent_bridge
    if not isinstance(values, (list, tuple)):
        raise TgiError("Invalid indirect interface choice", TgiFaultCode.INVALID_ID)
    if not values:
        return None, ()
    if len(values) == 1 and isinstance(values[0], str):
        try:
            return _name(values[0], "Name"), ()
        except TgiError as error:
            raise TgiError("Invalid indirect interface memoryMapRef", TgiFaultCode.INVALID_ID) from error
    if all(isinstance(value, TransparentBridge) for value in values):
        return None, values
    raise TgiError("Invalid indirect interface choice", TgiFaultCode.INVALID_ID)
