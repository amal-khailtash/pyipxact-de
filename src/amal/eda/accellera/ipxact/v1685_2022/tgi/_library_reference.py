"""Shared generated library-reference validation and identity-preserving mutation."""

from org.accellera.ipxact.v1685_2022 import ConfigurableLibraryRefType, LibraryRefType

from ._expressions import _xml_text
from .core import TgiError, TgiFaultCode, register_parent
from .instantiation import _validated_vlnv


def _xml_vlnv(value: tuple[str, str, str, str]) -> tuple[str, str, str, str]:
    parts = _validated_vlnv(value)
    for part in parts:
        _xml_text(part)
    return parts


def _set_reference[T: (LibraryRefType, ConfigurableLibraryRefType)](
    owner: object, attribute: str, model_type: type[T], value: tuple[str, str, str, str]
) -> T:
    parts = _xml_vlnv(value)
    ref = getattr(owner, attribute)
    if ref is not None and not isinstance(ref, model_type):
        raise TgiError(f"Invalid {attribute} model", TgiFaultCode.INVALID_ID)
    if ref is None:
        ref = model_type(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])
        setattr(owner, attribute, ref)
    else:
        ref.vendor, ref.library, ref.name, ref.version = parts
    register_parent(ref, owner, (attribute,), "single")
    return ref
