"""Generator category TGI functions (IEEE 1685-2022).

Annex F.7.49 BASE and F.7.50 EXTENDED cover GeneratorType objects and
AbstractorGenerator/ComponentGenerator instance generators. The generated
schema distinguishes API type nodes, API service enums, executable URIs,
phase expressions, transport-method containers and instance-generator groups.

Numeric phase access evaluates self-contained SystemVerilog expressions with
slang; source-expression access preserves the XML text. Full Annex E parameter
and scope resolution remains separate work. Transport methods use the schema's
required transportMethod child, and the standard setter returns Boolean.

Editing validates inputs before mutation, preserves existing child handles
when updating values, and invalidates detached subtrees during removal.
Group removers restrict ownership to the corresponding generator kind.
Invalid/wrong-kind handles raise INVALID_ID; invalid arguments raise
INVALID_ARGUMENT. Optional metadata getters preserve absent source values.
"""
# ruff: noqa: I001
from org.accellera.ipxact.v1685_2022 import (
    AbstractorGenerator,
    ComponentGenerator,
)
from org.accellera.ipxact.v1685_2022.instance_generator_type import InstanceGeneratorType
from org.accellera.ipxact.v1685_2022.instance_generator_type_scope import InstanceGeneratorTypeScope
from org.accellera.ipxact.v1685_2022.generator_type import GeneratorType

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.49)
    "getAbstractorGeneratorGroup",
    "getAbstractorGeneratorGroupIDs",
    "getComponentGeneratorGroupIDs",
    "getGeneratorApiService",
    "getGeneratorApiTypeID",
    "getGeneratorExecutable",
    "getGeneratorGeneratorExe",
    "getGeneratorGroups",
    "getGeneratorPhase",
    "getGeneratorPhaseExpression",
    "getGeneratorPhaseID",
    "getGeneratorScope",
    "getGeneratorTransportMethodsID",
    "getTransportMethodsTransportMethodID",
    # EXTENDED (F.7.50)
    "addAbstractorGeneratorGroup",
    "addComponentGeneratorGroup",
    "removeAbstractorGeneratorGroup",
    "removeComponentGeneratorGroup",
    "removeGeneratorApiService",
    "removeGeneratorApiType",
    "removeGeneratorPhase",
    "removeGeneratorTransportMethods",
    "removeTransportMethodsTransportMethod",
    "setGeneratorApiService",
    "setGeneratorApiType",
    "setGeneratorGeneratorExe",
    "setGeneratorPhase",
    "setGeneratorScope",
    "setGeneratorTransportMethods",
    "setTransportMethodsTransportMethod",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------

def _resolve_generator(handle: str) -> GeneratorType | None:
    obj = resolve_handle(handle)
    return obj if isinstance(obj, GeneratorType) else None


def _resolve_instance_generator(handle: str) -> InstanceGeneratorType | None:
    obj = resolve_handle(handle)
    return obj if isinstance(obj, AbstractorGenerator | ComponentGenerator) else None


