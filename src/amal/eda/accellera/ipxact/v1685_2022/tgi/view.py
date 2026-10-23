"""View category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.87) and EXTENDED (F.7.88) API for *view* elements.
A ``view`` in IP-XACT names a particular representation of a component
and references component instantiations, bus interfaces, filesets, env
identifiers, etc. This module exposes only the standard public TGI
functions - no more, no less - following the tolerant BASE / strict
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
    "getAbstractorInstanceViewNameRefByID",
    "getViewBusInterfaceRefIDs",
    "getViewComponentInstantiationRefByID",
    "getViewComponentInstantiationRefByName",
    "getViewEnvIdentifierIDs",
    "getViewEnvIdentifiers",
    "getViewRefByName",
    "getViewFileSetRefIDs",
    "getViewModelName",
    "getViewModelParametersID",
    "getViewName",
    "getViewOtherClockDriverRefIDs",
    "getViewParametersID",
    "getViewPortWireRefIDs",
    "getViewVendorExtensionsID",
    "getViewDesignConfigurationInstantiationRefByName",
    "getViewDesignInstantiationRefByName",
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
    "setViewRefValue",
    "setViewDesignConfigurationInstantiationRef",
    "removeViewDesignConfigurationInstantiationRef",
    "setViewDesignInstantiationRef",
    "removeViewDesignInstantiationRef",
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


def _ensure(viewID: str) -> Any:
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


def _reference_view(viewID: str) -> Any:
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    view = resolve_handle(viewID)
    if not isinstance(view, ModelType.Views.View):
        raise TgiError("Expected a component view handle", TgiFaultCode.INVALID_ID)
    from org.accellera.ipxact.v1685_2022 import ComponentType

    from .core import get_parent_info, registry

    if get_parent_info(viewID) is None:
        for root_id in registry.iter_by_predicate(lambda root: isinstance(root, ComponentType)):
            root = resolve_handle(root_id)
            if (root.model is not None and root.model.views is not None
                    and any(candidate is view for candidate in root.model.views.view)):
                register_parent(view, root, ("model", "views", "view"), "list")
                break
    return view


def _set_reference(viewID: str, value: str, attr: str) -> bool:
    view = _reference_view(viewID)
    if not isinstance(value, str) or not value.strip():
        raise TgiError("Expected a nonempty instantiation name", TgiFaultCode.INVALID_ARGUMENT)
    setattr(view, attr, value)
    return True


def _remove_reference(viewID: str, attr: str) -> bool:
    view = _reference_view(viewID)
    if getattr(view, attr) is None:
        return False
    setattr(view, attr, None)
    return True


def _view_ref(viewRefID: str) -> Any:
    from org.accellera.ipxact.v1685_2022.domain_type_def import DomainTypeDef
    from org.accellera.ipxact.v1685_2022.driver_type import DriverType
    from org.accellera.ipxact.v1685_2022.signal_type_def import SignalTypeDef
    from org.accellera.ipxact.v1685_2022.struct_port_type_defs import StructPortTypeDefs
    from org.accellera.ipxact.v1685_2022.trans_type_def import TransTypeDef
    from org.accellera.ipxact.v1685_2022.wire_type_def import WireTypeDef

    child = resolve_handle(viewRefID)
    if not isinstance(child, (DomainTypeDef.ViewRef, DriverType.ViewRef, SignalTypeDef.ViewRef,
                              StructPortTypeDefs.StructPortTypeDef.ViewRef, TransTypeDef.ViewRef, WireTypeDef.ViewRef)):
        raise TgiError("Expected a generated viewRef handle", TgiFaultCode.INVALID_ID)
    return child


def _reference_target(viewID: str, attr: str, target_type: type) -> str | None:
    """Resolve within the owning component only; never return a string-value handle."""
    from org.accellera.ipxact.v1685_2022 import ComponentType

    from .core import get_parent_info

    view = _reference_view(viewID)
    name = getattr(view, attr)
    if name is None:
        return None
    info = get_parent_info(viewID)
    root = resolve_handle(info.parent_handle) if info is not None else None
    if not isinstance(root, ComponentType) or info.path != ("model", "views", "view"):
        raise TgiError("View has no component ownership", TgiFaultCode.INVALID_ID)
    instantiations = root.model.instantiations
    items = (instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation
             if instantiations is not None else [])
    matches = [item for item in items if isinstance(item, target_type) and item.name == name]
    if len(matches) != 1:
        raise TgiError("Reference target is missing or ambiguous", TgiFaultCode.NOT_FOUND)
    register_parent(matches[0], root,
                    ("model", "instantiations",
                     "component_instantiation_or_design_instantiation_or_design_configuration_instantiation"), "list")
    return get_handle(matches[0])



# ---------------------------------------------------------------------------
# BASE (F.7.87) – tolerant getters
# ---------------------------------------------------------------------------

def getAbstractorInstanceViewNameRefByID(abstractorInstanceID: str) -> str:
    """Resolve an abstractor instance's selected view by its abstractor VLNV.

    Section: F.7.87.1.

    The view name is resolved within the abstractor identified by this
    instance's ``abstractorRef``. A same-named view in another abstractor is
    never considered.

    Args:
        abstractorInstanceID: Handle to an abstractorInstance element.

    Returns:
        Handle to the referenced view element.
    """
    from org.accellera.ipxact.v1685_2022.abstractor import Abstractor
    from org.accellera.ipxact.v1685_2022.design_configuration import DesignConfiguration

    from .core import registry

    instance = resolve_handle(abstractorInstanceID)
    instance_type = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance
    if not isinstance(instance, instance_type):
        raise TgiError("Invalid abstractorInstance handle", TgiFaultCode.INVALID_ID)

    ref = instance.abstractor_ref
    abstractor_id = registry.get_id((ref.vendor, ref.library, ref.name, ref.version))
    abstractor = resolve_handle(abstractor_id) if abstractor_id is not None else None
    if not isinstance(abstractor, Abstractor):
        raise TgiError("Referenced abstractor is missing", TgiFaultCode.NOT_FOUND)

    model = abstractor.model
    views = model.views.view if model is not None and model.views is not None else []
    matches = [candidate for candidate in views if candidate.name == instance.view_name]
    if len(matches) != 1:
        raise TgiError("Referenced abstractor view is missing or ambiguous", TgiFaultCode.NOT_FOUND)
    target = matches[0]
    register_parent(target, abstractor, ("model", "views", "view"), "list")
    return get_handle(target)


def getViewComponentInstantiationRefByID(viewID: str) -> str | None:
    """Resolve the local component instantiation (F.7.87.2).

    Return None for an absent reference; raise NOT_FOUND for missing/ambiguous
    targets and INVALID_ID for a view without component ownership.
    """
    from org.accellera.ipxact.v1685_2022.component_instantiation_type import ComponentInstantiationType
    return _reference_target(viewID, "component_instantiation_ref", ComponentInstantiationType)



def getViewComponentInstantiationRefByName(viewID: str) -> str | None:
    """Return the optional source instantiation name from a component view.

    Section: F.7.87.3.

    The result is the stored string, or None when absent. This does not
    resolve the target. Invalid or non-component view handles raise INVALID_ID.
    """
    return _reference_view(viewID).component_instantiation_ref



def getViewDesignConfigurationInstantiationID(viewID: str) -> str | None:
    """Return the design configuration instantiation referenced by this view (F.7.87.4)."""
    return getViewDesignConfigurationInstantiationRefByID(viewID)



def getViewDesignConfigurationInstantiationRefByID(viewID: str) -> str | None:
    """Resolve the local design configuration instantiation (F.7.87.5)."""
    from org.accellera.ipxact.v1685_2022.design_configuration_instantiation_type import (
        DesignConfigurationInstantiationType,
    )
    return _reference_target(viewID, "design_configuration_instantiation_ref", DesignConfigurationInstantiationType)



def getViewDesignConfigurationInstantiationRefByName(viewID: str) -> str | None:
    """Return the optional source instantiation name from a component view.

    Section: F.7.87.6.

    The result is the stored string, or None when absent. This does not
    resolve the target. Invalid or non-component view handles raise INVALID_ID.
    """
    return _reference_view(viewID).design_configuration_instantiation_ref



def getViewDesignInstantiationRefByID(viewID: str) -> str | None:
    """Resolve the local design instantiation with the same fault contract (F.7.87.7)."""
    from org.accellera.ipxact.v1685_2022.design_instantiation_type import DesignInstantiationType
    return _reference_target(viewID, "design_instantiation_ref", DesignInstantiationType)



def getViewDesignInstantiationRefByName(viewID: str) -> str | None:
    """Return the optional source instantiation name from a component view.

    Section: F.7.87.8.

    The result is the stored string, or None when absent. This does not
    resolve the target. Invalid or non-component view handles raise INVALID_ID.
    """
    return _reference_view(viewID).design_instantiation_ref



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



def getViewRefByName(viewRefID: str) -> str:
    """Return the source name from a generated viewRef (F.7.87.11).

    Invalid or unrelated handles raise INVALID_ID. Target resolution is separate.
    """
    return _view_ref(viewRefID).value


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



def removeViewComponentInstantiationRef(viewID: str) -> bool:
    """Remove the optional source reference from the supplied component view.

    Section: F.7.88.2.

    Return True when removed, False when absent. Preserve other view fields
    and referenced instantiation objects. Invalid handles raise INVALID_ID.
    """
    return _remove_reference(viewID, "component_instantiation_ref")



def removeViewDesignConfigurationInstantiationRef(viewID: str) -> bool:
    """Remove the optional source reference from the supplied component view.

    Section: F.7.88.3.

    Return True when removed, False when absent. Preserve other view fields
    and referenced instantiation objects. Invalid handles raise INVALID_ID.
    """
    return _remove_reference(viewID, "design_configuration_instantiation_ref")



def removeViewDesignInstantiationRef(viewID: str) -> bool:
    """Remove the optional source reference from the supplied component view.

    Section: F.7.88.4.

    Return True when removed, False when absent. Preserve other view fields
    and referenced instantiation objects. Invalid handles raise INVALID_ID.
    """
    return _remove_reference(viewID, "design_instantiation_ref")



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



def setViewComponentInstantiationRef(viewID: str, componentInstantiationRef: str) -> bool:
    """Set a component view's source reference to the supplied instantiation name.

    Section: F.7.88.6.

    Accept a nonempty string and preserve other view fields. Invalid handles
    raise INVALID_ID; invalid names raise INVALID_ARGUMENT before mutation.
    Target existence and configuration semantics are checked separately.
    """
    return _set_reference(viewID, componentInstantiationRef, "component_instantiation_ref")



def setViewDesignConfigurationInstantiationRef(viewID: str, designInstantiationRef: str) -> bool:
    """Set a component view's source reference to the supplied instantiation name.

    Section: F.7.88.7.

    Accept a nonempty string and preserve other view fields. Invalid handles
    raise INVALID_ID; invalid names raise INVALID_ARGUMENT before mutation.
    Target existence and configuration semantics are checked separately.
    """
    return _set_reference(viewID, designInstantiationRef, "design_configuration_instantiation_ref")



def setViewDesignInstantiationRef(viewID: str, designInstantiationRef: str) -> bool:
    """Set a component view's source reference to the supplied instantiation name.

    Section: F.7.88.8.

    Accept a nonempty string and preserve other view fields. Invalid handles
    raise INVALID_ID; invalid names raise INVALID_ARGUMENT before mutation.
    Target existence and configuration semantics are checked separately.
    """
    return _set_reference(viewID, designInstantiationRef, "design_instantiation_ref")



def setViewRefValue(viewRefID: str, value: str) -> bool:
    """Update a generated viewRef source name in place (F.7.88.9).

    Preserve identity and XML metadata. Invalid handles raise INVALID_ID;
    empty/nonstring names raise INVALID_ARGUMENT before mutation.
    """
    child = _view_ref(viewRefID)
    if not isinstance(value, str) or not value.strip():
        raise TgiError("Expected a nonempty view name", TgiFaultCode.INVALID_ARGUMENT)
    child.value = value
    return True


# Legacy compatibility helpers.

def getViewBusInterfaceRefIDs(viewID: str) -> list[str]:  # F.7.87.1
    v = _resolve(viewID)
    if v is None:
        return []
    refs = getattr(getattr(v, "bus_interface_refs", None), "bus_interface_ref", [])
    return [get_handle(r) for r in refs]



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



def removeViewBusInterfaceRef(refID: str) -> bool:  # F.7.88.2
    return detach_child_by_handle(refID)



def removeViewFileSetRef(refID: str) -> bool:  # F.7.88.5
    return detach_child_by_handle(refID)



def removeViewOtherClockDriverRef(refID: str) -> bool:  # F.7.88.6
    return detach_child_by_handle(refID)



def removeViewPortWireRef(refID: str) -> bool:  # F.7.88.7
    return detach_child_by_handle(refID)



def setViewModelName(viewID: str, modelName: str) -> bool:  # F.7.88.9
    v = _ensure(viewID)
    v.model_name = modelName  # type: ignore[attr-defined]
    return True



def setViewName(viewID: str, name: str) -> bool:  # F.7.88.10
    v = _ensure(viewID)
    v.name = name  # type: ignore[attr-defined]
    return True


__all__ += [
    "getViewDesignConfigurationInstantiationID",
    "getViewDesignConfigurationInstantiationRefByID",
    "getViewDesignInstantiationRefByID",
]
