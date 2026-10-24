"""Generated model traversal with immediate owning fields for TGI handles."""

from collections.abc import Iterable, Iterator
from dataclasses import fields, is_dataclass

from .core import get_handle, register_parent


def _owned_list_ids(owner: object, children: Iterable[object], attribute: str) -> list[str]:
    """Return ordered child handles with their immediate list ownership restored."""
    handles: list[str] = []
    for child in children:
        register_parent(child, owner, (attribute,), "list")
        handles.append(get_handle(child))
    return handles


def _walk_model(root: object) -> Iterator[tuple[object, object | None, str | None, str]]:
    """Yield each generated dataclass object with its direct owning field."""
    pending = [(root, None, None, "single")]
    seen: set[int] = set()
    while pending:
        obj, parent, attribute, container = pending.pop()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        yield obj, parent, attribute, container
        if not is_dataclass(obj) or isinstance(obj, type):
            continue
        for model_field in fields(obj):
            value = getattr(obj, model_field.name)
            if is_dataclass(value) and not isinstance(value, type):
                pending.append((value, obj, model_field.name, "single"))
            elif isinstance(value, (list, tuple)):
                pending.extend(
                    (child, obj, model_field.name, "list")
                    for child in value
                    if is_dataclass(child) and not isinstance(child, type)
                )