def _resolve_transport_methods(handle: str) -> GeneratorType.TransportMethods | None:
    obj = resolve_handle(handle)
    return obj if isinstance(obj, GeneratorType.TransportMethods) else None


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise TgiError(f"{label} requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _remove_child(parent, name):
    child = getattr(parent, name)
    if child is None:
        return True
    register_parent(child, parent, (name,), "single")
    return detach_child_by_handle(get_handle(child))


def _remove_group(groupID, parent_type):
    from .core import get_parent_info, registry
    group = resolve_handle(groupID)
    if not isinstance(group, InstanceGeneratorType.Group):
        return False
    info = get_parent_info(groupID)
    if info is None:
        from dataclasses import fields, is_dataclass
        pending = [resolve_handle(handle) for handle in registry.iter_by_predicate(lambda root: True)]
        seen = set()
        while pending:
            obj = pending.pop()
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            if isinstance(obj, parent_type) and any(item is group for item in obj.group):
                register_parent(group, obj, ("group",), "list")
                break
            if is_dataclass(obj) and not isinstance(obj, type):
                pending.extend(getattr(obj, field.name) for field in fields(obj))
            elif isinstance(obj, (list, tuple)):
                pending.extend(obj)
        info = get_parent_info(groupID)
    if info is None or not isinstance(resolve_handle(info.parent_handle), parent_type) or info.path != ("group",):
        return False
    return detach_child_by_handle(groupID)


# ---------------------------------------------------------------------------
# BASE (F.7.49)
# ---------------------------------------------------------------------------

def getAbstractorGeneratorGroup(abstractorGeneratorID: str) -> str | None:
    """Return the first group value of an ``AbstractorGenerator``.

    Section: F.7.49.1. If no group elements exist, returns None.

    Args:
        abstractorGeneratorID: Handle to an abstractorGenerator element.

    Returns:
        The group names.
    """
    ig = _resolve_instance_generator(abstractorGeneratorID)
    if ig is None or not isinstance(resolve_handle(abstractorGeneratorID), AbstractorGenerator):
        raise TgiError("Invalid abstractorGenerator handle", TgiFaultCode.INVALID_ID)
    groups = getattr(ig, "group", [])
    for g in groups:
        return getattr(g, "value", None)
    return None


def getAbstractorGeneratorGroupIDs(abstractorGeneratorID: str) -> list[str]:
    """Return handles of all group elements of an ``AbstractorGenerator``.

    Section: F.7.49.2.

    Args:
        abstractorGeneratorID: Handle to an abstractorGenerator element.

    Returns:
        List of handles to the group elements.
    """
    ig = _resolve_instance_generator(abstractorGeneratorID)
    if ig is None or not isinstance(resolve_handle(abstractorGeneratorID), AbstractorGenerator):
        raise TgiError("Invalid abstractorGenerator handle", TgiFaultCode.INVALID_ID)
    for group in ig.group:
        register_parent(group, ig, ("group",), "list")
    return [get_handle(group) for group in ig.group]


def getComponentGeneratorGroupIDs(componentGeneratorID: str) -> list[str]:
    """Return handles of group elements of a ``ComponentGenerator``.

    Section: F.7.49.3.

    Args:
        componentGeneratorID: Handle to a componentGenerator element.

    Returns:
        List of handles to the group elements.
    """
    ig = _resolve_instance_generator(componentGeneratorID)
    if ig is None or not isinstance(resolve_handle(componentGeneratorID), ComponentGenerator):
        raise TgiError("Invalid componentGenerator handle", TgiFaultCode.INVALID_ID)
    for group in ig.group:
        register_parent(group, ig, ("group",), "list")
    return [get_handle(group) for group in ig.group]


def getGeneratorApiService(generatorID: str) -> str | None:
    """Return API service (SOAP/REST).

    Section: F.7.49.4.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        The apiService value.
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    svc = g.api_service
    return None if svc is None else getattr(svc, "value", None)


def getGeneratorApiTypeID(generatorID: str) -> str | None:
    """Return handle of the ``apiType`` element (not its value).

    Section: F.7.49.5.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        Handle to the apiType element.
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    api = g.api_type
    if api is None:
        return None
    register_parent(api, g, ("api_type",), "single")
    return get_handle(api)


def getGeneratorExecutable(generatorID: str) -> str | None:
    """Return the path string of ``generatorExe``.

    Section: F.7.49.6.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        The generator executable file.
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    exe = g.generator_exe
    return None if exe is None else getattr(exe, "value", None)


def getGeneratorGeneratorExe(generatorID: str) -> str | None:
    """Return the ID (handle) of the ``generatorExe`` element.

    Section: F.7.49.7. Returns None if absent.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        The generatorExe value.
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    exe = g.generator_exe
    if exe is None:
        return None
    register_parent(exe, g, ("generator_exe",), "single")
    return get_handle(exe)


def getGeneratorGroups(generatorID: str) -> list[str]:
    """Return list of group values (works for instance generators only).

    Section: F.7.49.8. Non-instance generators return empty list.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        List of generator groups.
    """
    ig = _resolve_instance_generator(generatorID)
    if ig is None:
        if _resolve_generator(generatorID) is None:
            raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
        return []
    return [str(getattr(g, "value", "")) for g in getattr(ig, "group", []) if getattr(g, "value", None) is not None]


def getGeneratorPhase(generatorID: str) -> float | None:
    """Return the resolved generator phase number, or None when unresolved.

    Section: F.7.49.9.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        The phase number. Unresolved expressions or absent phase return None.
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    if g.phase is None:
        return None
    from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser
    try:
        return float(SvExpressionParser().evaluate(g.phase.value))
    except SvExpressionError:
        return None


def getGeneratorPhaseExpression(generatorID: str) -> str | None:
    """Return expression string of phase (same as value for this schema).

    Section: F.7.49.10.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        The generator phase.
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    return g.phase.value if g.phase is not None else None


def getGeneratorPhaseID(generatorID: str) -> str | None:
    """Return handle of ``phase`` element.

    Section: F.7.49.11.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        Handle to the phase element.
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    ph = g.phase
    if ph is None:
        return None
    register_parent(ph, g, ("phase",), "single")
    return get_handle(ph)


def getGeneratorScope(generatorID: str) -> str | None:
    """Return scope attribute (INSTANCE or DESIGN) for instance generators.

    Section: F.7.49.12. Returns None for plain Generator objects.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        The generator scope.
    """
    ig = _resolve_instance_generator(generatorID)
    if ig is None:
        if _resolve_generator(generatorID) is None:
            raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
        return None
    scope = getattr(ig, "scope", None)
    if scope is None:
        return None
    # InstanceGeneratorTypeScope is an Enum
    try:
        return scope.value  # type: ignore[return-value]
    except AttributeError:  # pragma: no cover - defensive
        return str(scope)


def getGeneratorTransportMethodsID(generatorID: str) -> str | None:
    """Return handle of ``transportMethods`` element.

    Section: F.7.49.13.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        Handle to the transportMethods element.
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    tm = g.transport_methods
    if tm is None:
        return None
    register_parent(tm, g, ("transport_methods",), "single")
    return get_handle(tm)


def getTransportMethodsTransportMethodID(transportMethodsID: str) -> str | None:
    """Return handle of the ``transportMethod`` child.

    Section: F.7.49.14.

    Args:
        transportMethodsID: Handle to a transportMethods element.

    Returns:
        Handle to the transportMethod element.
    """
    tm = _resolve_transport_methods(transportMethodsID)
    if tm is None:
        raise TgiError("Invalid transportMethods handle", TgiFaultCode.INVALID_ID)
    method = tm.transport_method
    if method is None:
        return None
    register_parent(method, tm, ("transport_method",), "single")
    return get_handle(method)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.50)
