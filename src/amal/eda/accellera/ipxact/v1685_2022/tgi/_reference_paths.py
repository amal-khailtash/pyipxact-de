"""Shared mutation of generated bank and register-file reference paths."""

from org.accellera.ipxact.v1685_2022 import BankRef, RegisterFileRef

from ._model import _owned_list_ids, _reference_list
from .address_space import _remove_owned
from .component import _list_attr
from .core import TgiError, TgiFaultCode, get_handle, resolve_handle
from .port_map import _name


def _append_reference_path[T: BankRef | RegisterFileRef](
    owner: object, source: str, attribute: str, model_type: type[T]
) -> str:
    """Append a generated named reference to its ordered owned path."""
    _reference_list(owner, attribute, model_type)
    child = model_type(**{attribute: _name(source, "Name")})
    children = _list_attr(owner, attribute)
    children.append(child)
    _owned_list_ids(owner, children, attribute)
    return get_handle(child)


def _remove_reference_path[T: BankRef | RegisterFileRef](
    owner: object, reference_id: str, attribute: str, model_type: type[T]
) -> bool:
    """Remove a member of a validated owned path and invalidate its descendants."""
    child = resolve_handle(reference_id)
    if not isinstance(child, model_type):
        raise TgiError("Invalid path reference handle", TgiFaultCode.INVALID_ID)
    children = _reference_list(owner, attribute, model_type)
    if not any(item is child for item in children):
        raise TgiError("Reference is not in the owning path", TgiFaultCode.INVALID_ID)
    _owned_list_ids(owner, children, attribute)
    _list_attr(owner, attribute)
    return _remove_owned(reference_id, model_type, type(owner), "path reference")
