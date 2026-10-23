"""Vector category TGI functions (IEEE 1685-2022).

Annex F.7.83 BASE exposes vectors, endpoint handles, resolved integer ranges
and source expressions. Annex F.7.84 EXTENDED adds and removes complete
vectors. Generated Vector, extended port vectors, module-parameter vectors
and constraint-set bit slices preserve their distinct schema endpoint types.

Self-contained SystemVerilog integer expressions are evaluated with slang;
parameter/scope resolution remains separate Annex E work. Ownership links
support parsed-document removal and invalidate detached endpoint handles.
The final vector removal also removes its empty optional vectors wrapper.

Historical endpoint setters/removers and vectorId editing remain compatibility
helpers; they are not operations in Annex F.7.84. BASE endpoint getters retain
neutral results for unknown handles. Creation rejects malformed ranges before
mutation and uses generated bindings rather than handwritten placeholder nodes.
"""
from collections.abc import Sequence
from dataclasses import fields, is_dataclass
from typing import cast, get_args, get_type_hints

from org.accellera.ipxact.v1685_2022 import (
    ConstraintSet,
    ExtendedVectorsType,
    Left,
    ModuleParameterType,
    Right,
    UnsignedIntExpression,
    Vector,
    Vectors,
)

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)

__all__ = [
    # BASE (F.7.83)
    "getVectorIDs",
    "getVectorIdAttribute",
    "getVectorLeftID",
    "getVectorRange",
    "getVectorRangeExpression",
    "getVectorRightID",
    # EXTENDED (F.7.84)
    "addVector",
    "removeVector",
    "removeVectorLeft",
    "removeVectorRight",
    "setVector",
    "setVectorIdAttribute",
    "setVectorLeft",
    "setVectorRight",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

type _VectorModel = Vector | ExtendedVectorsType.Vector | ModuleParameterType.Vectors.Vector | ConstraintSet.Vector
type _VectorContainerModel = Vectors | ExtendedVectorsType | ModuleParameterType.Vectors


def _resolve(objID: str) -> object | None:
    return resolve_handle(objID)


_VECTOR_TYPES = (Vector, ExtendedVectorsType.Vector, ModuleParameterType.Vectors.Vector, ConstraintSet.Vector)


def _resolve_vector(vectorID: str) -> _VectorModel | None:
    obj = _resolve(vectorID)
    return obj if isinstance(obj, _VECTOR_TYPES) else None


def _ensure_vector(vectorID: str) -> _VectorModel:
    vec = _resolve_vector(vectorID)
    if vec is None:
        raise TgiError("Invalid vector handle", TgiFaultCode.INVALID_ID)
    return vec


def _make_endpoint(value: str | int | None, expression: str | None = None) -> str:
    text = expression if expression is not None else value
    if isinstance(text, bool) or not isinstance(text, (str, int)) or not str(text).strip():
        raise TgiError("Endpoint requires a nonempty expression", TgiFaultCode.INVALID_ARGUMENT)
    return str(text)


def _get_endpoint_value(ep: UnsignedIntExpression | None) -> int | None:
    from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser
    if ep is None:
        return None
    try:
        value = SvExpressionParser().evaluate(ep.value)
    except SvExpressionError:
        return None
    return value if type(value) is int else None


def _get_endpoint_expr(ep: UnsignedIntExpression | None) -> str | None:
    return ep.value if ep is not None else None


def _endpoint_type(vec: _VectorModel, name: str) -> type[UnsignedIntExpression]:
    return cast(type[UnsignedIntExpression], get_type_hints(type(vec))[name])


def _set_endpoint(vec: _VectorModel, name: str, text: str) -> None:
    child = getattr(vec, name)
    if child is None:
        child = _endpoint_type(vec, name)(value=text)
        setattr(vec, name, child)
    else:
        child.value = text
    register_parent(child, vec, (name,), "single")


def _container_type(parent: object, attr: str) -> type[_VectorContainerModel] | None:
    annotation = get_type_hints(type(parent)).get(attr)
    candidates = get_args(annotation) or (annotation,)
    return cast(
        type[_VectorContainerModel] | None,
        next(
            (
                candidate
                for candidate in candidates
                if isinstance(candidate, type)
                and candidate in (Vectors, ExtendedVectorsType, ModuleParameterType.Vectors)
            ),
            None,
        ),
    )


# ---------------------------------------------------------------------------
# BASE (F.7.83)
# ---------------------------------------------------------------------------

def getVectorIDs(vectorContainerID: str) -> list[str]:  # F.7.83.1
    """Return the vectors defined on a generated containing element.

    Section: F.7.83.1.

    Args:
        vectorContainerID: Vector or containing element handle.

    Returns:
        Ordered handles to generated vectors; empty when the element has none.
    """
    container = _resolve(vectorContainerID)
    if container is None:
        raise TgiError("Invalid vector container handle", TgiFaultCode.INVALID_ID)
    if isinstance(container, (Vectors, ExtendedVectorsType, ModuleParameterType.Vectors)):
        owner, path, vectors = container, ("vector",), container.vector
    elif isinstance(getattr(container, "vectors", None), (Vectors, ExtendedVectorsType, ModuleParameterType.Vectors)):
        owner, path, vectors = container, ("vectors", "vector"), container.vectors.vector
    elif isinstance(getattr(container, "vector", None), _VECTOR_TYPES):
        owner, path, vectors = container, ("vector",), [container.vector]
    else:
        return []
    is_list = path == ("vectors", "vector") or isinstance(
        container, (Vectors, ExtendedVectorsType, ModuleParameterType.Vectors)
    )
    for vector in vectors:
        register_parent(vector, owner, path, "list" if is_list else "single")
    return [get_handle(vector) for vector in vectors]


# Shared attribute operation also appears in the Vector BASE category.
from .element_attribute import getVectorIdAttribute  # noqa: E402 (standard category order)


def _owned_endpoint(vec: _VectorModel, name: str) -> str | None:
    child = getattr(vec, name)
    if child is None:
        return None
    register_parent(child, vec, (name,), "single")
    return get_handle(child)


def getVectorLeftID(vectorID: str) -> str | None:  # F.7.83.2
    """Return the owned left endpoint handle.

    Section: F.7.83.2.

    Args:
        vectorID: Vector or containing element handle.

    Returns:
        Owned endpoint handle or None for an absent/invalid vector.
    """
    vec = _resolve_vector(vectorID)
    if vec is None:
        return None
    return _owned_endpoint(vec, "left")


def getVectorRange(vectorID: str) -> list[int | None] | None:  # F.7.83.3
    """Evaluate the left and right endpoint integer expressions.

    Section: F.7.83.3.

    Args:
        vectorID: Vector or containing element handle.

    Returns:
        Left/right integer values; unresolved expressions yield None.
    """
    vec = _resolve_vector(vectorID)
    if vec is None:
        return None
    left = getattr(vec, "left", None)
    right = getattr(vec, "right", None)
    return [_get_endpoint_value(left), _get_endpoint_value(right)]


def getVectorRangeExpression(vectorID: str) -> list[str | None] | None:  # F.7.83.4
    """Return the left and right XML source expressions.

    Section: F.7.83.4.

    Args:
        vectorID: Vector or containing element handle.

    Returns:
        Left/right XML source expressions, or None for an invalid handle.
    """
    vec = _resolve_vector(vectorID)
    if vec is None:
        return None
    left = getattr(vec, "left", None)
    right = getattr(vec, "right", None)
    return [_get_endpoint_expr(left), _get_endpoint_expr(right)]


def getVectorRightID(vectorID: str) -> str | None:  # F.7.83.5
    """Return the owned right endpoint handle.

    Section: F.7.83.5.

    Args:
        vectorID: Vector or containing element handle.

    Returns:
        Owned endpoint handle or None for an absent/invalid vector.
    """
    vec = _resolve_vector(vectorID)
    if vec is None:
        return None
    return _owned_endpoint(vec, "right")


# ---------------------------------------------------------------------------
# EXTENDED (F.7.84)
# ---------------------------------------------------------------------------

def addVector(vectorContainerElementID: str, range: Sequence[str]) -> str:
    """Add a generated vector with both endpoint expressions.

    Section: F.7.84.1.

    Args:
        vectorContainerElementID: Handle to a generated vector container or containing element.
        range: Two source expressions, left followed by right.

    Returns:
        Handle to the new vector. Invalid inputs raise INVALID_ARGUMENT.
    """
    parent = resolve_handle(vectorContainerElementID)
    if parent is None:
        raise TgiError("Invalid container handle", TgiFaultCode.INVALID_ID)
    if isinstance(range, str) or not isinstance(range, Sequence) or len(range) != 2:
        raise TgiError("Range requires two expressions", TgiFaultCode.INVALID_ARGUMENT)
    left, right = (_make_endpoint(value) for value in range)
    if isinstance(parent, ConstraintSet):
        if parent.vector is not None:
            raise TgiError("Vector already exists", TgiFaultCode.INVALID_ARGUMENT)
        from org.accellera.ipxact.v1685_2022 import UnsignedIntExpression
        vector = ConstraintSet.Vector(left=UnsignedIntExpression(value=left), right=UnsignedIntExpression(value=right))
        parent.vector = vector
        register_parent(vector, parent, ("vector",), "single")
    else:
        if isinstance(parent, (Vectors, ExtendedVectorsType, ModuleParameterType.Vectors)):
            wrapper, path = parent, ("vector",)
        else:
            cls = _container_type(parent, "vectors")
            if cls is None:
                raise TgiError("Element does not support vectors", TgiFaultCode.INVALID_ARGUMENT)
            wrapper = parent.vectors
            if wrapper is None:
                wrapper = cls()
                parent.vectors = wrapper
                register_parent(wrapper, parent, ("vectors",), "single")
            path = ("vectors", "vector")
        cls = {Vectors: Vector, ExtendedVectorsType: ExtendedVectorsType.Vector,
               ModuleParameterType.Vectors: ModuleParameterType.Vectors.Vector}[type(wrapper)]
        vector = cls(left=Left(value=left), right=Right(value=right))
        wrapper.vector.append(vector)
        register_parent(vector, parent, path, "list")
    _owned_endpoint(vector, "left")
    _owned_endpoint(vector, "right")
    return get_handle(vector)


def removeVector(vectorID: str) -> bool:
    """Remove a vector and invalidate its owned endpoint handles.

    Section: F.7.84.2.

    Args:
        vectorID: Handle to a vector element.

    Returns:
        True when detached; False for an unknown or unowned vector.
    """
    vector = _resolve_vector(vectorID)
    if vector is None:
        return False
    if get_parent_info(vectorID) is None:
        pending = [resolve_handle(handle) for handle in registry.iter_by_predicate(lambda root: True)]
        seen = set()
        while pending:
            obj = pending.pop()
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            if is_dataclass(obj) and not isinstance(obj, type):
                if get_parent_info(vectorID) is None:
                    getVectorIDs(get_handle(obj))
                pending.extend(getattr(obj, field.name) for field in fields(obj))
            elif isinstance(obj, (list, tuple)):
                pending.extend(obj)
    info = get_parent_info(vectorID)
    if info is None:
        return False
    parent = resolve_handle(info.parent_handle)
    wrapper = parent.vectors if info.path == ("vectors", "vector") else None
    result = detach_child_by_handle(vectorID)
    if result and wrapper is not None and not wrapper.vector:
        register_parent(wrapper, parent, ("vectors",), "single")
        detach_child_by_handle(get_handle(wrapper))
    return result


def removeVectorLeft(vectorID: str) -> bool:  # Compatibility helper
    """Remove the left endpoint through the historical compatibility API.

    Section: Nonstandard compatibility helper; no Annex F operation.

    Args:
        vectorID: Vector or containing element handle.

    Returns:
        True on successful mutation.
    """
    vec = _ensure_vector(vectorID)
    if getattr(vec, "left", None) is None:
        return True
    return detach_child_by_handle(_owned_endpoint(vec, "left"))


def removeVectorRight(vectorID: str) -> bool:  # Compatibility helper
    """Remove the right endpoint through the historical compatibility API.

    Section: Nonstandard compatibility helper; no Annex F operation.

    Args:
        vectorID: Vector or containing element handle.

    Returns:
        True on successful mutation.
    """
    vec = _ensure_vector(vectorID)
    if getattr(vec, "right", None) is None:
        return True
    return detach_child_by_handle(_owned_endpoint(vec, "right"))


def setVector(vectorID: str, left: str | int | None, right: str | int | None) -> bool:  # Compatibility helper
    """Set both endpoint expressions through the historical compatibility API.

    Section: Nonstandard compatibility helper; no Annex F operation.

    Args:
        vectorID: Vector or containing element handle.
        left: Endpoint expression or attribute value.
        right: Endpoint expression or attribute value.

    Returns:
        True on successful mutation.
    """
    vec = _ensure_vector(vectorID)
    left_text, right_text = _make_endpoint(left), _make_endpoint(right)
    _set_endpoint(vec, "left", left_text)
    _set_endpoint(vec, "right", right_text)
    return True


def setVectorIdAttribute(elementID: str, vectorId: str | None) -> bool:  # Compatibility helper
    """Set the optional vectorId attribute on an extended vector.

    Section: Nonstandard compatibility helper; no Annex F operation.

    Args:
        elementID: Vector or containing element handle.
        vectorId: Endpoint expression or attribute value.

    Returns:
        True on successful mutation.
    """
    obj = _ensure_vector(elementID)
    if obj is None:
        raise TgiError("Invalid ID", TgiFaultCode.INVALID_ID)
    if vectorId is None:
        if hasattr(obj, "vector_id"):
            obj.vector_id = None
    else:
        if not hasattr(obj, "vector_id"):
            raise TgiError("Vector has no vectorId attribute", TgiFaultCode.INVALID_ARGUMENT)
        obj.vector_id = vectorId  # type: ignore[attr-defined]
    return True


def setVectorLeft(vectorID: str, left: str | int | None) -> bool:  # Compatibility helper
    """Set the left endpoint expression through the compatibility API.

    Section: Nonstandard compatibility helper; no Annex F operation.

    Args:
        vectorID: Vector or containing element handle.
        left: Endpoint expression or attribute value.

    Returns:
        True on successful mutation.
    """
    vec = _ensure_vector(vectorID)
    _set_endpoint(vec, "left", _make_endpoint(left))
    return True


def setVectorRight(vectorID: str, right: str | int | None) -> bool:  # Compatibility helper
    """Set the right endpoint expression through the compatibility API.

    Section: Nonstandard compatibility helper; no Annex F operation.

    Args:
        vectorID: Vector or containing element handle.
        right: Endpoint expression or attribute value.

    Returns:
        True on successful mutation.
    """
    vec = _ensure_vector(vectorID)
    _set_endpoint(vec, "right", _make_endpoint(right))
    return True
