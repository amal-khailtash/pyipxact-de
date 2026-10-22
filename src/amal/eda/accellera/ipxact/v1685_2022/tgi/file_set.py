"""File set category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.47) and EXTENDED (F.7.48) *File set* functions.
Only the exact public API defined by Annex F is exported.  These functions
cover traversal of fileSets, files, default file builders, functions (SW
functions inside a fileSet), and their subordinate argument / sourceFile
elements; plus mutation helpers for the EXTENDED section.

Design notes:
* Absent optional children return ``None`` (or empty list) – invalid handles
  raise ``TgiError`` with ``INVALID_ID``.
* Newly created child objects are registered with their parent via
  ``register_parent`` allowing later detach via remove* functions.
* The 2022 schema expresses many list-valued fields as ``Iterable`` but
  uses ``list`` factories; we treat them as mutable lists (adding a
  ``# type: ignore`` where static checkers complain).
* FileSet references and groups live in their owning component, bus-interface,
  or executable-image structures. Reference lookups stay within that registered
  document, and group operations accept each schema-defined group type.
"""

from collections.abc import Iterable, Sequence
from dataclasses import fields, is_dataclass
from typing import Any

from org.accellera.ipxact.v1685_2022 import (
    DataTypeType,
    Dependency,
    File,
    FileBuilderType,
    FileSet,
    FileSetRef,
    FileType,
    IpxactUri,
    NameValuePairType,
    Value,
)
from org.accellera.ipxact.v1685_2022.file_set_type import FileSetType
from org.accellera.ipxact.v1685_2022.return_type_type import ReturnTypeType
from org.accellera.ipxact.v1685_2022.simple_file_type import SimpleFileType
from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression

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
    # BASE (F.7.47.x)
    "getBuildCommandReplaceDefaultFlagsExpression",
    "getFileDefineIDs",
    "getFileDefineSymbolValue",
    "getFileDependencyIDs",
    "getFileExportedNameIDs",
    "getFileExportedNames",
    "getFileFileTypeIDs",
    "getFileFileTypes",
    "getFileImageTypeIDs",
    "getFileImageTypes",
    "getFileIsIncludeFile",
    "getFileIsIncludeFileID",
    "getFileIsStructural",
    "getFileLogicalName",
    "getFileLogicalNameID",
    "getFileName",
    "getFileSetDefaultFileBuilderIDs",
    "getFileSetDependencyIDs",
    "getFileSetFileIDs",
    "getFileSetFunctionIDs",
    "getFileSetGroupFileSetRefIDs",
    "getFileSetGroupIDs",
    "getFileSetGroups",
    "getFileSetRefByID",
    "getFileSetRefGroupFileSetRefIDs",
    "getFileSetRefLocalNameRefByID",
    "getFunctionArgumentDataType",
    "getFunctionArgumentIDs",
    "getFunctionDisabled",
    "getFunctionDisabledExpression",
    "getFunctionDisabledID",
    "getFunctionEntryPoint",
    "getFunctionFileID",
    "getFunctionFileRefByID",
    "getFunctionFileRefByName",
    "getFunctionReplicate",
    "getFunctionReturnType",
    "getFunctionSourceFileIDs",
    "getFunctionSourceFileName",
    "getFunctionSourceFileType",
    "getSourceFileFileType",
    "getSourceFileFileTypeID",
    "getSourceFileSourceName",
    # EXTENDED (F.7.48.x)
    "addFileDefine",
    "addFileDependency",
    "addFileExportedName",
    "addFileFileType",
    "addFileImageType",
    "addFileSetDefaultFileBuilder",
    "addFileSetDependency",
    "addFileSetFile",
    "addFileSetFunction",
    "addFileSetGroup",
    "addFileSetRefGroupFileSetRef",
    "addFunctionArgument",
    "addFunctionSourceFile",
    "removeFileBuildCommand",
    "removeFileDefine",
    "removeFileDependency",
    "removeFileExportedName",
    "removeFileFileType",
    "removeFileImageType",
    "removeFileIsIncludeFile",
    "removeFileIsStructural",
    "removeFileLogicalName",
    "removeFileSetDefaultFileBuilder",
    "removeFileSetDependency",
    "removeFileSetFile",
    "removeFileSetFunction",
    "removeFileSetGroup",
    "removeFunctionArgument",
    "removeFunctionDisabled",
    "removeFunctionEntryPoint",
    "removeFunctionReturnType",
    "removeFunctionSourceFile",
    "setFileIsIncludeFile",
    "setFileIsStructural",
    "setFileLogicalName",
    "setFileName",
    "setFunctionArgumentDataType",
    "setFunctionDisabled",
    "setFunctionEntryPoint",
    "setFunctionFileRef",
    "setFunctionReplicate",
    "setFunctionReturnType",
    "setFunctionSourceFileName",
    "setSourceFileFileType",
    "setSourceFileSourceName",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_fileset(fileSetID: str) -> FileSet:
    fs = resolve_handle(fileSetID)
    if not isinstance(fs, FileSet):
        raise TgiError("Invalid fileSet handle", TgiFaultCode.INVALID_ID)
    return fs


def _resolve_file(fileID: str) -> File:
    f = resolve_handle(fileID)
    if not isinstance(f, File):
        raise TgiError("Invalid file handle", TgiFaultCode.INVALID_ID)
    return f


def _resolve_function(functionID: str) -> FileSetType.Function:
    fn = resolve_handle(functionID)
    if not isinstance(fn, FileSetType.Function):
        raise TgiError("Invalid function handle", TgiFaultCode.INVALID_ID)
    return fn


def _resolve_build_command(buildCommandID: str) -> File.BuildCommand:
    command = resolve_handle(buildCommandID)
    if not isinstance(command, File.BuildCommand):
        raise TgiError("Invalid buildCommand handle", TgiFaultCode.INVALID_ID)
    return command


def _resolve_argument(argumentID: str) -> FileSetType.Function.Argument:
    arg = resolve_handle(argumentID)
    if not isinstance(arg, FileSetType.Function.Argument):
        raise TgiError("Invalid argument handle", TgiFaultCode.INVALID_ID)
    return arg


def _resolve_source_file(sourceFileID: str) -> FileSetType.Function.SourceFile:
    sf = resolve_handle(sourceFileID)
    if not isinstance(sf, FileSetType.Function.SourceFile):
        raise TgiError("Invalid sourceFile handle", TgiFaultCode.INVALID_ID)
    return sf


def _resolve_define(defineID: str) -> NameValuePairType:
    dv = resolve_handle(defineID)
    if not isinstance(dv, NameValuePairType):
        raise TgiError("Invalid fileDefine handle", TgiFaultCode.INVALID_ID)
    return dv


