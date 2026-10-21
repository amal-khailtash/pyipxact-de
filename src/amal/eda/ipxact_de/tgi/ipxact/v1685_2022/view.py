"""View category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.87) and EXTENDED (F.7.88) API for *view* elements.
A ``view`` in IP-XACT names a particular representation of a component
and references component instantiations, bus interfaces, filesets, env
identifiers, etc. This module exposes only the standard public TGI
functions – no more, no less – following the tolerant BASE / strict
EXTENDED convention used across the codebase.

Notes / assumptions:
* We treat any object whose type name ends with ``View`` or which has
  characteristic attributes (``env_identifiers``, ``file_set_refs``) as a
  view for tolerant getters.
* Underlying generated schema classes are imported lazily where needed
  (kept minimal to avoid touching schema packages not required by tests).
* BASE getters return neutral values (``None`` / empty lists) when a
  handle is invalid instead of raising.
* EXTENDED mutators raise :class:`TgiError` with
  ``TgiFaultCode.INVALID_ID`` (unknown handle) or
  ``TgiFaultCode.INVALID_ARGUMENT`` (semantic issues).
"""
import re
from types import SimpleNamespace
from typing import Any

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    register_parent,
    resolve_handle,
)

__all__: list[str] = [
    # BASE (F.7.87)
    "getViewBusInterfaceRefIDs",
    "getViewComponentInstantiationRefByID",
    "getViewComponentInstantiationRefByName",
    "getViewEnvIdentifierIDs",
    "getViewEnvIdentifiers",
    "getViewFileSetRefIDs",
    "getViewModelName",
    "getViewModelParametersID",
    "getViewName",
    "getViewOtherClockDriverRefIDs",
    "getViewParametersID",
    "getViewPortWireRefIDs",
    "getViewVendorExtensionsID",
    # EXTENDED (F.7.88)
    "addViewEnvIdentifier",
    "removeViewBusInterfaceRef",
    "removeViewComponentInstantiationRef",
    "removeViewEnvIdentifier",
    "removeViewFileSetRef",
    "removeViewOtherClockDriverRef",
    "removeViewPortWireRef",
    "setViewComponentInstantiationRef",
    "setViewModelName",
    "setViewName",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve(viewID: str) -> Any | None:
    obj = resolve_handle(viewID)
    from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    if isinstance(obj, (ModelType.Views.View, AbstractorModelType.Views.View)):
        return obj
    # Accept any object that has typical view markers.
    if obj is None:
        return None
    if hasattr(obj, "bus_interface_refs") or hasattr(obj, "file_set_refs") or hasattr(obj, "env_identifiers"):
        return obj
    # Fallback: name attribute plus model_name heuristic
    if hasattr(obj, "model_name") and hasattr(obj, "name"):
        return obj
    return None


def _ensure(viewID: str):
    v = _resolve(viewID)
    if v is None:
        raise TgiError("Invalid ID", TgiFaultCode.INVALID_ID)
    return v


def _ensure_list(parent: Any, attr: str) -> list[Any]:
    lst = getattr(parent, attr, None)
    if lst is None:
        lst = []
        setattr(parent, attr, lst)
    return lst


# ---------------------------------------------------------------------------
# BASE (F.7.87) – tolerant getters
# ---------------------------------------------------------------------------

def getViewBusInterfaceRefIDs(viewID: str) -> list[str]:  # F.7.87.1
    v = _resolve(viewID)
    if v is None:
        return []
    refs = getattr(getattr(v, "bus_interface_refs", None), "bus_interface_ref", [])
    return [get_handle(r) for r in refs]


def getViewComponentInstantiationRefByID(viewID: str) -> str | None:  # F.7.87.2
    v = _resolve(viewID)
    if v is None:
        return None
    ci_ref = getattr(v, "component_instantiation_ref", None)
    return get_handle(ci_ref) if ci_ref is not None else None


def getViewComponentInstantiationRefByName(viewID: str) -> str | None:  # F.7.87.3
    v = _resolve(viewID)
    if v is None:
        return None
    ci_ref = getattr(v, "component_instantiation_ref", None)
    return getattr(ci_ref, "name", None)


def getViewEnvIdentifierIDs(viewID: str) -> list[str]:
    """Return ordered environment identifiers with ownership (F.7.87.9)."""
    view = _ensure(viewID)
    items = getattr(view, "env_identifier", None)
    if items is None:
        items = getattr(getattr(view, "env_identifiers", None), "env_identifier", [])
        path = ("env_identifiers", "env_identifier")
    else:
        path = ("env_identifier",)
    for item in items:
        register_parent(item, view, path, "list")
    return [get_handle(item) for item in items]


def getViewEnvIdentifiers(viewID: str) -> list[str]:
    """Return source environment identifier values in order (F.7.87.10)."""
    return [resolve_handle(handle).value for handle in getViewEnvIdentifierIDs(viewID)]


def getViewFileSetRefIDs(viewID: str) -> list[str]:  # F.7.87.6
    v = _resolve(viewID)
    if v is None:
        return []
    fs_refs = getattr(getattr(v, "file_set_refs", None), "file_set_ref", [])
    return [get_handle(r) for r in fs_refs]


def getViewModelName(viewID: str) -> str | None:  # F.7.87.7
    v = _resolve(viewID)
    if v is None:
        return None
    return getattr(v, "model_name", None)


def getViewModelParametersID(viewID: str) -> str | None:  # F.7.87.8
    v = _resolve(viewID)
    if v is None:
        return None
    mp = getattr(v, "model_parameters", None)
    return get_handle(mp) if mp is not None else None


def getViewName(viewID: str) -> str:
    """Return a generated component or abstractor view name (legacy helper)."""
    return _ensure(viewID).name


def getViewOtherClockDriverRefIDs(viewID: str) -> list[str]:  # F.7.87.10
    v = _resolve(viewID)
    if v is None:
        return []
    ocs = getattr(getattr(v, "other_clock_driver_refs", None), "other_clock_driver_ref", [])
    return [get_handle(o) for o in ocs]


def getViewParametersID(viewID: str) -> str | None:  # F.7.87.11
    v = _resolve(viewID)
    if v is None:
        return None
    params = getattr(v, "parameters", None)
    return get_handle(params) if params is not None else None


def getViewPortWireRefIDs(viewID: str) -> list[str]:  # F.7.87.12
    v = _resolve(viewID)
    if v is None:
        return []
    pw_refs = getattr(getattr(v, "port_wire_refs", None), "port_wire_ref", [])
    return [get_handle(r) for r in pw_refs]


def getViewVendorExtensionsID(viewID: str) -> str | None:  # F.7.87.13
    v = _resolve(viewID)
    if v is None:
        return None
    ve = getattr(v, "vendor_extensions", None)
    return get_handle(ve) if ve is not None else None


# ---------------------------------------------------------------------------
# EXTENDED (F.7.88)
# ---------------------------------------------------------------------------

def addViewEnvIdentifier(viewID: str, value: str) -> str:
    """Add a generated environment identifier, validating lexical syntax (F.7.88.1)."""
    view = _ensure(viewID)
    if not isinstance(value, str) or re.fullmatch(r"[a-zA-Z0-9_+*.]*:[a-zA-Z0-9_+*.]*:[a-zA-Z0-9_+*.]*", value) is None:
        raise TgiError("Environment identifier must have language:tool:extension syntax", TgiFaultCode.INVALID_ARGUMENT)
    from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    if isinstance(view, ModelType.Views.View):
        child = ModelType.Views.View.EnvIdentifier(value=value)
    elif isinstance(view, AbstractorModelType.Views.View):
        child = AbstractorModelType.Views.View.EnvIdentifier(value=value)
    else:
        raise TgiError("Expected a generated view", TgiFaultCode.INVALID_ID)
    view.env_identifier.append(child)
    register_parent(child, view, ("env_identifier",), "list")
    return get_handle(child)


def removeViewBusInterfaceRef(refID: str) -> bool:  # F.7.88.2
    return detach_child_by_handle(refID)


def removeViewComponentInstantiationRef(refID: str) -> bool:  # F.7.88.3
    return detach_child_by_handle(refID)


def removeViewEnvIdentifier(envIdentifierID: str) -> bool:
    """Remove an owned generated environment identifier (F.7.88.5)."""
    from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    from .core import get_parent_info

    child = resolve_handle(envIdentifierID)
    if child is None:
        return False
    if not isinstance(child, (ModelType.Views.View.EnvIdentifier, AbstractorModelType.Views.View.EnvIdentifier)):
        raise TgiError("Expected an environment identifier handle", TgiFaultCode.INVALID_ID)
    info = get_parent_info(envIdentifierID)
    if info is None or info.path != ("env_identifier",) or info.container != "list":
        raise TgiError("Environment identifier has no view ownership", TgiFaultCode.INVALID_ID)
    _ensure(info.parent_handle)
    return detach_child_by_handle(envIdentifierID)


def removeViewFileSetRef(refID: str) -> bool:  # F.7.88.5
    return detach_child_by_handle(refID)


def removeViewOtherClockDriverRef(refID: str) -> bool:  # F.7.88.6
    return detach_child_by_handle(refID)


def removeViewPortWireRef(refID: str) -> bool:  # F.7.88.7
    return detach_child_by_handle(refID)


def setViewComponentInstantiationRef(viewID: str, name: str) -> bool:  # F.7.88.8
    v = _ensure(viewID)
    ref = getattr(v, "component_instantiation_ref", None)
    if ref is None:
        ref = SimpleNamespace(name=name)
        v.component_instantiation_ref = ref  # type: ignore[attr-defined]
        register_parent(ref, v, ("component_instantiation_ref",), "single")
    else:
        ref.name = name  # type: ignore[attr-defined]
    return True


def setViewModelName(viewID: str, modelName: str) -> bool:  # F.7.88.9
    v = _ensure(viewID)
    v.model_name = modelName  # type: ignore[attr-defined]
    return True


def setViewName(viewID: str, name: str) -> bool:  # F.7.88.10
    v = _ensure(viewID)
    v.name = name  # type: ignore[attr-defined]
    return True