# ---------------------------------------------------------------------------

def addAbstractorGeneratorGroup(abstractorGeneratorID: str, groupName: str) -> str:
    """Append a group element to an ``AbstractorGenerator``.

    Section: F.7.50.1.

    Args:
        abstractorGeneratorID: Handle to an abstractorGenerator element.
        groupName: the value of the added group.

    Returns:
        the group identifier.
    """
    ig = _resolve_instance_generator(abstractorGeneratorID)
    if ig is None or not isinstance(resolve_handle(abstractorGeneratorID), AbstractorGenerator):
        raise TgiError("Invalid abstractorGenerator handle", TgiFaultCode.INVALID_ID)
    grp = InstanceGeneratorType.Group(value=_text(groupName, "Group name"))
    ig.group.append(grp)  # type: ignore[attr-defined]
    register_parent(grp, ig, ("group",), "list")
    return get_handle(grp)


def addComponentGeneratorGroup(componentGeneratorID: str, groupName: str) -> str:
    """Append a group element to a ``ComponentGenerator``.

    Section: F.7.50.2.

    Args:
        componentGeneratorID: Handle to a componentGenerator element.
        groupName: value to set on the group.

    Returns:
        the group identifier.
    """
    ig = _resolve_instance_generator(componentGeneratorID)
    if ig is None or not isinstance(resolve_handle(componentGeneratorID), ComponentGenerator):
        raise TgiError("Invalid componentGenerator handle", TgiFaultCode.INVALID_ID)
    grp = InstanceGeneratorType.Group(value=_text(groupName, "Group name"))
    ig.group.append(grp)  # type: ignore[attr-defined]
    register_parent(grp, ig, ("group",), "list")
    return get_handle(grp)