def _resolve_dependency(dependencyID: str) -> Dependency:
    dep = resolve_handle(dependencyID)
    if not isinstance(dep, Dependency):
        raise TgiError("Invalid dependency handle", TgiFaultCode.INVALID_ID)
    return dep


def _owned_file_ids(fileID: str, field: str) -> list[str]:
    """Return stable generated file-child handles and restore parsed ownership."""
    owner = _resolve_file(fileID)
    children = getattr(owner, field)
    for child in children:
        register_parent(child, owner, (field,), "list")
    return [get_handle(child) for child in children]


def _ids(items: Iterable[Any]) -> list[str]:
    return [get_handle(x) for x in items]


def _require_string(value: Any, argument: str) -> str:
    if not isinstance(value, str):
        raise TgiError(f"{argument} must be a string", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _walk_model(root: Any) -> Iterable[Any]:
    """Yield each dataclass model node once, including descendants."""
    pending = [root]
    visited: set[int] = set()
    while pending:
        obj = pending.pop()
        if obj is None or id(obj) in visited:
            continue
        visited.add(id(obj))
        yield obj
        if is_dataclass(obj) and not isinstance(obj, type):
            pending.extend(getattr(obj, item.name) for item in fields(obj))
        elif isinstance(obj, (list, tuple)):
            pending.extend(obj)


def _file_set_for_function(function: FileSetType.Function) -> FileSet | None:
    """Find the containing fileSet from restored ownership or a registered XML root."""
    info = get_parent_info(get_handle(function))
    visited: set[str] = set()
    while info is not None and info.parent_handle not in visited:
        visited.add(info.parent_handle)
        parent = resolve_handle(info.parent_handle)
        if isinstance(parent, FileSet):
            return parent
        info = get_parent_info(info.parent_handle)
    for root_id in registry.iter_by_predicate(lambda _root: True):
        root = resolve_handle(root_id)
        for node in _walk_model(root):
            if isinstance(node, FileSet) and any(child is function for child in node.function):
                if getattr(root, "file_sets", None) is not None:
                    register_parent(node, root, ("file_sets", "file_set"), "list")
                return node
    return None


def _resolve_function_file(function: FileSetType.Function) -> File | None:
    """Resolve function/fileRef by fileId inside its owning fileSet."""
    file_set = _file_set_for_function(function)
    if file_set is None:
        return None
    target = next((file for file in file_set.file if file.file_id == function.file_ref), None)
    if target is not None:
        register_parent(target, file_set, ("file",), "list")
    return target


def _file_set_ref_group_types() -> tuple[type, ...]:
    """Return schema classes that represent fileSetRefGroup containers."""
    from org.accellera.ipxact.v1685_2022 import BusInterfaceType, ExecutableImage

    return (
        BusInterfaceType.Target.FileSetRefGroup,
        ExecutableImage.FileSetRefGroup,
    )


def _resolve_file_set_ref_group(fileSetRefGroupID: str) -> Any:
    group = resolve_handle(fileSetRefGroupID)
    if not isinstance(group, _file_set_ref_group_types()):
        raise TgiError("Invalid fileSetRefGroup handle", TgiFaultCode.INVALID_ID)
    return group


def _resolve_file_set_reference(fileSetRefID: str) -> FileSetRef:
    ref = resolve_handle(fileSetRefID)
    if not isinstance(ref, FileSetRef):
        raise TgiError("Invalid fileSetRef handle", TgiFaultCode.INVALID_ID)
    return ref


def _referenced_file_set(ref: FileSetRef) -> FileSet | None:
    """Resolve localName against the fileSets in the same registered document."""
    for root_id in registry.iter_by_predicate(lambda _root: True):
        root = resolve_handle(root_id)
        nodes = tuple(_walk_model(root))
        if not any(node is ref for node in nodes):
            continue
        file_sets = getattr(root, "file_sets", None)
        candidates = getattr(file_sets, "file_set", ()) if file_sets is not None else ()
        matches = [candidate for candidate in candidates if candidate.name == ref.local_name]
        if len(matches) == 1:
            register_parent(matches[0], root, ("file_sets", "file_set"), "list")
            return matches[0]
        return None
    return None


def _enum_file_type(value: str) -> FileType:
    if not isinstance(value, str):
        raise TgiError("Expected a fileType string", TgiFaultCode.INVALID_ARGUMENT)
    try:
        simple = SimpleFileType(value)
    except ValueError as exc:  # invalid enum literal
        raise TgiError("Unknown FileType", TgiFaultCode.INVALID_ARGUMENT) from exc
    return FileType(value=simple)


def _enum_data_type(value: str) -> DataTypeType:
    if not isinstance(value, str):
        raise TgiError("Expected a dataType string", TgiFaultCode.INVALID_ARGUMENT)
    try:
        return DataTypeType(value)
    except ValueError as exc:
        raise TgiError("Unknown function argument dataType", TgiFaultCode.INVALID_ARGUMENT) from exc


def _validate_bool(value: Any, argument: str) -> bool:
    if type(value) is not bool:
        raise TgiError(f"{argument} must be a Boolean", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _evaluate_unsigned_bit_expression(expression: str | None) -> bool:
    """Evaluate a self-contained SystemVerilog integer expression when possible."""
    if expression is None:
        return False
    try:
        value = int(expression, 0) if expression.lower().startswith(("0x", "0o", "0b")) else int(expression)
    except ValueError:
        try:
            from amal.eda.systemverilog.expression_parser import SvExpressionParser

            value = SvExpressionParser().evaluate(expression)
        except (ImportError, ValueError, TypeError, RuntimeError):
            return False
    return bool(value) if isinstance(value, (int, bool)) else False


def _remove_owned_list_child(
    childID: str,
    expected_type: type | tuple[type, ...],
    owner_type: type | tuple[type, ...],
    field: str,
) -> bool:
    child = resolve_handle(childID)
    if not isinstance(child, expected_type):
        raise TgiError("Invalid child handle", TgiFaultCode.INVALID_ID)
    info = get_parent_info(childID)
    if info is None:
        return False
    owner = resolve_handle(info.parent_handle)
    if info.path != (field,) or not isinstance(owner, owner_type):
        raise TgiError("Child is not owned by the expected element", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(childID)


def _remove_optional_child(owner: Any, field: str) -> bool:
    child = getattr(owner, field)
    if child is None:
        return False
    register_parent(child, owner, (field,), "single")
    return detach_child_by_handle(get_handle(child))


# ---------------------------------------------------------------------------
# BASE (F.7.47)
# ---------------------------------------------------------------------------

def getBuildCommandReplaceDefaultFlagsExpression(buildCommandID: str) -> str | None:  # F.7.47.1
    """Return the raw replaceDefaultFlags expression on a build command.

    Args:
        buildCommandID: Handle to a buildCommand element.

    Returns:
        The expression text, or None when replaceDefaultFlags is absent.

    Section: F.7.47.1.
    """
    command = _resolve_build_command(buildCommandID)
    if command.replace_default_flags is None:
        return None
    return command.replace_default_flags.value


def getFileDefineIDs(fileID: str) -> list[str]:  # F.7.47.2
    """Restore parsed ownership and return handles of define symbols.

Args:
    fileID: Handle to a file element

Returns:
    fileDefineIDs of type String - List of handles to the fileDefine elements

Section: F.7.47.2."""
    return _owned_file_ids(fileID, "define")


def getFileDefineSymbolValue(fileDefineID: str) -> str | None:  # F.7.47.3
    """Return the generated define value source string.

Args:
    fileDefineID: Handle to a fileDefine element

Returns:
    value of type String - The file define value

Section: F.7.47.3."""
    d = _resolve_define(fileDefineID)
    return d.value.value


def getFileDependencyIDs(fileID: str) -> list[str]:  # F.7.47.4
    """Restore parsed ownership and return dependency handles for a file.

Args:
    fileID: Handle to a file element

Returns:
    dependencyIDs of type String - List of handles to the dependency elements

Section: F.7.47.4."""
    return _owned_file_ids(fileID, "dependency")


def getFileExportedNameIDs(fileID: str) -> list[str]:  # F.7.47.5
    """Restore parsed ownership and return exportedName handles.

Args:
    fileID: Handle to a file element

Returns:
    exportedNameIDs of type String - List of handles to the exportedName elements

Section: F.7.47.5."""
    return _owned_file_ids(fileID, "exported_name")


def getFileExportedNames(fileID: str) -> list[str]:  # F.7.47.6
    """Return exported names.

Args:
    fileID: Handle to a file element

Returns:
    exportedNames of type String - List of exported names

Section: F.7.47.6."""
    return [getattr(en, "value", "") for en in _resolve_file(fileID).exported_name]


def getFileFileTypeIDs(fileID: str) -> list[str]:  # F.7.47.7
    """Restore parsed ownership and return fileType handles.

Args:
    fileID: Handle to a file element

Returns:
    fileTypeID of type String - List of handles to the fileType elements

Section: F.7.47.7."""
    return _owned_file_ids(fileID, "file_type")


def getFileFileTypes(fileID: str) -> list[str]:  # F.7.47.8
    """Return fileType enumeration literals.

Args:
    fileID: Handle to a file element

Returns:
    fileTypes of type String - List of file types

Section: F.7.47.8."""
    names: list[str] = []
    for ft in _resolve_file(fileID).file_type:
        val = getattr(ft, "value", None)
        if val is None:
            continue
        lit = getattr(val, "value", None)
        names.append(lit if lit is not None else str(val))
    return names


def getFileImageTypeIDs(fileID: str) -> list[str]:  # F.7.47.9
    """Return stable imageType handles and restore parsed ownership.

Args:
    fileID: Handle to a file element

Returns:
    imageTypeIDs of type String - List of handles to the imageType elements

Section: F.7.47.9."""
    return _owned_file_ids(fileID, "image_type")


def getFileImageTypes(fileID: str) -> list[str]:  # F.7.47.10
    """Return image type values.

Args:
    fileID: Handle to a file element

Returns:
    imageTypes of type String - List of image types

Section: F.7.47.10."""
    return [getattr(it, "value", "") for it in _resolve_file(fileID).image_type]


def getFileIsIncludeFile(fileID: str) -> bool:  # F.7.47.11
    """Return explicit include state; default to False when absent.

Args:
    fileID: Handle to a file element

Returns:
    value of type Boolean - The isIncludeFile value

Section: F.7.47.11."""
    inc = _resolve_file(fileID).is_include_file
    return bool(getattr(inc, "value", False)) if inc is not None else False


def getFileIsIncludeFileID(fileID: str) -> str | None:  # F.7.47.12
    """Return the include child handle with parsed ownership.

Args:
    fileID: Handle to a file element

Returns:
    isIncludeFileID of type String - Handle to the isIncludeFile element

Section: F.7.47.12."""
    f = _resolve_file(fileID)
    if f.is_include_file is None:
        return None
    register_parent(f.is_include_file, f, ("is_include_file",), "single")
    return get_handle(f.is_include_file)


def getFileIsStructural(fileID: str) -> bool:  # F.7.47.13
    """Return explicit structural state; default to False when absent.

Args:
    fileID: Handle to a file element

Returns:
    value of type Boolean - File isStructural value

Section: F.7.47.13."""
    return bool(_resolve_file(fileID).is_structural)


def getFileLogicalName(fileID: str) -> str | None:  # F.7.47.14
    """Return logicalName value.

Args:
    fileID: Handle to a file element

Returns:
    logicalName of type String - The logical name

Section: F.7.47.14."""
    ln = _resolve_file(fileID).logical_name
    return getattr(ln, "value", None) if ln is not None else None


def getFileLogicalNameID(fileID: str) -> str | None:  # F.7.47.15
    """Return the logical-name handle with parsed ownership.

Args:
    fileID: Handle to a file element

Returns:
    logicalNameID of type String - Handle to the logicalName element

Section: F.7.47.15."""
    f = _resolve_file(fileID)
    if f.logical_name is None:
        return None
    register_parent(f.logical_name, f, ("logical_name",), "single")
    return get_handle(f.logical_name)


def getFileName(fileID: str) -> str | None:  # F.7.47.16
    """Return file name path value.

Args:
    fileID: Handle to a file element

Returns:
    name of type String - The file name

Section: F.7.47.16."""
    n = _resolve_file(fileID).name
    return getattr(n, "value", None) if n is not None else None


def getFileSetDefaultFileBuilderIDs(fileSetID: str) -> list[str]:  # F.7.47.17
    """Return stable builder handles and restore parsed ownership.

Args:
    fileSetID: Handle to a fileSet element

Returns:
    fileBuilderIDs of type String - List of handles to the fileBuilder elements

Section: F.7.47.17."""
    fs = _resolve_fileset(fileSetID)
    for builder in fs.default_file_builder:
        register_parent(builder, fs, ("default_file_builder",), "list")
    return _ids(fs.default_file_builder)


def getFileSetDependencyIDs(fileSetID: str) -> list[str]:  # F.7.47.18
    """Return stable fileSet dependency handles with parsed ownership.

Args:
    fileSetID: Handle to a fileSet element

Returns:
    dependencyIDs of type String - List of handles to the fileSet elements

Section: F.7.47.18."""
    fs = _resolve_fileset(fileSetID)
    for child in fs.dependency:
        register_parent(child, fs, ("dependency",), "list")
    return _ids(fs.dependency)


def getFileSetFileIDs(fileSetID: str) -> list[str]:  # F.7.47.19
    """Return stable file handles with parsed ownership.

Args:
    fileSetID: Handle to a fileSet element

Returns:
    fileIDs of type String - List of handles to file elements

Section: F.7.47.19."""
    fs = _resolve_fileset(fileSetID)
    for child in fs.file:
        register_parent(child, fs, ("file",), "list")
    return _ids(fs.file)


def getFileSetFunctionIDs(fileSetID: str) -> list[str]:  # F.7.47.20
    """Return stable function handles with parsed ownership.

Args:
    fileSetID: Handle to a fileSet element

Returns:
    functionIDs of type String - List of handles to the function elements

Section: F.7.47.20."""
    fs = _resolve_fileset(fileSetID)
    for child in fs.function:
        register_parent(child, fs, ("function",), "list")
    return _ids(fs.function)


def getFileSetGroupFileSetRefIDs(fileSetRefGroupID: str) -> list[str]:  # F.7.47.21
    """Return handles of the references in a schema fileSetRefGroup.

    Args:
        fileSetRefGroupID: Handle to a fileSetRefGroup element.

    Returns:
        Handles of its direct fileSetRef children in document order.

    Section: F.7.47.21.
    """
    group = _resolve_file_set_ref_group(fileSetRefGroupID)
    for ref in group.file_set_ref:
        register_parent(ref, group, ("file_set_ref",), "list")
    return _ids(group.file_set_ref)


def getFileSetGroupIDs(fileSetID: str) -> list[str]:  # F.7.47.22
    """Return stable group handles with parsed ownership.

Args:
    fileSetID: Handle to a fileSet element

Returns:
    groupID of type String - List of handles to the group elements

Section: F.7.47.22."""
    fs = _resolve_fileset(fileSetID)
    for child in fs.group:
        register_parent(child, fs, ("group",), "list")
    return _ids(fs.group)


def getFileSetGroups(fileSetID: str) -> list[str]:  # F.7.47.23
    """Return group string values.

Args:
    fileSetID: Handle to a fileSet element

Returns:
    groups of type String - List of fileSet groups

Section: F.7.47.23."""
    return [getattr(g, "value", "") for g in _resolve_fileset(fileSetID).group]


def getFileSetRefByID(fileSetRefID: str) -> str | None:  # F.7.47.24
    """Resolve a fileSetRef to its owning document's fileSet.

    Args:
        fileSetRefID: Handle to a fileSetRef element.

    Returns:
        Handle to the referenced fileSet, or None when it cannot be resolved.

    Section: F.7.47.24.
    """
    ref = _resolve_file_set_reference(fileSetRefID)
    target = _referenced_file_set(ref)
    return get_handle(target) if target is not None else None


def getFileSetRefGroupFileSetRefIDs(fileSetRefGroupID: str) -> list[str]:  # F.7.47.25
    """Return handles of references in a schema fileSetRefGroup.

    Args:
        fileSetRefGroupID: Handle to a fileSetRefGroup element.

    Returns:
        Handles of its direct fileSetRef children in document order.

    Section: F.7.47.25.
    """
    return getFileSetGroupFileSetRefIDs(fileSetRefGroupID)


def getFileSetRefLocalNameRefByID(fileSetRefID: str) -> str | None:  # F.7.47.26
    """Resolve localName on a fileSetRef to its fileSet handle.

    Args:
        fileSetRefID: Handle to a fileSetRef element.

    Returns:
        Handle to the referenced fileSet, or None when it cannot be resolved.

    Section: F.7.47.26.
    """
    return getFileSetRefByID(fileSetRefID)


def getFunctionArgumentDataType(argumentID: str) -> str | None:  # F.7.47.27
    """Return argument dataType.

Args:
    argumentID: Handle to an argument element

Returns:
    dataType of type String - The argument data type

Section: F.7.47.27."""
    arg = _resolve_argument(argumentID)
    return arg.data_type.value


def getFunctionArgumentIDs(functionID: str) -> list[str]:  # F.7.47.28
    """Return function argument handles.

Args:
    functionID: Handle to a function element

Returns:
    argumentIDs of type String - List of handles to argument elements

Section: F.7.47.28."""
    fn = _resolve_function(functionID)
    for child in fn.argument:
        register_parent(child, fn, ("argument",), "list")
    return _ids(fn.argument)


def getFunctionDisabled(functionID: str) -> bool:  # F.7.47.29
    """Return the evaluated disabled value, defaulting to false when absent or unresolved.

    Args:
        functionID: Handle to a function element.

    Returns:
        True when the self-contained disabled expression evaluates to a nonzero value.

    Section: F.7.47.29.
    """
    fn = _resolve_function(functionID)
    return _evaluate_unsigned_bit_expression(fn.disabled.value if fn.disabled is not None else None)


def getFunctionDisabledExpression(functionID: str) -> str | None:  # F.7.47.30
    """Return disabled expression.

Args:
    functionID: Handle to a function element

Returns:
    valueExpression of type String - The disabled expression

Section: F.7.47.30."""
    fn = _resolve_function(functionID)
    return getattr(fn.disabled, "value", None) if fn.disabled is not None else None


def getFunctionDisabledID(functionID: str) -> str | None:  # F.7.47.31
    """Return disabled element handle.

Args:
    functionID: Handle to a function element

Returns:
    DisabledID of type String - Handle to the disabled element

Section: F.7.47.31."""
    fn = _resolve_function(functionID)
    if fn.disabled is None:
        return None
    register_parent(fn.disabled, fn, ("disabled",), "single")
    return get_handle(fn.disabled)


def getFunctionEntryPoint(functionID: str) -> str | None:  # F.7.47.32
    """Return entryPoint.

Args:
    functionID: Handle to a function element

Returns:
    entryPoint of type String - The function entry point

Section: F.7.47.32."""
    return _resolve_function(functionID).entry_point


def getFunctionFileID(functionID: str) -> str | None:  # F.7.47.33
    """Return the handle of the file identified by this function's fileRef.

    Args:
        functionID: Handle to a function element.

    Returns:
        Handle to the matching file in the owning fileSet, or None if unresolved.

    Section: F.7.47.33.
    """
    target = _resolve_function_file(_resolve_function(functionID))
    return get_handle(target) if target is not None else None


def getFunctionFileRefByID(functionID: str) -> str | None:  # F.7.47.34
    """Return the file handle resolved from fileRef within the owning fileSet.

    Args:
        functionID: Handle to a function element.

    Returns:
        Handle to the matching file, or None when fileRef cannot be resolved.

    Section: F.7.47.34.
    """
    return getFunctionFileID(functionID)


def getFunctionFileRefByName(functionID: str) -> str | None:  # F.7.47.35
    """Return the stored fileRef name without resolving its target (F.7.47.35).

Args:
    functionID: Handle to a function element

Returns:
    fileRef of type String - The referenced file

Section: F.7.47.35."""
    return _resolve_function(functionID).file_ref


def getFunctionReplicate(functionID: str) -> bool:  # F.7.47.36
    """Return replicate boolean.

Args:
    functionID: Handle to a function element

Returns:
    replicate of type Boolean - The replicate value

Section: F.7.47.36."""
    return bool(_resolve_function(functionID).replicate)


def getFunctionReturnType(functionID: str) -> str | None:  # F.7.47.37
    """Return returnType literal.

Args:
    functionID: Handle to a function element

Returns:
    returnType of type String - The function return type

Section: F.7.47.37."""
    rt = _resolve_function(functionID).return_type
    if rt is None:
        return None
    return rt.value


def getFunctionSourceFileIDs(functionID: str) -> list[str]:  # F.7.47.38
    """Return sourceFile handles.

Args:
    functionID: Handle to a function element

Returns:
    functionSourceFileIDs of type String - List of handles to sourceFile elements

Section: F.7.47.38."""
    fn = _resolve_function(functionID)
    for child in fn.source_file:
        register_parent(child, fn, ("source_file",), "list")
    return _ids(fn.source_file)


def getFunctionSourceFileName(functionSourceFileID: str) -> str | None:  # F.7.47.39
    """Return sourceFile sourceName.

Args:
    functionSourceFileID: Handle to a functionSourceFile element

Returns:
    name of type String - The SourceFile name

Section: F.7.47.39."""
    sf = _resolve_source_file(functionSourceFileID)
    sn = sf.source_name
    return getattr(sn, "value", None) if sn is not None else None


def getFunctionSourceFileType(functionSourceFileID: str) -> str | None:  # F.7.47.40
    """Return sourceFile fileType literal.

Args:
    functionSourceFileID: Handle to a functionSourceFile element

Returns:
    type of type String - The fileType value

Section: F.7.47.40."""
    sf = _resolve_source_file(functionSourceFileID)
    ft = sf.file_type
    if ft is None:
        return None
    val = getattr(ft, "value", None)
    return getattr(val, "value", None) if val is not None else None


def getSourceFileFileType(sourceFileID: str) -> str | None:  # F.7.47.41
    """Return fileType value.

Args:
    sourceFileID: Handle to a sourceFile element

Returns:
    fileType of type String - The fileType value

Section: F.7.47.41."""
    return getFunctionSourceFileType(sourceFileID)


def getSourceFileFileTypeID(sourceFileID: str) -> str | None:  # F.7.47.42
    """Return the fileType element handle and restore sourceFile ownership.

    Args:
        sourceFileID: Handle to a sourceFile element.

    Returns:
        Handle to the fileType element, or None when absent.

    Section: F.7.47.42.
    """
    sf = _resolve_source_file(sourceFileID)
    if sf.file_type is None:
        return None
    register_parent(sf.file_type, sf, ("file_type",), "single")
    return get_handle(sf.file_type)


def getSourceFileSourceName(sourceFileID: str) -> str | None:  # F.7.47.43
    """Return sourceName value.

Args:
    sourceFileID: Handle to a sourceFile element

Returns:
    sourceName of type String - The sourceName value

Section: F.7.47.43."""
    return getFunctionSourceFileName(sourceFileID)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.48)
# ---------------------------------------------------------------------------

def addFileDefine(fileID: str, name: str, value: str) -> str:  # F.7.48.1
    """Add a define name/value pair to a file.

    Args:
        fileID: Handle to a file element.
        name: Define symbol name.
        value: Define symbol value expression.

    Returns:
        Handle to the new fileDefine element.

    Section: F.7.48.1.
    """
    _require_string(name, "name")
    _require_string(value, "value")
    f = _resolve_file(fileID)
    new = NameValuePairType(name=name, value=Value(value=value))
    f.define.append(new)  # type: ignore[attr-defined]
    register_parent(new, f, ("define",), "list")
    return get_handle(new)


def addFileDependency(fileID: str, dependency: str) -> str:  # F.7.48.2
    """Add a dependency to a file.

    Args:
        fileID: Handle to a file element.
        dependency: Dependency expression.

    Returns:
        Handle to the new dependency element.

    Section: F.7.48.2.
    """
    _require_string(dependency, "dependency")
    f = _resolve_file(fileID)
    dep = Dependency(value=dependency)
    f.dependency.append(dep)  # type: ignore[attr-defined]
    register_parent(dep, f, ("dependency",), "list")
    return get_handle(dep)


def addFileExportedName(fileID: str, value: str) -> str:  # F.7.48.3
    """Add an exported name to a file.

    Args:
        fileID: Handle to a file element.
        value: Exported name.

    Returns:
        Handle to the new exportedName element.

    Section: F.7.48.3.
    """
    _require_string(value, "value")
    from org.accellera.ipxact.v1685_2022.file import File as _File
    f = _resolve_file(fileID)
    en = _File.ExportedName(value=value)
    f.exported_name.append(en)  # type: ignore[attr-defined]
    register_parent(en, f, ("exported_name",), "list")
    return get_handle(en)


def addFileFileType(fileID: str, fileType: str) -> str:  # F.7.48.4
    """Add a file type to a file.

    Args:
        fileID: Handle to a file element.
        fileType: IP-XACT file type enumeration literal.

    Returns:
        Handle to the new fileType element.

    Section: F.7.48.4.
    """
    ft = _enum_file_type(fileType)
    f = _resolve_file(fileID)
    f.file_type.append(ft)  # type: ignore[attr-defined]
    register_parent(ft, f, ("file_type",), "list")
    return get_handle(ft)


def addFileImageType(fileID: str, value: str) -> str:  # F.7.48.5
    """Add an image type to a file.

    Args:
        fileID: Handle to a file element.
        value: Image type name.

    Returns:
        Handle to the new imageType element.

    Section: F.7.48.5.
    """
    _require_string(value, "value")
    from org.accellera.ipxact.v1685_2022.file import File as _File
    f = _resolve_file(fileID)
    it = _File.ImageType(value=value)
    f.image_type.append(it)  # type: ignore[attr-defined]
    register_parent(it, f, ("image_type",), "list")
    return get_handle(it)


def addFileSetDefaultFileBuilder(fileSetID: str, fileType: str) -> str:  # F.7.48.6
    """Add a default builder for the specified file type to a fileSet.

    Args:
        fileSetID: Handle to a fileSet element (the owning schema type).
        fileType: IP-XACT file type enumeration literal.

    Returns:
        Handle to the new defaultFileBuilder element.

    Section: F.7.48.6. Annex F names this parameter fileID, while the
    normative schema places defaultFileBuilder on fileSet.
    """
    ft = _enum_file_type(fileType)
    fs = _resolve_fileset(fileSetID)
    b = FileBuilderType(file_type=ft)
    fs.default_file_builder.append(b)  # type: ignore[attr-defined]
    register_parent(b, fs, ("default_file_builder",), "list")
    return get_handle(b)


def addFileSetDependency(fileSetID: str, dependency: str) -> str:  # F.7.48.7
    """Add a dependency to a fileSet.

    Args:
        fileSetID: Handle to a fileSet element.
        dependency: Dependency expression.

    Returns:
        Handle to the new dependency element.

    Section: F.7.48.7.
    """
    _require_string(dependency, "dependency")
    fs = _resolve_fileset(fileSetID)
    dep = Dependency(value=dependency)
    fs.dependency.append(dep)  # type: ignore[attr-defined]
    register_parent(dep, fs, ("dependency",), "list")
    return get_handle(dep)


def addFileSetFile(fileSetID: str, name: str, fileTypes: list[str]) -> str:  # F.7.48.8
    """Add a file with its required path and file types to a fileSet.

    Args:
        fileSetID: Handle to a fileSet element.
        name: File path or IP-XACT URI expression.
        fileTypes: One or more IP-XACT file type enumeration literals.

    Returns:
        Handle to the new file element.

    Section: F.7.48.8.
    """
    _require_string(name, "name")
    if isinstance(fileTypes, (str, bytes)) or not isinstance(fileTypes, Sequence) or not fileTypes:
        raise TgiError("fileTypes must be a non-empty sequence of strings", TgiFaultCode.INVALID_ARGUMENT)
    ft_list = [_enum_file_type(ft) for ft in fileTypes]
    fs = _resolve_fileset(fileSetID)
    new_file = File(name=IpxactUri(value=name), file_type=ft_list)
    fs.file.append(new_file)  # type: ignore[attr-defined]
    register_parent(new_file, fs, ("file",), "list")
    return get_handle(new_file)


def addFileSetFunction(fileSetID: str, fileRef: str) -> str:  # F.7.48.9
    """Add a function that refers to a file in the fileSet.

    Args:
        fileSetID: Handle to a fileSet element.
        fileRef: The referenced file's fileId value.

    Returns:
        Handle to the new function element.

    Section: F.7.48.9.
    """
    _require_string(fileRef, "fileRef")
    fs = _resolve_fileset(fileSetID)
    fn = FileSetType.Function(file_ref=fileRef)
    fs.function.append(fn)  # type: ignore[attr-defined]
    register_parent(fn, fs, ("function",), "list")
    return get_handle(fn)


def addFileSetGroup(fileSetID: str, group: str) -> str:  # F.7.48.10
    """Add a group label to a fileSet.

    Args:
        fileSetID: Handle to a fileSet element.
        group: Group label.

    Returns:
        Handle to the new group element.

    Section: F.7.48.10.
    """
    _require_string(group, "group")
    fs = _resolve_fileset(fileSetID)
    g = FileSetType.Group(value=group)
    fs.group.append(g)  # type: ignore[attr-defined]
    register_parent(g, fs, ("group",), "list")
    return get_handle(g)


def addFileSetRefGroupFileSetRef(fileSetRefGroupID: str, localName: str) -> str:  # F.7.48.11
    """Add a fileSetRef to a schema fileSetRefGroup.

    Args:
        fileSetRefGroupID: Handle to a fileSetRefGroup element.
        localName: Name of the fileSet in the owning IP-XACT document.

    Returns:
        Handle to the new fileSetRef element.

    Section: F.7.48.11.
    """
    _require_string(localName, "localName")
    group = _resolve_file_set_ref_group(fileSetRefGroupID)
    ref = FileSetRef(local_name=localName)
    group.file_set_ref.append(ref)
    register_parent(ref, group, ("file_set_ref",), "list")
    return get_handle(ref)


def addFunctionArgument(functionID: str, name: str, value: str, dataType: str) -> str:  # F.7.48.12
    """Add an ordered, typed argument to a function.

    Args:
        functionID: Handle to a function element.
        name: Argument name.
        value: Argument value expression.
        dataType: One of the standard C argument data type literals.

    Returns:
        Handle to the new argument element.

    Section: F.7.48.12.
    """
    _require_string(name, "name")
    _require_string(value, "value")
    datatype = _enum_data_type(dataType)
    fn = _resolve_function(functionID)
    arg = FileSetType.Function.Argument(name=name, value=Value(value=value), data_type=datatype)
    fn.argument.append(arg)  # type: ignore[attr-defined]
    register_parent(arg, fn, ("argument",), "list")
    return get_handle(arg)


def addFunctionSourceFile(functionID: str, sourceFileName: str, fileType: str) -> str:  # F.7.48.13
    """Add a typed sourceFile location to a function.

    Args:
        functionID: Handle to a function element.
        sourceFileName: Source file path or IP-XACT URI expression.
        fileType: IP-XACT file type enumeration literal.

    Returns:
        Handle to the new sourceFile element.

    Section: F.7.48.13.
    """
    _require_string(sourceFileName, "sourceFileName")
    file_type = _enum_file_type(fileType)
    fn = _resolve_function(functionID)
    sf = FileSetType.Function.SourceFile(
        source_name=IpxactUri(value=sourceFileName),
        file_type=file_type,
    )
    fn.source_file.append(sf)  # type: ignore[attr-defined]
    register_parent(sf, fn, ("source_file",), "list")
    return get_handle(sf)


def removeFileBuildCommand(fileID: str) -> bool:  # F.7.48.14
    """Remove the buildCommand child from a file.

    Args:
        fileID: Handle to a file element.

    Returns:
        True when a buildCommand was removed; otherwise False.

    Section: F.7.48.14.
    """
    f = _resolve_file(fileID)
    return _remove_optional_child(f, "build_command")


def removeFileDefine(defineID: str) -> bool:  # F.7.48.15
    """Remove a fileDefine element from its file.

    Args:
        defineID: Handle to a fileDefine element.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.15.
    """
    return _remove_owned_list_child(defineID, NameValuePairType, File, "define")


def removeFileDependency(dependencyID: str) -> bool:  # F.7.48.16
    """Remove a dependency from its file.

    Args:
        dependencyID: Handle to a dependency element owned by a file.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.16.
    """
    return _remove_owned_list_child(dependencyID, Dependency, File, "dependency")


def removeFileExportedName(exportedNameID: str) -> bool:  # F.7.48.17
    """Remove an exportedName from its file.

    Args:
        exportedNameID: Handle to an exportedName element.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.17.
    """
    return _remove_owned_list_child(exportedNameID, File.ExportedName, File, "exported_name")


def removeFileFileType(fileTypeID: str) -> bool:  # F.7.48.18
    """Remove a fileType from its file.

    Args:
        fileTypeID: Handle to a fileType element owned by a file.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.18.
    """
    child = resolve_handle(fileTypeID)
    if not isinstance(child, FileType):
        raise TgiError("Invalid fileType handle", TgiFaultCode.INVALID_ID)
    info = get_parent_info(fileTypeID)
    if info is None:
        return False
    owner = resolve_handle(info.parent_handle)
    if info.path != ("file_type",) or not isinstance(owner, File):
        raise TgiError("fileType is not owned by a file", TgiFaultCode.INVALID_ID)
    if len(owner.file_type) <= 1:
        return False
    return detach_child_by_handle(fileTypeID)


def removeFileImageType(imageTypeID: str) -> bool:  # F.7.48.19
    """Remove an imageType from its file.

    Args:
        imageTypeID: Handle to an imageType element.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.19.
    """
    return _remove_owned_list_child(imageTypeID, File.ImageType, File, "image_type")


def removeFileIsIncludeFile(fileID: str) -> bool:  # F.7.48.20
    """Remove a file's isIncludeFile child.

    Args:
        fileID: Handle to a file element.

    Returns:
        True when removed; otherwise False when absent.

    Section: F.7.48.20.
    """
    f = _resolve_file(fileID)
    return _remove_optional_child(f, "is_include_file")


def removeFileIsStructural(fileID: str) -> bool:  # F.7.48.21
    """Remove a file's isStructural value.

    Args:
        fileID: Handle to a file element.

    Returns:
        True when an explicit value was removed; otherwise False.

    Section: F.7.48.21.
    """
    f = _resolve_file(fileID)
    if f.is_structural is None:
        return False
    f.is_structural = None  # type: ignore[assignment]
    return True


def removeFileLogicalName(fileID: str) -> bool:  # F.7.48.22
    """Remove a file's logicalName child.

    Args:
        fileID: Handle to a file element.

    Returns:
        True when removed; otherwise False when absent.

    Section: F.7.48.22.
    """
    f = _resolve_file(fileID)
    return _remove_optional_child(f, "logical_name")


def removeFileSetDefaultFileBuilder(fileBuilderID: str) -> bool:  # F.7.48.23
    """Remove a defaultFileBuilder and invalidate its owned descendants.

    Args:
        fileBuilderID: Handle to a defaultFileBuilder element.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.23.
    """
    return _remove_owned_list_child(fileBuilderID, FileBuilderType, FileSet, "default_file_builder")


def removeFileSetDependency(dependencyID: str) -> bool:  # F.7.48.24
    """Remove a dependency from its fileSet.

    Args:
        dependencyID: Handle to a dependency element owned by a fileSet.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.24.
    """
    return _remove_owned_list_child(dependencyID, Dependency, FileSet, "dependency")


def removeFileSetFile(fileID: str) -> bool:  # F.7.48.25
    """Remove a file from its fileSet.

    Args:
        fileID: Handle to a file element owned by a fileSet.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.25.
    """
    return _remove_owned_list_child(fileID, File, FileSet, "file")


def removeFileSetFunction(functionID: str) -> bool:  # F.7.48.26
    """Remove a function from its fileSet.

    Args:
        functionID: Handle to a function element.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.26.
    """
    return _remove_owned_list_child(functionID, FileSetType.Function, FileSet, "function")


def removeFileSetGroup(groupID: str) -> bool:  # F.7.48.27
    """Remove a group label from its fileSet.

    Args:
        groupID: Handle to a fileSet group element.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.27.
    """
    return _remove_owned_list_child(groupID, FileSetType.Group, FileSet, "group")


def removeFunctionArgument(argumentID: str) -> bool:  # F.7.48.28
    """Remove an argument from its function.

    Args:
        argumentID: Handle to a function argument element.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.28.
    """
    return _remove_owned_list_child(argumentID, FileSetType.Function.Argument, FileSetType.Function, "argument")


def removeFunctionDisabled(functionID: str) -> bool:  # F.7.48.29
    """Remove the disabled element from a function.

    Args:
        functionID: Handle to a function element.

    Returns:
        True when removed; otherwise False when absent.

    Section: F.7.48.29.
    """
    fn = _resolve_function(functionID)
    return _remove_optional_child(fn, "disabled")


def removeFunctionEntryPoint(functionID: str) -> bool:  # F.7.48.30
    """Remove the entryPoint value from a function.

    Args:
        functionID: Handle to a function element.

    Returns:
        True when removed; otherwise False when absent.

    Section: F.7.48.30.
    """
    fn = _resolve_function(functionID)
    if fn.entry_point is None:
        return False
    fn.entry_point = None  # type: ignore[assignment]
    return True


def removeFunctionReturnType(functionID: str) -> bool:  # F.7.48.31
    """Remove the returnType value from a function.

    Args:
        functionID: Handle to a function element.

    Returns:
        True when removed; otherwise False when absent.

    Section: F.7.48.31.
    """
    fn = _resolve_function(functionID)
    if fn.return_type is None:
        return False
    fn.return_type = None  # type: ignore[assignment]
    return True


def removeFunctionSourceFile(functionSourceFileID: str) -> bool:  # F.7.48.32
    """Remove a sourceFile from its function.

    Args:
        functionSourceFileID: Handle to a sourceFile element.

    Returns:
        True when removed; otherwise False if it has no restored owner.

    Section: F.7.48.32.
    """
    return _remove_owned_list_child(
        functionSourceFileID, FileSetType.Function.SourceFile, FileSetType.Function, "source_file"
    )


def setFileIsIncludeFile(fileID: str, value: bool) -> bool:  # F.7.48.33
    """Set the isIncludeFile value on a file.

    Args:
        fileID: Handle to a file element.
        value: Whether the file is an include file.

    Returns:
        True after setting the value.

    Section: F.7.48.33.
    """
    value = _validate_bool(value, "value")
    from org.accellera.ipxact.v1685_2022.file import File as _File

    f = _resolve_file(fileID)
    if f.is_include_file is None:
        f.is_include_file = _File.IsIncludeFile(value=value)  # type: ignore[assignment]
        register_parent(f.is_include_file, f, ("is_include_file",), "single")
    else:
        f.is_include_file.value = value
    return True


def setFileIsStructural(fileID: str, value: bool) -> bool:  # F.7.48.34
    """Set the isStructural value on a file.

    Args:
        fileID: Handle to a file element.
        value: Whether the file is purely structural.

    Returns:
        True after setting the value.

    Section: F.7.48.34.
    """
    value = _validate_bool(value, "value")
    f = _resolve_file(fileID)
    f.is_structural = value  # type: ignore[assignment]
    return True


def setFileLogicalName(fileID: str, logicalName: str) -> bool:  # F.7.48.35
    """Set the logicalName value on a file.

    Args:
        fileID: Handle to a file element.
        logicalName: Logical name, such as a VHDL library name.

    Returns:
        True after setting the value.

    Section: F.7.48.35.
    """
    _require_string(logicalName, "logicalName")
    from org.accellera.ipxact.v1685_2022.file import File as _File

    f = _resolve_file(fileID)
    if f.logical_name is None:
        f.logical_name = _File.LogicalName(value=logicalName)  # type: ignore[assignment]
        register_parent(f.logical_name, f, ("logical_name",), "single")
    else:
        f.logical_name.value = logicalName
    return True


def setFileName(fileID: str, name: str) -> bool:  # F.7.48.36
    """Set the file name URI expression.

    Args:
        fileID: Handle to a file element.
        name: File name or IP-XACT URI expression.

    Returns:
        True after setting the value.

    Section: F.7.48.36.
    """
    _require_string(name, "name")
    f = _resolve_file(fileID)
    f.name.value = name
    return True


def setFunctionArgumentDataType(argumentID: str, dataType: str) -> bool:  # F.7.48.37
    """Set the argument's standard data type.

    Args:
        argumentID: Handle to a function argument element.
        dataType: Standard C argument data type literal.

    Returns:
        True after setting the dataType.

    Section: F.7.48.37.
    """
    datatype = _enum_data_type(dataType)
    arg = _resolve_argument(argumentID)
    arg.data_type = datatype
    return True


def setFunctionDisabled(functionID: str, disabledExpression: str) -> bool:  # F.7.48.38
    """Set the raw disabled unsigned bit expression.

    Args:
        functionID: Handle to a function element.
        disabledExpression: Unsigned bit expression; parameter references are preserved.

    Returns:
        True after setting the expression.

    Section: F.7.48.38.
    """
    _require_string(disabledExpression, "disabledExpression")
    fn = _resolve_function(functionID)
    if fn.disabled is None:
        fn.disabled = UnsignedBitExpression(value=disabledExpression)  # type: ignore[assignment]
        register_parent(fn.disabled, fn, ("disabled",), "single")
    else:
        fn.disabled.value = disabledExpression
    return True


def setFunctionEntryPoint(functionID: str, entryPoint: str) -> bool:  # F.7.48.39
    """Set the entryPoint name on a function.

    Args:
        functionID: Handle to a function element.
        entryPoint: Function entry point name.

    Returns:
        True after setting the value.

    Section: F.7.48.39.
    """
    _require_string(entryPoint, "entryPoint")
    fn = _resolve_function(functionID)
    fn.entry_point = entryPoint  # type: ignore[assignment]
    return True


def setFunctionFileRef(functionID: str, fileRef: str) -> bool:  # F.7.48.40
    """Set the function's fileRef token.

    Args:
        functionID: Handle to a function element.
        fileRef: Referenced file's fileId token.

    Returns:
        True after setting the reference token.

    Section: F.7.48.40.
    """
    _require_string(fileRef, "fileRef")
    fn = _resolve_function(functionID)
    fn.file_ref = fileRef  # type: ignore[assignment]
    return True


def setFunctionReplicate(functionID: str, replicate: bool) -> bool:  # F.7.48.41
    """Set the replicate attribute on a function.

    Args:
        functionID: Handle to a function element.
        replicate: Whether the generator creates a separate object per instance.

    Returns:
        True after setting the attribute.

    Section: F.7.48.41.
    """
    replicate = _validate_bool(replicate, "replicate")
    fn = _resolve_function(functionID)
    fn.replicate = replicate  # type: ignore[assignment]
    return True


def setFunctionReturnType(functionID: str, returnType: str) -> bool:  # F.7.48.42
    """Set the function's return type.

    Args:
        functionID: Handle to a function element.
        returnType: Standard return type literal, ``int`` or ``void``.

    Returns:
        True after setting the return type.

    Section: F.7.48.42.
    """
    if not isinstance(returnType, str):
        raise TgiError("returnType must be a string", TgiFaultCode.INVALID_ARGUMENT)
    fn = _resolve_function(functionID)
    try:
        enum_val = ReturnTypeType(returnType)
    except (ValueError, TypeError) as exc:
        raise TgiError("Unknown returnType", TgiFaultCode.INVALID_ARGUMENT) from exc
    fn.return_type = enum_val
    return True


def setFunctionSourceFileName(functionID: str, value: str) -> bool:  # F.7.48.43
    """Set the first sourceFile name belonging to a function.

    Args:
        functionID: Handle to a function element.
        value: Source file path or IP-XACT URI expression.

    Returns:
        True when a sourceFile exists and was updated; False when the function has none.

    Section: F.7.48.43. A sourceFile requires a fileType in the schema, so
    this operation does not synthesize an incomplete sourceFile.
    """
    _require_string(value, "value")
    fn = _resolve_function(functionID)
    if not fn.source_file:
        return False
    fn.source_file[0].source_name.value = value
    return True


def setSourceFileFileType(sourceFileID: str, value: str) -> bool:  # F.7.48.44
    """Set a sourceFile's fileType enumeration.

    Args:
        sourceFileID: Handle to a sourceFile element.
        value: IP-XACT file type enumeration literal.

    Returns:
        True after setting the value.

    Section: F.7.48.44.
    """
    file_type = _enum_file_type(value)
    sf = _resolve_source_file(sourceFileID)
    sf.file_type.value = file_type.value
    sf.file_type.user = file_type.user
    sf.file_type.libext = file_type.libext
    return True


def setSourceFileSourceName(sourceFileID: str, sourceName: str) -> bool:  # F.7.48.45
    """Set a sourceFile's sourceName URI expression.

    Args:
        sourceFileID: Handle to a sourceFile element.
        sourceName: Source file path or IP-XACT URI expression.

    Returns:
        True after setting the value.

    Section: F.7.48.45.
    """
    _require_string(sourceName, "sourceName")
    sf = _resolve_source_file(sourceFileID)
    sf.source_name.value = sourceName
    return True
