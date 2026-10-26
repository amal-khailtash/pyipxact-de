"""Scoped host-supplied Design context for an invoked TGI generator."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from org.accellera.ipxact.v1685_2022 import Design

from .core import TgiError, TgiFaultCode, resolve_handle

_designs: ContextVar[tuple[str, str] | None] = ContextVar("ipxact_generator_designs", default=None)


def _require_design(design_id: str) -> str:
    """Require a live supported Design handle before establishing or reading context."""
    if not isinstance(design_id, str) or not isinstance(resolve_handle(design_id), Design):
        raise TgiError("Invalid generator Design handle", TgiFaultCode.INVALID_ID)
    return design_id


@contextmanager
def generator_context(current_design_id: str, top_design_id: str | None = None) -> Iterator[None]:
    """Supply current and top Design handles for one invocation, restoring any outer context."""
    current = _require_design(current_design_id)
    top = current if top_design_id is None else _require_design(top_design_id)
    token = _designs.set((current, top))
    try:
        yield
    finally:
        _designs.reset(token)


def _design_context_id(top: bool) -> str | None:
    """Return the selected generator Design, without inferring context from registry order."""
    if not isinstance(top, bool):
        raise TgiError("top requires a Boolean", TgiFaultCode.INVALID_ARGUMENT)
    context = _designs.get()
    return None if context is None else _require_design(context[1 if top else 0])