def removeAbstractorGeneratorGroup(groupID: str) -> bool:
    """Remove a group element from an ``AbstractorGenerator``.

    Section: F.7.50.3.

    Args:
        groupID: Handle to a group element.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    return _remove_group(groupID, AbstractorGenerator)


def removeComponentGeneratorGroup(groupID: str) -> bool:
    """Remove a group element from a ``ComponentGenerator``.

    Section: F.7.50.4.

    Args:
        groupID: Handle to a group element.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    return _remove_group(groupID, ComponentGenerator)


def removeGeneratorApiService(generatorID: str) -> bool:
    """Remove the ``apiService`` element.

    Section: F.7.50.5.

    Args:
        generatorID: Handle to a generator.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    g.api_service = None  # type: ignore[assignment]
    return True


def removeGeneratorApiType(generatorID: str) -> bool:
    """Remove the ``apiType`` element.

    Section: F.7.50.6.

    Args:
        generatorID: Handle to a generator.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    return _remove_child(g, "api_type")


def removeGeneratorPhase(generatorID: str) -> bool:
    """Remove the ``phase`` element.

    Section: F.7.50.7.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    return _remove_child(g, "phase")


def removeGeneratorTransportMethods(generatorID: str) -> bool:
    """Remove the ``transportMethods`` container.

    Section: F.7.50.8.

    Args:
        generatorID: Handle to a generator.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    return _remove_child(g, "transport_methods")


def removeTransportMethodsTransportMethod(transportMethodsID: str) -> bool:
    """Remove the ``transportMethod`` child from a container.

    Section: F.7.50.9. Container itself remains.

    Args:
        transportMethodsID: Handle to a transportMethods element.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    tm = _resolve_transport_methods(transportMethodsID)
    if tm is None:
        raise TgiError("Invalid transportMethods handle", TgiFaultCode.INVALID_ID)
    return _remove_child(tm, "transport_method")


def setGeneratorApiService(generatorID: str, apiService: str | None) -> bool:
    """Set or clear the ``apiService`` element.

    Section: F.7.50.10.

    Args:
        generatorID: Handle to a generator element.
        apiService: Generator apiService.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    if apiService is None:
        g.api_service = None  # type: ignore[assignment]
        return True
    from org.accellera.ipxact.v1685_2022.generator_type_api_service import GeneratorTypeApiService
    try:
        enum_val = GeneratorTypeApiService(apiService)
    except (ValueError, TypeError) as exc:
        raise TgiError("Unknown apiService value", TgiFaultCode.INVALID_ARGUMENT) from exc
    g.api_service = enum_val  # type: ignore[assignment]
    return True


def setGeneratorApiType(generatorID: str, apiType: str | None) -> bool:
    """Set or clear the ``apiType`` element.

    Section: F.7.50.11.

    Args:
        generatorID: Handle to a generator | componentGenerator | abstractor-.
        apiType: Generator apiType.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    if apiType is None:
        return _remove_child(g, "api_type")
    from org.accellera.ipxact.v1685_2022.api_type import ApiType
    try:
        enum_val = ApiType(apiType)
    except (ValueError, TypeError) as exc:
        raise TgiError("Unknown apiType value", TgiFaultCode.INVALID_ARGUMENT) from exc
    if g.api_type is None:
        g.api_type = GeneratorType.ApiType(value=enum_val)
    else:
        g.api_type.value = enum_val
    register_parent(g.api_type, g, ("api_type",), "single")
    return True


def setGeneratorGeneratorExe(generatorID: str, path: str) -> bool:
    """Set the path of ``generatorExe`` (creates element if absent).

    Section: F.7.50.12.

    Args:
        generatorID: Handle to a generator element.
        path: the value of the generatorExe.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    from org.accellera.ipxact.v1685_2022.ipxact_uri import IpxactUri
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    path = _text(path, "Generator executable")
    if g.generator_exe is None:
        g.generator_exe = IpxactUri(value=path)  # type: ignore[arg-type]
    else:
        if hasattr(g.generator_exe, "value"):
            g.generator_exe.value = path  # type: ignore[attr-defined]
        else:  # pragma: no cover
            g.generator_exe = IpxactUri(value=path)  # type: ignore[arg-type]
    register_parent(g.generator_exe, g, ("generator_exe",), "single")
    return True


