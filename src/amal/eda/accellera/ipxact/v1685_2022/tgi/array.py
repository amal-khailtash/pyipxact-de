"""Array category TGI functions for IEEE 1685-2022 Annex F.

This module implements the BASE calls in F.7.13 and the EXTENDED calls in
F.7.14. It follows the generated 1685-2022 schema classes because the XML
schema defines distinct array forms: port and parameter arrays have left/right
bounds in an ``arrays`` wrapper, register arrays contain ``dim`` plus optional
``stride``, and register-field arrays contain ``dim`` plus optional
``bitStride``. A ``dim`` value is preserved as an expression and may carry an
``indexVar`` XML ``Name`` attribute.

Numeric getters convert integer literals and evaluate self-contained
SystemVerilog integer expressions with slang. References that need IP-XACT
parameter or scope resolution return ``None``. Extended mutations create the
corresponding generated binding objects, reject malformed argument shapes
before editing, and keep handle ownership synchronized with model ownership.
Removing the final bounded array removes its now-empty optional wrapper so the
parent remains serializable under the schema.
"""

from collections.abc import Sequence
from typing import Any, get_args, get_type_hints
from unicodedata import category

from org.accellera.ipxact.v1685_2022 import (
    AddressBlockType,
    Array,
    Arrays,
    BitStride,
    ConfigurableArrays,
    Dim,
    FieldType,
    Left,
    ModuleParameterArrays,
    RegisterFile,
    Right,
    Stride,
)

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    resolve_handle,
)

__all__ = [
    # BASE (F.7.13)
    "getArrayDimIDs",
    "getArrayIDs",
    "getArrayLeftID",
    "getArrayRange",
    "getArrayRangeExpression",
    "getArrayRightID",
    "getArrayStride",
    "getArrayStrideExpression",
    "getArrayStrideID",
    "getDimExpression",
    "getDimIndexVar",
    "getDimValue",
    "getRegisterArrayID",
    "getRegisterFieldArrayID",
    # EXTENDED (F.7.14)
    "addArray",
    "addArrayDim",
    "removeArray",
    "removeArrayDim",
    "removeArrayStride",
    "removeIndexVarAttribute",
    "setArrayStride",
    "setDimIndexVar",
]


_BOUNDED_ARRAY_TYPES = (Arrays.Array, ConfigurableArrays.Array, ModuleParameterArrays.Array)
_DIM_ARRAY_TYPES = (Array, FieldType.Array)
_ARRAY_TYPES = _BOUNDED_ARRAY_TYPES + _DIM_ARRAY_TYPES
_ARRAY_CONTAINER_TYPES = (Arrays, ConfigurableArrays, ModuleParameterArrays)


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _resolve_array(arrayID: str) -> Any:
    """Resolve one of the array elements defined by the 1685-2022 schema."""
    obj = resolve_handle(arrayID)
    if not isinstance(obj, _ARRAY_TYPES):
        raise TgiError("Invalid array handle", TgiFaultCode.INVALID_ID)
    return obj


def _resolve_dim(dimID: str) -> Dim:
    """Resolve a schema-bound ``dim`` element."""
    obj = resolve_handle(dimID)
    if not isinstance(obj, Dim):
        raise TgiError("Invalid dim handle", TgiFaultCode.INVALID_ID)
    return obj


def _int_value(expr_obj: Any) -> int | None:
    """Convert a literal or evaluate a self-contained SystemVerilog integer expression."""
    if expr_obj is None:
        return None
    try:
        value = expr_obj.value
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return int(value, 0) if value.lower().startswith(("0x", "0o", "0b")) else int(value)
        except ValueError:
            from amal.eda.systemverilog.expression_parser import SvExpressionParser

            evaluated = SvExpressionParser().evaluate(value)
            return evaluated if type(evaluated) is int else None
    except ImportError, ValueError, TypeError, AttributeError:
        return None


