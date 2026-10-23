"""Lifetime of objects indexed by the shared TGI ownership manager."""

import gc
import weakref
from dataclasses import dataclass

from amal.eda.accellera.ipxact.v1685_2022.tgi.core import HandleManager


@dataclass
class _Child:
    name: str


def test_parent_registration_retains_child_until_owned_handles_are_forgotten() -> None:
    manager = HandleManager()
    parent = object()
    child = _Child("owned")
    reference = weakref.ref(child)
    manager.register_parent(child, parent, ("child",), "single")
    del child
    gc.collect()
    retained = reference()
    assert retained is not None
    child_handle = manager.get(retained)
    info = manager.get_parent_info(child_handle)
    assert info is not None
    assert manager.resolve(info.parent_handle) is parent
    del retained
    assert manager.forget(manager.get(parent))
    gc.collect()
    assert reference() is None