def setGeneratorPhase(generatorID: str, phaseValue: str) -> bool:
    """Set (or create) the ``phase`` element value.

    Section: F.7.50.13. The value is stored as the expression string.

    Args:
        generatorID: Handle to a generator element.
        phaseValue: Generator phase.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    from org.accellera.ipxact.v1685_2022.phase import Phase
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    phaseValue = _text(phaseValue, "Phase")
    if g.phase is None:
        g.phase = Phase(value=phaseValue)
    else:
        g.phase.value = phaseValue
    register_parent(g.phase, g, ("phase",), "single")
    return True


def setGeneratorScope(generatorID: str, scope: str) -> bool:
    """Set scope attribute of an instance generator (INSTANCE/DESIGN).

    Section: F.7.50.14.

    Args:
        generatorID: Handle to a generator element.
        scope: Generator scope.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    ig = _resolve_instance_generator(generatorID)
    if ig is None:
        raise TgiError("Handle is not an instance generator", TgiFaultCode.INVALID_ID)
    try:
        ig.scope = InstanceGeneratorTypeScope(scope)  # type: ignore[assignment]
    except (ValueError, TypeError) as exc:
        raise TgiError("Unknown scope value", TgiFaultCode.INVALID_ARGUMENT) from exc
    return True


def setGeneratorTransportMethods(generatorID: str, transportMethod: str) -> bool:
    """Set the generator transport method using its standard string value.

    Section: F.7.50.15.

    Args:
        generatorID: Handle to a generator.
        transportMethod: Transport method value (file).

    Returns:
        True on successful creation or update; invalid inputs do not mutate.
    """
    from org.accellera.ipxact.v1685_2022.transport_method_type import TransportMethodType
    g = _resolve_generator(generatorID)
    if g is None:
        raise TgiError("Invalid generator handle", TgiFaultCode.INVALID_ID)
    try:
        value = TransportMethodType(transportMethod)
    except (ValueError, TypeError) as exc:
        raise TgiError("Unknown transport method", TgiFaultCode.INVALID_ARGUMENT) from exc
    if g.transport_methods is None:
        g.transport_methods = GeneratorType.TransportMethods(
            transport_method=GeneratorType.TransportMethods.TransportMethod(value=value))
    else:
        setTransportMethodsTransportMethod(get_handle(g.transport_methods), transportMethod)
    register_parent(g.transport_methods, g, ("transport_methods",), "single")
    register_parent(g.transport_methods.transport_method, g.transport_methods, ("transport_method",), "single")
    return True


def setTransportMethodsTransportMethod(transportMethodsID: str, method: str | None) -> bool:
    """Set/clear the ``transportMethod`` child (currently only 'file').

    Section: F.7.50.16.

    Args:
        transportMethodsID: Handle to a transportMethods element.
        method: the transportMethod value.

    Returns:
        Indicates call is successful (true) or not (false).
    """
    tm = _resolve_transport_methods(transportMethodsID)
    if tm is None:
        raise TgiError("Invalid transportMethods handle", TgiFaultCode.INVALID_ID)
    if method is None:
        return _remove_child(tm, "transport_method")
    from org.accellera.ipxact.v1685_2022.transport_method_type import TransportMethodType
    try:
        enum_val = TransportMethodType(method)
    except (ValueError, TypeError) as exc:
        raise TgiError("Unknown transportMethod value", TgiFaultCode.INVALID_ARGUMENT) from exc
    if tm.transport_method is None:
        tm.transport_method = GeneratorType.TransportMethods.TransportMethod(value=enum_val)
    else:
        tm.transport_method.value = enum_val
    register_parent(tm.transport_method, tm, ("transport_method",), "single")
    return True