def _expression(value: Any, argument: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TgiError(f"{argument} must be a non-empty string", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _bounded_array_wrapper(parent: Any) -> tuple[type, Any] | None:
    """Return the schema-declared wrapper class and current value for ``parent.arrays``."""
    if not hasattr(parent, "arrays"):
        return None
    current = parent.arrays
    if current is not None:
        if type(current) not in _ARRAY_CONTAINER_TYPES:
            return None
        return type(current), current

    try:
        annotation = get_type_hints(type(parent)).get("arrays")
    except NameError, TypeError:
        return None
    declared = [candidate for candidate in get_args(annotation) if candidate in _ARRAY_CONTAINER_TYPES]
    if len(declared) != 1:
        return None
    return declared[0], None


def _valid_name(value: str) -> bool:
    """Check the XML Schema ``xs:Name`` lexical form for an indexVar."""
    if not value:
        return False

    def is_start(char: str) -> bool:
        return char in "_:" or category(char) in {"Lu", "Ll", "Lt", "Lm", "Lo", "Nl"}

    def is_name_char(char: str) -> bool:
        return is_start(char) or char in "-." or category(char) in {"Mn", "Mc", "Nd", "Pc"}

    return is_start(value[0]) and all(is_name_char(char) for char in value[1:])


# ---------------------------------------------------------------------------
# BASE (F.7.13)
# ---------------------------------------------------------------------------


def getArrayDimIDs(arrayOrfieldArrayID: str) -> list[str]:  # F.7.13.1
    """Return handles to all dimensions on a register or register-field array.

    Args:
        arrayOrfieldArrayID: Handle to a register or register-field array.

    Returns:
        List of handles to the array's ``dim`` elements.

    Section: F.7.13.1.
    """
    arr = _resolve_array(arrayOrfieldArrayID)
    if not isinstance(arr, _DIM_ARRAY_TYPES):
        return []
    result = []
    for dim in arr.dim:
        register_parent(dim, arr, ("dim",), "list")
        result.append(get_handle(dim))
    return result


def getArrayIDs(arrayContainerElementID: str) -> list[str]:  # F.7.13.2
    """Return handles of arrays contained by an element.

    Args:
        arrayContainerElementID: Handle to an element that contains arrays.

    Returns:
        List of handles to bounded arrays or the register/field array, if present.

    Section: F.7.13.2.
    """
    parent = resolve_handle(arrayContainerElementID)
    if parent is None:
        raise TgiError("Invalid array container handle", TgiFaultCode.INVALID_ID)

    # Prefer list container 'arrays'
    wrapper = getattr(parent, "arrays", None)
    if type(wrapper) in _ARRAY_CONTAINER_TYPES:
        result = []
        for item in wrapper.array:
            if not isinstance(item, _BOUNDED_ARRAY_TYPES):
                continue
            register_parent(item, parent, ("arrays", "array"), "list")
            result.append(get_handle(item))
        return result

    # Fallback single attribute 'array'
    arr = getattr(parent, "array", None)
    if isinstance(arr, _ARRAY_TYPES):
        register_parent(arr, parent, ("array",), "single")
        return [get_handle(arr)]
    return []


def getArrayLeftID(arrayID: str) -> str | None:  # F.7.13.3
    """Return the handle of the array's ``left`` bound, if it exists.

    Args:
        arrayID: Handle to an array element.

    Returns:
        Handle to the ``left`` bound, or ``None`` when it is absent.

    Section: F.7.13.3.
    """
    arr = _resolve_array(arrayID)
    left = getattr(arr, "left", None)
    if left is None:
        return None
    register_parent(left, arr, ("left",), "single")
    return get_handle(left)


def getArrayRange(arrayID: str) -> list[int | None]:  # F.7.13.4
    """Return integer values for the array's left and right bound expressions.

    Args:
        arrayID: Handle to an array element.

    Returns:
        Two values ordered as left then right; unresolved expressions return ``None``.

    Section: F.7.13.4.
    """
    arr = _resolve_array(arrayID)
    return [_int_value(getattr(arr, bound, None)) for bound in ("left", "right")]


def getArrayRangeExpression(arrayID: str) -> list[str | None]:  # F.7.13.5
    """Return the original expressions for the array's left and right bounds.

    Args:
        arrayID: Handle to an array element.

    Returns:
        Two expressions ordered as left then right; missing bounds return ``None``.

    Section: F.7.13.5.
    """
    arr = _resolve_array(arrayID)
    return [getattr(getattr(arr, bound, None), "value", None) for bound in ("left", "right")]


def getArrayRightID(arrayID: str) -> str | None:  # F.7.13.6
    """Return the handle of the array's ``right`` bound, if it exists.

    Args:
        arrayID: Handle to an array element.

    Returns:
        Handle to the ``right`` bound, or ``None`` when it is absent.

    Section: F.7.13.6.
    """
    arr = _resolve_array(arrayID)
    right = getattr(arr, "right", None)
    if right is None:
        return None
    register_parent(right, arr, ("right",), "single")
    return get_handle(right)


def getArrayStride(arrayID: str) -> int | None:  # F.7.13.7
    """Return an integer literal stride value, if one is defined.

    Args:
        arrayID: Handle to a register or register-field array.

    Returns:
        Integer stride value, or ``None`` for unresolved expressions or absent strides.

    Section: F.7.13.7.
    """
    arr = _resolve_array(arrayID)
    stride = getattr(arr, "bit_stride", None) if isinstance(arr, FieldType.Array) else getattr(arr, "stride", None)
    return _int_value(stride)


def getArrayStrideExpression(arrayID: str) -> str | None:  # F.7.13.8
    """Return the original stride expression, if one is defined.

    Args:
        arrayID: Handle to a register or register-field array.

    Returns:
        Stride expression, or ``None`` when no stride is defined.

    Section: F.7.13.8.
    """
    arr = _resolve_array(arrayID)
    stride = getattr(arr, "bit_stride", None) if isinstance(arr, FieldType.Array) else getattr(arr, "stride", None)
    return getattr(stride, "value", None) if stride is not None else None


def getArrayStrideID(arrayOrfieldArrayID: str) -> str | None:  # F.7.13.9
    """Return a handle to a register stride or field ``bitStride`` element.

    Args:
        arrayOrfieldArrayID: Handle to a register or register-field array.

    Returns:
        Handle to the stride element, or ``None`` when absent.

    Section: F.7.13.9.
    """
    arr = _resolve_array(arrayOrfieldArrayID)
    if isinstance(arr, FieldType.Array):
        name = "bit_stride"
    elif isinstance(arr, Array):
        name = "stride"
    else:
        return None
    stride = getattr(arr, name)
    if stride is None:
        return None
    register_parent(stride, arr, (name,), "single")
    return get_handle(stride)


def getDimExpression(dimID: str) -> str:  # F.7.13.10
    """Return the expression text stored in a ``dim`` element.

    Args:
        dimID: Handle to a ``dim`` element.

    Returns:
        The dimension expression.

    Section: F.7.13.10.
    """
    return _resolve_dim(dimID).value


def getDimIndexVar(dimID: str) -> str | None:  # F.7.13.11
    """Return the ``indexVar`` attribute of a dimension.

    Args:
        dimID: Handle to a ``dim`` element.

    Returns:
        The index variable name, or ``None`` when the attribute is absent.

    Section: F.7.13.11.
    """
    return _resolve_dim(dimID).index_var


def getDimValue(dimID: str) -> int | None:  # F.7.13.12
    """Return an integer value for the dimension, or ``None`` when unresolved.

    Args:
        dimID: Handle to a ``dim`` element.

    Returns:
        Integer dimension value, or ``None`` when the value is unresolved or non-integer.

    Section: F.7.13.12.
    """
    return _int_value(_resolve_dim(dimID))


def getRegisterArrayID(registerID: str) -> str | None:  # F.7.13.13
    """Return the handle of the array on a register, if present.

    Args:
        registerID: Handle to a register.

    Returns:
        Handle to the register's array, or ``None`` when absent.

    Section: F.7.13.13.
    """
    reg = resolve_handle(registerID)
    if not isinstance(reg, (AddressBlockType.Register, RegisterFile.Register)):
        raise TgiError("Invalid register handle", TgiFaultCode.INVALID_ID)
    arr = reg.array
    if arr is None:
        return None
    if not isinstance(arr, Array):
        raise TgiError("Invalid register array", TgiFaultCode.INVALID_ID)
    register_parent(arr, reg, ("array",), "single")
    return get_handle(arr)


def getRegisterFieldArrayID(registerFieldID: str) -> str | None:  # F.7.13.14
    """Return the handle of the array on a register field, if present.

    Args:
        registerFieldID: Handle to a register field.

    Returns:
        Handle to the field's array, or ``None`` when absent.

    Section: F.7.13.14.
    """
    fld = resolve_handle(registerFieldID)
    if not isinstance(fld, FieldType):
        raise TgiError("Invalid field handle", TgiFaultCode.INVALID_ID)
    arr = fld.array
    if arr is None:
        return None
    if not isinstance(arr, FieldType.Array):
        raise TgiError("Invalid field array", TgiFaultCode.INVALID_ID)
    register_parent(arr, fld, ("array",), "single")
    return get_handle(arr)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.14)
# ---------------------------------------------------------------------------


def addArray(arrayContainerElementID: str, range: Sequence[str]) -> str:  # F.7.14.1
    """Add a bounded array with left and right range expressions to an element.

    Args:
        arrayContainerElementID: Handle to an element that contains arrays.
        range: Two expressions, with the left bound at index 0 and right at index 1.

    Returns:
        Handle to the created array.

    Section: F.7.14.1.
    """
    parent = resolve_handle(arrayContainerElementID)
    if parent is None:
        raise TgiError("Invalid array container handle", TgiFaultCode.INVALID_ID)
    if isinstance(range, (str, bytes)) or not isinstance(range, Sequence) or len(range) != 2:
        raise TgiError("range must contain left and right expressions", TgiFaultCode.INVALID_ARGUMENT)
    left_value, right_value = (_expression(value, "range expression") for value in range)

    declared = _bounded_array_wrapper(parent)
    if declared is None:
        raise TgiError("Element cannot contain a bounded array", TgiFaultCode.INVALID_ARGUMENT)
    wrapper_type, wrapper = declared
    child_types = {
        Arrays: Arrays.Array,
        ConfigurableArrays: ConfigurableArrays.Array,
        ModuleParameterArrays: ModuleParameterArrays.Array,
    }
    item = child_types[wrapper_type](left=Left(value=left_value), right=Right(value=right_value))

    if wrapper is None:
        wrapper = wrapper_type(array=[item])
        parent.arrays = wrapper
    else:
        items = wrapper.array
        if (
            isinstance(items, (str, bytes))
            or not isinstance(items, Sequence)
            or any(not isinstance(existing, _BOUNDED_ARRAY_TYPES) for existing in items)
        ):
            raise TgiError("Array container has invalid contents", TgiFaultCode.INVALID_ID)
        if isinstance(items, list):
            items.append(item)
        else:
            wrapper.array = [*items, item]

    register_parent(item, parent, ("arrays", "array"), "list")
    return get_handle(item)


def addArrayDim(arrayOrfieldArrayID: str, value: str) -> str:  # F.7.14.2
    """Add a dimension to a register or register-field array.

    Args:
        arrayOrfieldArrayID: Handle to a register or register-field array.
        value: Dimension value or expression.

    Returns:
        Handle to the added ``dim`` element.

    Section: F.7.14.2.
    """
    arr = _resolve_array(arrayOrfieldArrayID)
    if not isinstance(arr, _DIM_ARRAY_TYPES):
        raise TgiError("Array does not contain dimensions", TgiFaultCode.INVALID_ARGUMENT)
    expression = _expression(value, "value")
    dim = Dim(value=expression)
    if isinstance(arr.dim, list):
        arr.dim.append(dim)
    else:
        arr.dim = [*arr.dim, dim]
    register_parent(dim, arr, ("dim",), "list")
    return get_handle(dim)


def removeArray(arrayID: str) -> bool:  # F.7.14.3
    """Remove an array from its schema parent and invalidate its handles.

    Args:
        arrayID: Handle to an array element.

    Returns:
        ``True`` when the array was removed; otherwise ``False``.

    Section: F.7.14.3.
    """
    arr = _resolve_array(arrayID)
    info = get_parent_info(arrayID)
    removed = detach_child_by_handle(arrayID)
    if removed and isinstance(arr, _BOUNDED_ARRAY_TYPES) and info is not None and info.path == ("arrays", "array"):
        parent = resolve_handle(info.parent_handle)
        wrapper = getattr(parent, "arrays", None) if parent is not None else None
        if type(wrapper) in _ARRAY_CONTAINER_TYPES and not wrapper.array:
            parent.arrays = None
    return removed


def removeArrayDim(dimID: str) -> bool:  # F.7.14.4
    """Remove a dimension from its array and invalidate its handle.

    Args:
        dimID: Handle to a ``dim`` element.

    Returns:
        ``True`` when the dimension was removed; otherwise ``False``.

    Section: F.7.14.4.
    """
    _resolve_dim(dimID)
    info = get_parent_info(dimID)
    if info is not None and info.path == ("dim",):
        parent = resolve_handle(info.parent_handle)
        if isinstance(parent, _DIM_ARRAY_TYPES) and len(parent.dim) == 1:
            raise TgiError("An array must retain at least one dimension", TgiFaultCode.INVALID_ARGUMENT)
    return detach_child_by_handle(dimID)


def removeArrayStride(arrayID: str) -> bool:  # F.7.14.5
    """Remove a register stride or field ``bitStride`` and invalidate its handle.

    Args:
        arrayID: Handle to a register or register-field array.

    Returns:
        ``True`` when a stride was removed; otherwise ``False``.

    Section: F.7.14.5.
    """
    arr = _resolve_array(arrayID)
    if isinstance(arr, FieldType.Array):
        name = "bit_stride"
    elif isinstance(arr, Array):
        name = "stride"
    else:
        raise TgiError("Array does not contain a stride", TgiFaultCode.INVALID_ARGUMENT)
    stride = getattr(arr, name)
    if stride is None:
        return False
    stride_id = get_handle(stride)
    register_parent(stride, arr, (name,), "single")
    return detach_child_by_handle(stride_id)


def removeIndexVarAttribute(dimID: str) -> bool:  # F.7.14.6
    """Remove the ``indexVar`` attribute from a dimension.

    Args:
        dimID: Handle to a ``dim`` element.

    Returns:
        ``True`` when the attribute was removed; otherwise ``False``.

    Section: F.7.14.6.
    """
    dim = _resolve_dim(dimID)
    if dim.index_var is None:
        return False
    dim.index_var = None
    return True


def setArrayStride(arrayID: str, stride: str) -> bool:  # F.7.14.7
    """Set or create a register stride or field ``bitStride`` expression.

    Args:
        arrayID: Handle to a register or register-field array.
        stride: New stride value or expression.

    Returns:
        ``True`` when the stride was set.

    Section: F.7.14.7.
    """
    arr = _resolve_array(arrayID)
    expression = _expression(stride, "stride")
    if isinstance(arr, FieldType.Array):
        name, replacement = "bit_stride", BitStride(value=expression)
    elif isinstance(arr, Array):
        name, replacement = "stride", Stride(value=expression)
    else:
        raise TgiError("Array does not contain a stride", TgiFaultCode.INVALID_ARGUMENT)

    previous = getattr(arr, name)
    if previous is not None:
        previous_id = get_handle(previous)
        register_parent(previous, arr, (name,), "single")
        detach_child_by_handle(previous_id)
    setattr(arr, name, replacement)
    register_parent(replacement, arr, (name,), "single")
    return True


def setDimIndexVar(dimID: str, value: str) -> bool:  # F.7.14.8
    """Set the ``indexVar`` attribute on a dimension.

    Args:
        dimID: Handle to a ``dim`` element.
        value: New XML Name for the index variable.

    Returns:
        ``True`` when the attribute was set.

    Section: F.7.14.8.
    """
    dim = _resolve_dim(dimID)
    index_var = _expression(value, "value")
    if not _valid_name(index_var):
        raise TgiError("value must be an XML Name", TgiFaultCode.INVALID_ARGUMENT)

    owner_info = get_parent_info(dimID)
    if owner_info is not None and owner_info.path == ("dim",):
        owner = resolve_handle(owner_info.parent_handle)
        if isinstance(owner, _DIM_ARRAY_TYPES) and any(
            sibling is not dim and sibling.index_var == index_var for sibling in owner.dim
        ):
            raise TgiError("indexVar must be unique within its array", TgiFaultCode.INVALID_ARGUMENT)
    dim.index_var = index_var
    return True
