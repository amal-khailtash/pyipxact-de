"""File builder category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.45) and EXTENDED (F.7.46) *File builder* functions.
Only the exact public API defined by Annex F is exported (no legacy helper
aliases). The functions provide access to buildCommand and fileBuilder
structures contained within higher-level elements (e.g., executableImage,
languageTools, fileSet entries). Where an element (command/flags/...) is not
present, getters return ``None`` (or empty lists) consistent with other
categories.

NOTE: The underlying 2022 schema classes are imported from
``org.accellera.ipxact.v1685_2022``. We interact with them via attribute
access and simple container list manipulations. We purposefully keep the
implementation conservative—if an expected container is missing we raise
``INVALID_ID`` for invalid handles; absence of a specific optional child just
returns ``None`` / False.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from org.accellera.ipxact.v1685_2022.executable_image import ExecutableImage
from org.accellera.ipxact.v1685_2022.file_builder_type import FileBuilderType
from org.accellera.ipxact.v1685_2022.linker_command_file import LinkerCommandFile

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    register_parent,
    registry,
    resolve_handle,
)

__all__ = [
    # BASE (F.7.45.x)
    "getBuildCommandCommand",
    "getBuildCommandCommandExpression",
    "getBuildCommandCommandID",
    "getBuildCommandFlags",
    "getBuildCommandFlagsExpression",
    "getBuildCommandFlagsID",
    "getBuildCommandReplaceDefaultFlags",
    "getBuildCommandReplaceDefaultFlagsID",
    "getBuildCommandTargetName",
    "getBuildCommandTargetNameExpression",
    "getExecutableImageFileBuilderIDs",
    "getExecutableImageFileSetRefIDs",
    "getExecutableImageLanguageToolsID",
    "getExecutableImageLinker",
    "getExecutableImageLinkerCommandFileID",
    "getExecutableImageLinkerExpression",
    "getExecutableImageLinkerFlags",
    "getExecutableImageLinkerFlagsExpression",
    "getFileBuildCommandID",
    "getFileBuilderCommand",
    "getFileBuilderCommandExpression",
    "getFileBuilderCommandID",
    "getFileBuilderFileType",
    "getFileBuilderFileTypeID",
    "getFileBuilderFlags",
    "getFileBuilderFlagsExpression",
    "getFileBuilderFlagsID",
    "getFileBuilderReplaceDefaultFlags",
    "getFileBuilderReplaceDefaultFlagsExpression",
    "getFileBuilderReplaceDefaultFlagsID",
    "getGeneratorRefByID",
    "getLanguageToolsFileBuilderIDs",
    "getLanguageToolsLinker",
    "getLanguageToolsLinkerCommandFileID",
    "getLanguageToolsLinkerExpression",
    "getLanguageToolsLinkerFlags",
    "getLanguageToolsLinkerFlagsExpression",
    "getLanguageToolsLinkerFlagsID",
    "getLanguageToolsLinkerID",
    "getLinkerCommandFileCommandLineSwitch",
    "getLinkerCommandFileCommandLineSwitchExpression",
    "getLinkerCommandFileCommandLineSwitchID",
    "getLinkerCommandFileEnable",
    "getLinkerCommandFileEnableExpression",
    "getLinkerCommandFileEnableID",
    "getLinkerCommandFileGeneratorRefByID",
    "getLinkerCommandFileGeneratorRefByNames",
    "getLinkerCommandFileGeneratorRefIDs",
    "getLinkerCommandFileLineSwitch",
    "getLinkerCommandFileLineSwitchExpression",
    "getLinkerCommandFileName",
    "getLinkerCommandFileNameExpression",
    "getLinkerCommandFileNameID",
    "getLinkerCommandFileNameValue",
    # EXTENDED (F.7.46.x)
    "addExecutableImageFileBuilderID",
    "addExecutableImageLinkerCommandFile",
    "addLanguageToolsFileBuilder",
    "addLinkerCommandFileGeneratorRef",
    "removeBuildCommandCommand",
    "removeBuildCommandFlags",
    "removeBuildCommandReplaceDefaultFlags",
    "removeBuildCommandTargetName",
    "removeDefaultFileBuilderCommand",
    "removeExecutableImageFileBuilderID",
    "removeExecutableImageLanguageTools",
    "removeExecutableImageLinkerCommandFile",
    "removeFileBuilderCommand",
    "removeFileBuilderFlags",
    "removeFileBuilderReplaceDefaultFlags",
    "removeLanguageToolsFileBuilder",
    "removeLanguageToolsLinkerCommandFile",
    "removeLanguageToolsLinkerFlags",
    "removeLinkerCommandFileGeneratorRef",
    "setBuildCommandCommand",
    "setBuildCommandFlags",
    "setBuildCommandReplaceDefaultFlags",
    "setBuildCommandTargetName",
    "setExecutableImageLanguageTools",
    "setExecutableImageLinker",
    "setExecutableImageLinkerFlags",
    "setFileBuildCommand",
    "setFileBuilderCommand",
    "setFileBuilderFileType",
    "setFileBuilderFlags",
    "setFileBuilderReplaceDefaultFlags",
    "setLanguageToolsLinker",
    "setLanguageToolsLinkerCommandFile",
    "setLanguageToolsLinkerFlags",
    "setLinkerCommandFileCommandLineSwitch",
    "setLinkerCommandFileEnable",
    "setLinkerCommandFileName",
]


def _require_file_builder(handle: str):
    """Require either generated fileBuilder type used in the standard model."""
    obj = _resolve(handle)
    if not isinstance(obj, FileBuilderType | ExecutableImage.LanguageTools.FileBuilder):
        raise TgiError("Handle is not FileBuilder", TgiFaultCode.INVALID_ID)
    return obj


def _require_default_file_builder(handle: str) -> FileBuilderType:
    """Resolve only a fileSet/component defaultFileBuilder model object."""
    obj = _resolve(handle)
    if not isinstance(obj, FileBuilderType):
        raise TgiError("Handle is not a defaultFileBuilder", TgiFaultCode.INVALID_ID)
    return obj


def _require_executable_file_builder(handle: str) -> ExecutableImage.LanguageTools.FileBuilder:
    """Resolve only an executableImage.languageTools.fileBuilder element."""
    obj = _resolve(handle)
    if not isinstance(obj, ExecutableImage.LanguageTools.FileBuilder):
        raise TgiError("Handle is not an executable fileBuilder", TgiFaultCode.INVALID_ID)
    return obj


def _set_builder_expression(handle: str, field: str, value: str) -> bool:
    """Update generated expression source without replacing metadata or identity."""
    from org.accellera.ipxact.v1685_2022 import StringExpression, UnsignedBitExpression

    fb = _require_file_builder(handle)
    if not isinstance(value, str):
        raise TgiError("Expected expression source text", TgiFaultCode.INVALID_ARGUMENT)
    child = getattr(fb, field)
    if child is None:
        cls = UnsignedBitExpression if field == "replace_default_flags" else StringExpression
        child = cls(value=value)
        setattr(fb, field, child)
    else:
        child.value = value
    register_parent(child, fb, (field,), "single")
    return True


def _remove_builder_expression(handle: str, field: str) -> bool:
    """Detach an optional generated expression and invalidate its descendants."""
    fb = _require_file_builder(handle)
    child = getattr(fb, field)
    if child is None:
        return False
    register_parent(child, fb, (field,), "single")
    return detach_child_by_handle(get_handle(child))


def _resolve(handle: str) -> Any:
    obj = resolve_handle(handle)
    if obj is None:
        raise TgiError("Invalid handle", TgiFaultCode.INVALID_ID)
    return obj


def _get_value(node: Any) -> Any:
    if node is None:
        return None
    v = getattr(node, "value", node)
    return getattr(v, "value", v)


def _require_language_tools(handle: str) -> ExecutableImage.LanguageTools:
    """Resolve a languageTools handle and reject unrelated model objects."""
    obj = _resolve(handle)
    if not isinstance(obj, ExecutableImage.LanguageTools):
        raise TgiError("Handle is not LanguageTools", TgiFaultCode.INVALID_ID)
    return obj


def _require_linker_command_file(handle: str) -> LinkerCommandFile:
    """Resolve a linkerCommandFile handle with strict generated-type checking."""
    obj = _resolve(handle)
    if not isinstance(obj, LinkerCommandFile):
        raise TgiError("Handle is not LinkerCommandFile", TgiFaultCode.INVALID_ID)
    return obj


def _require_generator_ref(handle: str) -> Any:
    """Resolve a generatorRef handle without confusing it with its target."""
    from org.accellera.ipxact.v1685_2022.generator_ref import GeneratorRef

    obj = _resolve(handle)
    if not isinstance(obj, GeneratorRef):
        raise TgiError("Handle is not generatorRef", TgiFaultCode.INVALID_ID)
    return obj


def _set_text_child(owner: Any, field: str, value: str, cls: type, path: tuple[str, ...]) -> Any:
    """Validate and set a generated text node while preserving child identity."""
    if not isinstance(value, str):
        raise TgiError("Expected string source text", TgiFaultCode.INVALID_ARGUMENT)
    child = getattr(owner, field)
    if child is None:
        child = cls(value=value)
        setattr(owner, field, child)
    else:
        child.value = value
    register_parent(child, owner, path, "single")
    return child


def _set_linker_choice(lt: ExecutableImage.LanguageTools, child: Any, cls: type) -> Any:
    """Insert or update one linker choice, preserving XSD order and identity."""
    from org.accellera.ipxact.v1685_2022 import StringExpression

    choices = list(lt.linker_flags_or_linker_command_file)
    current = next((item for item in choices if isinstance(item, cls)), None)
    if current is None and len(choices) >= 2:
        raise TgiError("languageTools linker choice exceeds schema cardinality", TgiFaultCode.INVALID_ARGUMENT)
    if current is not None:
        if isinstance(current, StringExpression) and isinstance(child, StringExpression):
            current.value = child.value
            current.other_attributes.update(child.other_attributes)
            selected = current
        else:
            selected = child
            choices[choices.index(current)] = selected
            register_parent(selected, lt, ("linker_flags_or_linker_command_file",), "list")
            old_id = get_handle(current)
            detach_child_by_handle(old_id)
            choices = list(lt.linker_flags_or_linker_command_file)
    else:
        selected = child
        choices.append(selected)
        register_parent(selected, lt, ("linker_flags_or_linker_command_file",), "list")
    # XML sequence requires linkerFlags before linkerCommandFile.
    choices.sort(key=lambda item: 0 if isinstance(item, StringExpression) else 1)
    if len(choices) > 2 or sum(isinstance(item, StringExpression) for item in choices) > 1:
        raise TgiError("languageTools linker choice exceeds schema cardinality", TgiFaultCode.INVALID_ARGUMENT)
    lt.linker_flags_or_linker_command_file = choices
    return selected


def _linker_choices(lt: ExecutableImage.LanguageTools) -> tuple[Any | None, LinkerCommandFile | None]:
    from org.accellera.ipxact.v1685_2022 import StringExpression

    flags = None
    command_file = None
    for child in lt.linker_flags_or_linker_command_file:
        if isinstance(child, StringExpression):
            flags = child
            register_parent(child, lt, ("linker_flags_or_linker_command_file",), "list")
        elif isinstance(child, LinkerCommandFile):
            command_file = child
            register_parent(child, lt, ("linker_flags_or_linker_command_file",), "list")
    return flags, command_file


def _boolean_value(node: Any) -> bool | None:
    """Evaluate a self-contained SystemVerilog boolean expression with slang."""
    if node is None:
        return None
    from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser

    try:
        return bool(SvExpressionParser().evaluate(str(node.value)))
    except SvExpressionError:
        return None


def _set_lcf_expression(lcf: LinkerCommandFile, field: str, value: str, cls: type) -> Any:
    return _set_text_child(lcf, field, value, cls, (field,))


def _iter_component_tree(root: Any, seen: set[int] | None = None):
    """Yield dataclass nodes with their owner field/list location."""
    seen = set() if seen is None else seen
    if id(root) in seen:
        return
    seen.add(id(root))
    if not is_dataclass(root) or isinstance(root, type):
        return
    for field_info in fields(root):
        value = getattr(root, field_info.name)
        if is_dataclass(value) and not isinstance(value, type):
            yield value, root, (field_info.name,), "single"
            yield from _iter_component_tree(value, seen)
        elif isinstance(value, (list, tuple)):
            for child in value:
                if is_dataclass(child) and not isinstance(child, type):
                    yield child, root, (field_info.name,), "list"
                    yield from _iter_component_tree(child, seen)


def _resolve_generator_name(name: str, context: Any) -> Any | None:
    """Resolve a component generator name within its owning component only."""
    from org.accellera.ipxact.v1685_2022.component import Component
    from org.accellera.ipxact.v1685_2022.component_generator import ComponentGenerator

    matches: list[Any] = []
    for root_handle in registry.iter_by_predicate(lambda root: isinstance(root, Component)):
        root = resolve_handle(root_handle)
        owner_found = False
        target = None
        for candidate, parent, path, container in _iter_component_tree(root):
            if candidate is context:
                owner_found = True
            if isinstance(candidate, ComponentGenerator) and candidate.name == name:
                target = (candidate, parent, path, container)
        if owner_found and target is not None:
            matches.append(target)
    # Ambiguous ownership is an invalid tree; do not guess across components.
    if len(matches) != 1:
        return None
    candidate, parent, path, container = matches[0]
    register_parent(candidate, parent, path, container)
    return candidate


def _component_context(node: Any) -> Any | None:
    """Find the registered component that owns a nested IP-XACT node."""
    from org.accellera.ipxact.v1685_2022.component import Component

    matches = []
    for root_handle in registry.iter_by_predicate(lambda root: isinstance(root, Component)):
        root = resolve_handle(root_handle)
        if any(candidate is node for candidate, _, _, _ in _iter_component_tree(root)):
            matches.append(root)
    return matches[0] if len(matches) == 1 else None


def _register_owner_from_roots(child: Any) -> bool:
    """Restore a direct owner link when an operation starts from a nested ID."""
    for root_handle in registry.iter_by_predicate(lambda root: True):
        root = resolve_handle(root_handle)
        for candidate, parent, path, container in _iter_component_tree(root):
            if candidate is child:
                register_parent(child, parent, path, container)
                return True
    return False


def _set_lcf_boolean(lcf: LinkerCommandFile, field: str, value: str) -> Any:
    from org.accellera.ipxact.v1685_2022 import UnsignedBitExpression

    return _set_lcf_expression(lcf, field, value, UnsignedBitExpression)


def _new_linker_command_file(name: str, switch: str, enable: bool | str) -> LinkerCommandFile:
    from org.accellera.ipxact.v1685_2022 import StringExpression, UnsignedBitExpression

    if not isinstance(name, str) or not isinstance(switch, str):
        raise TgiError("Linker command file name and switch must be strings", TgiFaultCode.INVALID_ARGUMENT)
    if isinstance(enable, bool):
        enabled_source = "1" if enable else "0"
    elif isinstance(enable, str):
        enabled_source = enable
    else:
        raise TgiError(
            "Linker command file enable must be a boolean or expression string", TgiFaultCode.INVALID_ARGUMENT
        )
    return LinkerCommandFile(
        name=StringExpression(value=name),
        command_line_switch=StringExpression(value=switch),
        enable=UnsignedBitExpression(value=enabled_source),
    )


def _remove_nested(child: Any) -> bool:
    """Remove a child after recovering parsed-tree ownership where possible."""
    child_id = get_handle(child)
    if not detach_child_by_handle(child_id):
        _register_owner_from_roots(child)
        return detach_child_by_handle(child_id)
    return True


# ---------------------------------------------------------------------------
# BASE (F.7.45)
# ---------------------------------------------------------------------------


def _resolve_build_command(handle: str) -> Any:
    """Resolve a standard buildCommand handle or a legacy containing-file handle."""
    from org.accellera.ipxact.v1685_2022 import File

    obj = _resolve(handle)
    if isinstance(obj, File.BuildCommand):
        return obj
    if not isinstance(obj, File):
        raise TgiError("Expected a file or buildCommand handle", TgiFaultCode.INVALID_ID)
    if obj.build_command is not None:
        register_parent(obj.build_command, obj, ("build_command",), "single")
    return obj.build_command


def _set_build_expression(handle: str, field: str, value: str) -> bool:
    """Set generated source text with atomic validation and stable child identity."""
    from org.accellera.ipxact.v1685_2022 import File, IpxactUri, StringExpression, UnsignedBitExpression

    bc = _resolve_build_command(handle)
    if not isinstance(value, str):
        raise TgiError("Expected expression source string", TgiFaultCode.INVALID_ARGUMENT)
    if bc is None:
        owner = _resolve(handle)
        bc = File.BuildCommand()
        owner.build_command = bc
        register_parent(bc, owner, ("build_command",), "single")
    child = getattr(bc, field)
    if child is None:
        cls = {
            "flags": File.BuildCommand.Flags,
            "target_name": IpxactUri,
            "replace_default_flags": UnsignedBitExpression,
        }.get(field, StringExpression)
        child = cls(value=value)
        setattr(bc, field, child)
    else:
        child.value = value
    register_parent(child, bc, (field,), "single")
    return True


def _remove_build_expression(handle: str, field: str) -> bool:
    """Remove a generated source field and invalidate the child handle."""
    bc = _resolve_build_command(handle)
    child = None if bc is None else getattr(bc, field)
    if child is None:
        return False
    register_parent(child, bc, (field,), "single")
    return detach_child_by_handle(get_handle(child))


def getBuildCommandCommand(buildCommandID: str) -> str | None:  # F.7.45.1
    """Return textual build command value.

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.1.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.command is None:
        return None
    return _get_value(bc.command)


def getBuildCommandCommandExpression(buildCommandID: str) -> str | None:  # F.7.45.2
    """Return expression (if any) for build command.

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.2.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.command is None:
        return None
    return getattr(bc.command, "value", None)


def getBuildCommandCommandID(buildCommandID: str) -> str | None:  # F.7.45.3
    """Return handle of build command value element.

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.3.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.command is None:
        return None
    register_parent(bc.command, bc, ("command",), "single")
    return get_handle(bc.command)


def getBuildCommandFlags(buildCommandID: str) -> str | None:  # F.7.45.4
    """Return textual flags value.

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.4.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.flags is None:
        return None
    return _get_value(bc.flags)


def getBuildCommandFlagsExpression(buildCommandID: str) -> str | None:  # F.7.45.5
    """Return expression (if any) for flags.

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.5.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.flags is None:
        return None
    return getattr(bc.flags, "value", None)


def getBuildCommandFlagsID(buildCommandID: str) -> str | None:  # F.7.45.6
    """Return handle of flags element.

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.6.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.flags is None:
        return None
    register_parent(bc.flags, bc, ("flags",), "single")
    return get_handle(bc.flags)


def getBuildCommandReplaceDefaultFlags(buildCommandID: str) -> bool | None:  # F.7.45.7
    """Return boolean value of replaceDefaultFlags (converted to bool).

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.7.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.replace_default_flags is None:
        return None
    return _boolean_value(bc.replace_default_flags)


def getBuildCommandReplaceDefaultFlagsID(buildCommandID: str) -> str | None:  # F.7.45.8
    """Return handle of replaceDefaultFlags element.

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.8.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.replace_default_flags is None:
        return None
    register_parent(bc.replace_default_flags, bc, ("replace_default_flags",), "single")
    return get_handle(bc.replace_default_flags)


def getBuildCommandTargetName(buildCommandID: str) -> str | None:  # F.7.45.9
    """Return targetName value (derived file path).

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.9.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.target_name is None:
        return None
    return _get_value(bc.target_name)


def getBuildCommandTargetNameExpression(buildCommandID: str) -> str | None:  # F.7.45.10
    """Return expression for targetName.

    Args:
        buildCommandID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.10.
    """
    bc = _resolve_build_command(buildCommandID)
    if bc is None or bc.target_name is None:
        return None
    return getattr(bc.target_name, "value", None)


def getExecutableImageFileBuilderIDs(executableImageID: str) -> list[str]:  # F.7.45.11
    """Return handles of all fileBuilder children of languageTools.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        Ordered list of child handles.

    Section: F.7.45.11.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None:
        return []
    register_parent(img.language_tools, img, ("language_tools",), "single")
    for fb in img.language_tools.file_builder:
        register_parent(fb, img.language_tools, ("file_builder",), "list")
    return [get_handle(fb) for fb in img.language_tools.file_builder]


def getExecutableImageFileSetRefIDs(executableImageID: str) -> list[str]:  # F.7.45.12
    """Return handles of all fileSetRef children.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        Ordered list of child handles.

    Section: F.7.45.12.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.file_set_ref_group is None:
        return []
    register_parent(img.file_set_ref_group, img, ("file_set_ref_group",), "single")
    for ref in img.file_set_ref_group.file_set_ref:
        register_parent(ref, img.file_set_ref_group, ("file_set_ref",), "list")
    return [get_handle(r) for r in img.file_set_ref_group.file_set_ref]


def getExecutableImageLanguageToolsID(executableImageID: str) -> str | None:  # F.7.45.13
    """Return handle of languageTools or None.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.13.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None:
        return None
    register_parent(img.language_tools, img, ("language_tools",), "single")
    return get_handle(img.language_tools)


def getExecutableImageLinker(executableImageID: str) -> str | None:  # F.7.45.14
    """Return linker command text.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.14.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None or img.language_tools.linker is None:
        return None
    register_parent(img.language_tools, img, ("language_tools",), "single")
    register_parent(img.language_tools.linker, img.language_tools, ("linker",), "single")
    return _get_value(img.language_tools.linker)


def getExecutableImageLinkerCommandFileID(executableImageID: str) -> str | None:  # F.7.45.15
    """Return handle of first linkerCommandFile (if any).

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.15.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None:
        return None
    # Spec returns first? F.7.45.15 singular; choose first if present
    register_parent(img.language_tools, img, ("language_tools",), "single")
    _, lcf = _linker_choices(img.language_tools)
    return None if lcf is None else get_handle(lcf)


def getExecutableImageLinkerExpression(executableImageID: str) -> str | None:  # F.7.45.16
    """Return expression for linker element.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.16.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None or img.language_tools.linker is None:
        return None
    register_parent(img.language_tools, img, ("language_tools",), "single")
    register_parent(img.language_tools.linker, img.language_tools, ("linker",), "single")
    return getattr(img.language_tools.linker, "value", None)


def getExecutableImageLinkerFlags(executableImageID: str) -> str | None:  # F.7.45.17
    """Return textual linker flags.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.17.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None:
        return None
    flags, _ = _linker_choices(img.language_tools)
    return None if flags is None else flags.value


def getExecutableImageLinkerFlagsExpression(executableImageID: str) -> str | None:  # F.7.45.18
    """Return expression for linker flags.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.18.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None:
        return None
    flags, _ = _linker_choices(img.language_tools)
    return None if flags is None else flags.value


def getFileBuildCommandID(fileID: str) -> str | None:  # F.7.45.19
    """Return handle of buildCommand element for a File.

    Args:
        fileID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.19.
    """
    from org.accellera.ipxact.v1685_2022 import File

    owner = _resolve(fileID)
    if not isinstance(owner, File):
        raise TgiError("Expected a file handle", TgiFaultCode.INVALID_ID)
    bc = _resolve_build_command(fileID)
    return None if bc is None else get_handle(bc)


def getFileBuilderCommand(fileBuilderID: str) -> str | None:  # F.7.45.20
    """Return command text of a fileBuilder.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.20.
    """
    fb = _require_file_builder(fileBuilderID)
    if fb.command is None:
        return None
    register_parent(fb.command, fb, ("command",), "single")
    return fb.command.value


def getFileBuilderCommandExpression(fileBuilderID: str) -> str | None:  # F.7.45.21
    """Return the command source expression on a fileBuilder.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.21.
    """
    fb = _require_file_builder(fileBuilderID)
    if fb.command is None:
        return None
    register_parent(fb.command, fb, ("command",), "single")
    return fb.command.value


def getFileBuilderCommandID(fileBuilderID: str) -> str | None:  # F.7.45.22
    """Return the command child handle on a fileBuilder.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.22.
    """
    fb = _require_file_builder(fileBuilderID)
    if fb.command is None:
        return None
    register_parent(fb.command, fb, ("command",), "single")
    return get_handle(fb.command)


def getFileBuilderFileType(fileBuilderID: str) -> str:  # F.7.45.23
    """Return the standard fileType enumeration value.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.23.
    """
    fb = _require_file_builder(fileBuilderID)
    register_parent(fb.file_type, fb, ("file_type",), "single")
    value = getattr(fb.file_type.value, "value", fb.file_type.value)
    return str(value)


def getFileBuilderFileTypeID(fileBuilderID: str) -> str:  # F.7.45.24
    """Return the fileType child handle on a fileBuilder.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.24.
    """
    fb = _require_file_builder(fileBuilderID)
    register_parent(fb.file_type, fb, ("file_type",), "single")
    return get_handle(fb.file_type)


def getFileBuilderFlags(fileBuilderID: str) -> str | None:  # F.7.45.25
    """Return fileBuilder flags text.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.25.
    """
    fb = _require_file_builder(fileBuilderID)
    if fb.flags is None:
        return None
    register_parent(fb.flags, fb, ("flags",), "single")
    return fb.flags.value


def getFileBuilderFlagsExpression(fileBuilderID: str) -> str | None:  # F.7.45.26
    """Return fileBuilder flags source expression.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.26.
    """
    return getFileBuilderFlags(fileBuilderID)


def getFileBuilderFlagsID(fileBuilderID: str) -> str | None:  # F.7.45.27
    """Return the fileBuilder flags child handle.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.27.
    """
    fb = _require_file_builder(fileBuilderID)
    if fb.flags is None:
        return None
    register_parent(fb.flags, fb, ("flags",), "single")
    return get_handle(fb.flags)


def getFileBuilderReplaceDefaultFlags(fileBuilderID: str) -> bool | None:  # F.7.45.28
    """Return the evaluated replaceDefaultFlags value.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.28.
    """
    fb = _require_file_builder(fileBuilderID)
    if fb.replace_default_flags is None:
        return None
    register_parent(fb.replace_default_flags, fb, ("replace_default_flags",), "single")
    return _boolean_value(fb.replace_default_flags)


def getFileBuilderReplaceDefaultFlagsExpression(fileBuilderID: str) -> str | None:  # F.7.45.29
    """Return the replaceDefaultFlags source expression.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.29.
    """
    fb = _require_file_builder(fileBuilderID)
    if fb.replace_default_flags is None:
        return None
    register_parent(fb.replace_default_flags, fb, ("replace_default_flags",), "single")
    return fb.replace_default_flags.value


def getFileBuilderReplaceDefaultFlagsID(fileBuilderID: str) -> str | None:  # F.7.45.30
    """Return the replaceDefaultFlags child handle.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.30.
    """
    fb = _require_file_builder(fileBuilderID)
    if fb.replace_default_flags is None:
        return None
    register_parent(fb.replace_default_flags, fb, ("replace_default_flags",), "single")
    return get_handle(fb.replace_default_flags)


def getGeneratorRefByID(generatorRefID: str) -> str | None:  # F.7.45.31
    """Resolve a generatorRef name to the matching component generator handle.

    Args:
        generatorRefID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.31.
    """
    ref = _require_generator_ref(generatorRefID)
    target = _resolve_generator_name(ref.value, ref)
    return None if target is None else get_handle(target)


def getLanguageToolsFileBuilderIDs(languageToolsID: str) -> list[str]:  # F.7.45.32
    """Return handles to all fileBuilder children of languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        Ordered list of child handles.

    Section: F.7.45.32.
    """
    lt = _require_language_tools(languageToolsID)
    for builder in lt.file_builder:
        register_parent(builder, lt, ("file_builder",), "list")
    return [get_handle(builder) for builder in lt.file_builder]


def getLanguageToolsLinker(languageToolsID: str) -> str | None:  # F.7.45.33
    """Return linker text from languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.33.
    """
    lt = _require_language_tools(languageToolsID)
    if lt.linker is None:
        return None
    register_parent(lt.linker, lt, ("linker",), "single")
    return lt.linker.value


def getLanguageToolsLinkerCommandFileID(languageToolsID: str) -> str | None:  # F.7.45.34
    """Return the linkerCommandFile child handle from languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.34.
    """
    _, command_file = _linker_choices(_require_language_tools(languageToolsID))
    return None if command_file is None else get_handle(command_file)


def getLanguageToolsLinkerExpression(languageToolsID: str) -> str | None:  # F.7.45.35
    """Return linker source expression from languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.35.
    """
    return getLanguageToolsLinker(languageToolsID)


def getLanguageToolsLinkerFlags(languageToolsID: str) -> str | None:  # F.7.45.36
    """Return linkerFlags text from languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.36.
    """
    flags, _ = _linker_choices(_require_language_tools(languageToolsID))
    return None if flags is None else flags.value


def getLanguageToolsLinkerFlagsExpression(languageToolsID: str) -> str | None:  # F.7.45.37
    """Return linkerFlags source expression from languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.37.
    """
    return getLanguageToolsLinkerFlags(languageToolsID)


def getLanguageToolsLinkerFlagsID(languageToolsID: str) -> str | None:  # F.7.45.38
    """Return the linkerFlags child handle from languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.38.
    """
    flags, _ = _linker_choices(_require_language_tools(languageToolsID))
    return None if flags is None else get_handle(flags)


def getLanguageToolsLinkerID(languageToolsID: str) -> str | None:  # F.7.45.39
    """Return the linker child handle from languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.39.
    """
    lt = _require_language_tools(languageToolsID)
    if lt.linker is None:
        return None
    register_parent(lt.linker, lt, ("linker",), "single")
    return get_handle(lt.linker)


def getLinkerCommandFileCommandLineSwitch(linkerCommandFileID: str) -> str | None:  # F.7.45.40
    """Return commandLineSwitch text from a linkerCommandFile.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.40.
    """
    child = _require_linker_command_file(linkerCommandFileID).command_line_switch
    return None if child is None else child.value


def getLinkerCommandFileCommandLineSwitchExpression(linkerCommandFileID: str) -> str | None:  # F.7.45.41
    """Return commandLineSwitch source expression.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.41.
    """
    return getLinkerCommandFileCommandLineSwitch(linkerCommandFileID)


def getLinkerCommandFileCommandLineSwitchID(linkerCommandFileID: str) -> str | None:  # F.7.45.42
    """Return commandLineSwitch child handle.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.42.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    if lcf.command_line_switch is None:
        return None
    register_parent(lcf.command_line_switch, lcf, ("command_line_switch",), "single")
    return get_handle(lcf.command_line_switch)


def getLinkerCommandFileEnable(linkerCommandFileID: str) -> bool | None:  # F.7.45.43
    """Evaluate and return the enable expression.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.43.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    if lcf.enable is not None:
        register_parent(lcf.enable, lcf, ("enable",), "single")
    return _boolean_value(lcf.enable)


def getLinkerCommandFileEnableExpression(linkerCommandFileID: str) -> str | None:  # F.7.45.44
    """Return the enable source expression.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.44.
    """
    child = _require_linker_command_file(linkerCommandFileID).enable
    return None if child is None else child.value


def getLinkerCommandFileEnableID(linkerCommandFileID: str) -> str | None:  # F.7.45.45
    """Return enable child handle.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.45.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    if lcf.enable is None:
        return None
    register_parent(lcf.enable, lcf, ("enable",), "single")
    return get_handle(lcf.enable)


def getLinkerCommandFileGeneratorRefByID(linkerCommandFileID: str, generatorRef: str) -> str | None:  # F.7.45.46
    """Resolve one generatorRef by its component generator name.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.
        generatorRef: Value or expression source for this operation.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.46.
    """
    _require_linker_command_file(linkerCommandFileID)
    if not isinstance(generatorRef, str):
        raise TgiError("Expected generator name", TgiFaultCode.INVALID_ARGUMENT)
    lcf = _require_linker_command_file(linkerCommandFileID)
    target = _resolve_generator_name(generatorRef, lcf)
    return None if target is None else get_handle(target)


def getLinkerCommandFileGeneratorRefByNames(linkerCommandFileID: str) -> list[str]:  # F.7.45.47
    """Return the generator names referenced by a linkerCommandFile.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Ordered list of referenced names.

    Section: F.7.45.47.
    """
    return [ref.value for ref in _require_linker_command_file(linkerCommandFileID).generator_ref]


def getLinkerCommandFileGeneratorRefIDs(linkerCommandFileID: str) -> list[str]:  # F.7.45.48
    """Return generatorRef element handles in document order.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Ordered list of child handles.

    Section: F.7.45.48.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    for ref in lcf.generator_ref:
        register_parent(ref, lcf, ("generator_ref",), "list")
    return [get_handle(ref) for ref in lcf.generator_ref]


def getLinkerCommandFileLineSwitch(linkerCommandFileID: str) -> str | None:  # F.7.45.49
    """Return command line switch value using the Annex F alias name.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.49.
    """
    return getLinkerCommandFileCommandLineSwitch(linkerCommandFileID)


def getLinkerCommandFileLineSwitchExpression(linkerCommandFileID: str) -> str | None:  # F.7.45.50
    """Return command line switch expression using the Annex F alias name.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.50.
    """
    return getLinkerCommandFileCommandLineSwitchExpression(linkerCommandFileID)


def getLinkerCommandFileName(linkerCommandFileID: str) -> str | None:  # F.7.45.51
    """Return the linker command file name expression value.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.51.
    """
    child = _require_linker_command_file(linkerCommandFileID).name
    return None if child is None else child.value


def getLinkerCommandFileNameExpression(linkerCommandFileID: str) -> str | None:  # F.7.45.52
    """Return the linker command file name source expression.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.52.
    """
    return getLinkerCommandFileName(linkerCommandFileID)


def getLinkerCommandFileNameID(linkerCommandFileID: str) -> str | None:  # F.7.45.53
    """Return the name child handle.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Child handle, or None when the child is absent.

    Section: F.7.45.53.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    if lcf.name is None:
        return None
    register_parent(lcf.name, lcf, ("name",), "single")
    return get_handle(lcf.name)


def getLinkerCommandFileNameValue(linkerCommandFileID: str) -> str | None:  # F.7.45.54
    """Return linkerCommandFile name value (same generated text as expression).

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        Stored value or expression, or None when the optional child is absent.

    Section: F.7.45.54.
    """
    return getLinkerCommandFileName(linkerCommandFileID)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.46)
# ---------------------------------------------------------------------------


def addExecutableImageFileBuilderID(executableImageID: str, fileType: str, command: str) -> str:  # F.7.46.1
    """Create a new fileBuilder under executableImage.languageTools.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.
        fileType: Value or expression source for this operation.
        command: Value or expression source for this operation.

    Returns:
        Handle to the newly created child.

    Section: F.7.46.1.
    """
    from org.accellera.ipxact.v1685_2022 import FileType, SimpleFileType, StringExpression

    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    if not isinstance(fileType, str) or not isinstance(command, str):
        raise TgiError("fileType and command must be strings", TgiFaultCode.INVALID_ARGUMENT)
    try:
        file_type = SimpleFileType(fileType)
    except ValueError as exc:
        raise TgiError("Expected a standard file type value", TgiFaultCode.INVALID_ARGUMENT) from exc
    if img.language_tools is None:
        img.language_tools = ExecutableImage.LanguageTools()
    register_parent(img.language_tools, img, ("language_tools",), "single")
    fb = ExecutableImage.LanguageTools.FileBuilder(
        file_type=FileType(value=file_type), command=StringExpression(value=command)
    )
    img.language_tools.file_builder.append(fb)
    register_parent(fb, img.language_tools, ("file_builder",), "list")
    register_parent(fb.file_type, fb, ("file_type",), "single")
    register_parent(fb.command, fb, ("command",), "single")
    return get_handle(fb)


def addExecutableImageLinkerCommandFile(
    executableImageID: str, name: str, commandLineSwitch: str, enable: bool
) -> str:  # F.7.46.2
    """Append a new linkerCommandFile (optionally setting enable flag).

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.
        name: Value or expression source for this operation.
        commandLineSwitch: Value or expression source for this operation.
        enable: Boolean value or SystemVerilog expression source.

    Returns:
        Handle to the newly created child.

    Section: F.7.46.2.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not an ExecutableImage", TgiFaultCode.INVALID_ID)
    lcf = _new_linker_command_file(name, commandLineSwitch, enable)
    if img.language_tools is not None:
        _, existing = _linker_choices(img.language_tools)
        if existing is not None or len(img.language_tools.linker_flags_or_linker_command_file) >= 2:
            raise TgiError("languageTools already has its linkerCommandFile choice", TgiFaultCode.INVALID_ARGUMENT)
    if img.language_tools is None:
        img.language_tools = ExecutableImage.LanguageTools()
    register_parent(img.language_tools, img, ("language_tools",), "single")
    from org.accellera.ipxact.v1685_2022 import StringExpression

    lt = img.language_tools
    if lt.linker is None:
        lt.linker = StringExpression(value="")
    lt.linker_flags_or_linker_command_file.append(lcf)
    register_parent(lt, img, ("language_tools",), "single")
    register_parent(lt.linker, lt, ("linker",), "single")
    register_parent(lcf, lt, ("linker_flags_or_linker_command_file",), "list")
    register_parent(lcf.name, lcf, ("name",), "single")
    register_parent(lcf.command_line_switch, lcf, ("command_line_switch",), "single")
    register_parent(lcf.enable, lcf, ("enable",), "single")
    return get_handle(lcf)


def addLanguageToolsFileBuilder(languageToolsID: str, fileType: str, command: str) -> str:  # F.7.46.3
    """Add fileBuilder to existing languageTools element.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.
        fileType: Value or expression source for this operation.
        command: Value or expression source for this operation.

    Returns:
        Handle to the newly created child.

    Section: F.7.46.3.
    """
    from org.accellera.ipxact.v1685_2022 import FileType, SimpleFileType, StringExpression

    lt = _require_language_tools(languageToolsID)
    if not isinstance(fileType, str) or not isinstance(command, str):
        raise TgiError("fileType and command must be strings", TgiFaultCode.INVALID_ARGUMENT)
    try:
        file_type = SimpleFileType(fileType)
    except ValueError as exc:
        raise TgiError("Expected a standard file type value", TgiFaultCode.INVALID_ARGUMENT) from exc
    fb = ExecutableImage.LanguageTools.FileBuilder(
        file_type=FileType(value=file_type), command=StringExpression(value=command)
    )
    lt.file_builder.append(fb)
    register_parent(fb, lt, ("file_builder",), "list")
    register_parent(fb.file_type, fb, ("file_type",), "single")
    register_parent(fb.command, fb, ("command",), "single")
    return get_handle(fb)


def addLinkerCommandFileGeneratorRef(linkerCommandFileID: str, generatorRef: str) -> str:  # F.7.46.4
    """Append a generatorRef to a linkerCommandFile.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.
        generatorRef: Value or expression source for this operation.

    Returns:
        Handle to the newly created child.

    Section: F.7.46.4.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    if not isinstance(generatorRef, str):
        raise TgiError("Expected generator name", TgiFaultCode.INVALID_ARGUMENT)
    from org.accellera.ipxact.v1685_2022.generator_ref import GeneratorRef

    gr = GeneratorRef(value=generatorRef)  # type: ignore[arg-type]
    lcf.generator_ref.append(gr)
    register_parent(gr, lcf, ("generator_ref",), "list")
    return get_handle(gr)


def removeBuildCommandCommand(buildCommandID: str) -> bool:  # F.7.46.5
    """Remove buildCommand.command element.

    Accept a standard buildCommand handle or a legacy file handle. Preserve
    generated metadata on edits; removal invalidates the expression handle.

        Args:
            buildCommandID: Handle or handles supplied by the TGI caller.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.5.
    """
    return _remove_build_expression(buildCommandID, "command")


def removeBuildCommandFlags(fileID: str) -> bool:  # F.7.46.6
    """Remove buildCommand.flags element.

    Accept a standard buildCommand handle or a legacy file handle. Preserve
    generated metadata on edits; removal invalidates the expression handle.

        Args:
            fileID: Handle or handles supplied by the TGI caller.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.6.
    """
    return _remove_build_expression(fileID, "flags")


def removeBuildCommandReplaceDefaultFlags(fileID: str) -> bool:  # F.7.46.7
    """Remove replaceDefaultFlags element.

    Preserve generated source identity on edits; invalidate handles on removal.
    Expression evaluation is separate from this source operation.

        Args:
            fileID: Handle or handles supplied by the TGI caller.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.7.
    """
    return _remove_build_expression(fileID, "replace_default_flags")


def removeBuildCommandTargetName(fileID: str) -> bool:  # F.7.46.8
    """Remove targetName element.

    Preserve generated source identity on edits; invalidate handles on removal.
    Expression evaluation is separate from this source operation.

        Args:
            fileID: Handle or handles supplied by the TGI caller.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.8.
    """
    return _remove_build_expression(fileID, "target_name")


def removeDefaultFileBuilderCommand(defaultFileBuilderID: str) -> bool:  # F.7.46.9
    """Remove command child from fileBuilder.

    Args:
        defaultFileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.9.
    """
    fb = _require_default_file_builder(defaultFileBuilderID)
    if fb.command is None:
        return False
    register_parent(fb.command, fb, ("command",), "single")
    return detach_child_by_handle(get_handle(fb.command))


def removeExecutableImageFileBuilderID(fileBuilderID: str) -> bool:  # F.7.46.10
    """Detach a fileBuilder from its parent list.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.10.
    """
    return _remove_nested(_require_executable_file_builder(fileBuilderID))


def removeExecutableImageLanguageTools(executableImageID: str) -> bool:  # F.7.46.11
    """Remove the entire languageTools element.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.11.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None:
        return False
    register_parent(img.language_tools, img, ("language_tools",), "single")
    return detach_child_by_handle(get_handle(img.language_tools))


def removeExecutableImageLinkerCommandFile(linkerCommandFileID: str) -> bool:  # F.7.46.12
    """Remove first linkerCommandFile under languageTools.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.12.
    """
    return _remove_nested(_require_linker_command_file(linkerCommandFileID))


def removeFileBuilderCommand(fileBuilderID: str) -> bool:  # F.7.46.13
    """Remove command element of fileBuilder.

    Invalidate the removed expression handle; return False when absent.

        Args:
            fileBuilderID: Handle or handles supplied by the TGI caller.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.13.
    """
    return _remove_builder_expression(fileBuilderID, "command")


def removeFileBuilderFlags(fileBuilderID: str) -> bool:  # F.7.46.14
    """Remove flags element of fileBuilder.

    Invalidate the removed expression handle; return False when absent.

        Args:
            fileBuilderID: Handle or handles supplied by the TGI caller.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.14.
    """
    return _remove_builder_expression(fileBuilderID, "flags")


def removeFileBuilderReplaceDefaultFlags(fileBuilderID: str) -> bool:  # F.7.46.15
    """Remove replaceDefaultFlags element of fileBuilder.

    Invalidate the removed expression handle; return False when absent.

        Args:
            fileBuilderID: Handle or handles supplied by the TGI caller.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.15.
    """
    return _remove_builder_expression(fileBuilderID, "replace_default_flags")


def removeLanguageToolsFileBuilder(fileBuilderID: str) -> bool:  # F.7.46.16
    """Remove fileBuilder from languageTools (alias context).

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.16.
    """
    return _remove_nested(_require_executable_file_builder(fileBuilderID))


def removeLanguageToolsLinkerCommandFile(languageToolsID: str) -> bool:  # F.7.46.17
    """Remove first linkerCommandFile of languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.17.
    """
    lt = _require_language_tools(languageToolsID)
    _, command_file = _linker_choices(lt)
    if command_file is None:
        return False
    return detach_child_by_handle(get_handle(command_file))


def removeLanguageToolsLinkerFlags(languageToolsID: str) -> bool:  # F.7.46.18
    """Remove linkerFlags element.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.18.
    """
    lt = _require_language_tools(languageToolsID)
    flags, _ = _linker_choices(lt)
    if flags is None:
        return False
    return detach_child_by_handle(get_handle(flags))


def removeLinkerCommandFileGeneratorRef(generatorRefID: str) -> bool:  # F.7.46.19
    """Clear all generatorRef entries from linkerCommandFile.

    Args:
        generatorRefID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.19.
    """
    return _remove_nested(_require_generator_ref(generatorRefID))


def setBuildCommandCommand(buildCommandID: str, command: str) -> bool:  # F.7.46.20
    """Set buildCommand.command value (creates buildCommand if absent).

    Accept a standard buildCommand handle or a legacy file handle. Preserve
    generated metadata on edits; removal invalidates the expression handle.

        Args:
            buildCommandID: Handle or handles supplied by the TGI caller.
            command: Value or expression source for this operation.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.20.
    """
    return _set_build_expression(buildCommandID, "command", command)


def setBuildCommandFlags(buildCommandID: str, flags: str) -> bool:  # F.7.46.21
    """Set buildCommand.flags value.

    Accept a standard buildCommand handle or a legacy file handle. Preserve
    generated metadata on edits; removal invalidates the expression handle.

        Args:
            buildCommandID: Handle or handles supplied by the TGI caller.
            flags: Value or expression source for this operation.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.21.
    """
    return _set_build_expression(buildCommandID, "flags", flags)


def setBuildCommandReplaceDefaultFlags(buildCommandID: str, valueExpression: str) -> bool:  # F.7.46.22
    """Set replaceDefaultFlags boolean.

    Preserve generated source identity on edits; invalidate handles on removal.
    Expression evaluation is separate from this source operation.

        Args:
            buildCommandID: Handle or handles supplied by the TGI caller.
            valueExpression: Value or expression source for this operation.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.22.
    """
    return _set_build_expression(buildCommandID, "replace_default_flags", valueExpression)


def setBuildCommandTargetName(buildCommandID: str, targetName: str) -> bool:  # F.7.46.23
    """Set targetName value.

    Preserve generated source identity on edits; invalidate handles on removal.
    Expression evaluation is separate from this source operation.

        Args:
            buildCommandID: Handle or handles supplied by the TGI caller.
            targetName: Value or expression source for this operation.

        Returns:
            True when the operation succeeds.

        Section: F.7.46.23.
    """
    return _set_build_expression(buildCommandID, "target_name", targetName)


def setExecutableImageLanguageTools(executableImageID: str) -> bool:  # F.7.46.24
    """Create (if absent) and return handle of languageTools.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the requested structure exists.

    Section: F.7.46.24.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not ExecutableImage", TgiFaultCode.INVALID_ID)
    if img.language_tools is None:
        img.language_tools = ExecutableImage.LanguageTools()
        register_parent(img.language_tools, img, ("language_tools",), "single")
    return True


def setExecutableImageLinker(executableImageID: str, linker: str) -> bool:  # F.7.46.25
    """Set linker text inside languageTools.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.
        linker: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.25.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not ExecutableImage", TgiFaultCode.INVALID_ID)
    if not isinstance(linker, str):
        raise TgiError("Expected linker expression string", TgiFaultCode.INVALID_ARGUMENT)
    if img.language_tools is None:
        img.language_tools = ExecutableImage.LanguageTools()
    register_parent(img.language_tools, img, ("language_tools",), "single")
    from org.accellera.ipxact.v1685_2022 import StringExpression

    _set_text_child(img.language_tools, "linker", linker, StringExpression, ("linker",))
    return True


def setExecutableImageLinkerFlags(executableImageID: str, flags: str) -> bool:  # F.7.46.26
    """Set linkerFlags text inside languageTools.

    Args:
        executableImageID: Handle or handles supplied by the TGI caller.
        flags: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.26.
    """
    img = _resolve(executableImageID)
    if not isinstance(img, ExecutableImage):
        raise TgiError("Handle is not ExecutableImage", TgiFaultCode.INVALID_ID)
    if not isinstance(flags, str):
        raise TgiError("Expected linker flags expression string", TgiFaultCode.INVALID_ARGUMENT)
    if img.language_tools is not None:
        existing_flags, _ = _linker_choices(img.language_tools)
        if existing_flags is None and len(img.language_tools.linker_flags_or_linker_command_file) >= 2:
            raise TgiError("languageTools linker choice exceeds schema cardinality", TgiFaultCode.INVALID_ARGUMENT)
    if img.language_tools is None:
        img.language_tools = ExecutableImage.LanguageTools()
    register_parent(img.language_tools, img, ("language_tools",), "single")
    from org.accellera.ipxact.v1685_2022 import StringExpression

    lt = img.language_tools
    _set_linker_choice(lt, StringExpression(value=flags), StringExpression)
    if lt.linker is None:
        _set_text_child(lt, "linker", "", StringExpression, ("linker",))
    return True


def setFileBuildCommand(fileID: str) -> bool:  # F.7.46.27
    """Ensure buildCommand exists and return its handle.

    Args:
        fileID: Handle or handles supplied by the TGI caller.

    Returns:
        True when the requested structure exists.

    Section: F.7.46.27.
    """
    from org.accellera.ipxact.v1685_2022 import File

    owner = _resolve(fileID)
    if not isinstance(owner, File):
        raise TgiError("Expected a file handle", TgiFaultCode.INVALID_ID)
    if owner.build_command is None:
        owner.build_command = File.BuildCommand()
    register_parent(owner.build_command, owner, ("build_command",), "single")
    return True


def setFileBuilderCommand(fileBuilderID: str, command: str) -> bool:  # F.7.46.28
    """Set generated command source text, preserving child identity and metadata.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.
        command: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.28.
    """
    return _set_builder_expression(fileBuilderID, "command", command)


def setFileBuilderFileType(fileBuilderID: str, fileTypeValue: str) -> bool:  # F.7.46.29
    """Set fileBuilder.fileType.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.
        fileTypeValue: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.29.
    """
    from org.accellera.ipxact.v1685_2022 import SimpleFileType

    fb = _require_file_builder(fileBuilderID)
    if not isinstance(fileTypeValue, str):
        raise TgiError("Expected file type source string", TgiFaultCode.INVALID_ARGUMENT)
    try:
        value = SimpleFileType(fileTypeValue)
    except ValueError as exc:
        raise TgiError("Expected a standard file type value", TgiFaultCode.INVALID_ARGUMENT) from exc
    fb.file_type.value = value
    register_parent(fb.file_type, fb, ("file_type",), "single")
    return True


def setFileBuilderFlags(fileBuilderID: str, flags: str) -> bool:  # F.7.46.30
    """Set generated flags source text, preserving child identity and metadata.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.
        flags: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.30.
    """
    return _set_builder_expression(fileBuilderID, "flags", flags)


def setFileBuilderReplaceDefaultFlags(fileBuilderID: str, valueExpression: str) -> bool:  # F.7.46.31
    """Set fileBuilder.replaceDefaultFlags.

    Args:
        fileBuilderID: Handle or handles supplied by the TGI caller.
        valueExpression: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.31.
    """
    return _set_builder_expression(fileBuilderID, "replace_default_flags", valueExpression)


def setLanguageToolsLinker(languageToolsID: str, linker: str) -> bool:  # F.7.46.32
    """Set linker value under languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.
        linker: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.32.
    """
    lt = _require_language_tools(languageToolsID)
    from org.accellera.ipxact.v1685_2022 import StringExpression

    _set_text_child(lt, "linker", linker, StringExpression, ("linker",))
    return True


def setLanguageToolsLinkerCommandFile(
    languageToolsID: str, name: str, commandLineSwitch: str, enable: str, linker: str
) -> bool:  # F.7.46.33
    """Append new linkerCommandFile under languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.
        name: Value or expression source for this operation.
        commandLineSwitch: Value or expression source for this operation.
        enable: Boolean value or SystemVerilog expression source.
        linker: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.33.
    """
    lt = _require_language_tools(languageToolsID)
    if not all(isinstance(value, str) for value in (name, commandLineSwitch, enable, linker)):
        raise TgiError("Linker command file fields must be expression strings", TgiFaultCode.INVALID_ARGUMENT)
    lcf = _new_linker_command_file(name, commandLineSwitch, enable)
    from org.accellera.ipxact.v1685_2022 import StringExpression

    _, existing = _linker_choices(lt)
    if existing is not None:
        # This setter addresses the singleton schema choice: preserve handles
        # for all three required children and update their source values.
        existing.name.value = name
        existing.command_line_switch.value = commandLineSwitch
        existing.enable.value = enable
        _set_text_child(lt, "linker", linker, StringExpression, ("linker",))
        register_parent(existing.name, existing, ("name",), "single")
        register_parent(existing.command_line_switch, existing, ("command_line_switch",), "single")
        register_parent(existing.enable, existing, ("enable",), "single")
        return True
    if len(lt.linker_flags_or_linker_command_file) >= 2:
        raise TgiError("languageTools linker choice exceeds schema cardinality", TgiFaultCode.INVALID_ARGUMENT)
    # Validate all inputs above before changing the model.
    _set_text_child(lt, "linker", linker, StringExpression, ("linker",))
    lt.linker_flags_or_linker_command_file.append(lcf)
    register_parent(lcf, lt, ("linker_flags_or_linker_command_file",), "list")
    register_parent(lcf.name, lcf, ("name",), "single")
    register_parent(lcf.command_line_switch, lcf, ("command_line_switch",), "single")
    register_parent(lcf.enable, lcf, ("enable",), "single")
    return True


def setLanguageToolsLinkerFlags(languageToolsID: str, linkerFlags: str, linker: str) -> bool:  # F.7.46.34
    """Set linkerFlags for languageTools.

    Args:
        languageToolsID: Handle or handles supplied by the TGI caller.
        linkerFlags: Value or expression source for this operation.
        linker: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.34.
    """
    lt = _require_language_tools(languageToolsID)
    from org.accellera.ipxact.v1685_2022 import StringExpression

    if not isinstance(linkerFlags, str) or not isinstance(linker, str):
        raise TgiError("Expected linker and flags expression strings", TgiFaultCode.INVALID_ARGUMENT)
    current_flags, _ = _linker_choices(lt)
    if current_flags is None and len(lt.linker_flags_or_linker_command_file) >= 2:
        raise TgiError("languageTools linker choice exceeds schema cardinality", TgiFaultCode.INVALID_ARGUMENT)
    # Both source strings are validated before either field changes.
    _set_text_child(lt, "linker", linker, StringExpression, ("linker",))
    _set_linker_choice(lt, StringExpression(value=linkerFlags), StringExpression)
    return True


def setLinkerCommandFileCommandLineSwitch(linkerCommandFileID: str, commandLineSwitch: str) -> bool:  # F.7.46.35
    """Set commandLineSwitch of linkerCommandFile.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.
        commandLineSwitch: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.35.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    from org.accellera.ipxact.v1685_2022 import StringExpression

    _set_lcf_expression(lcf, "command_line_switch", commandLineSwitch, StringExpression)
    return True


def setLinkerCommandFileEnable(linkerCommandFileID: str, enable: str) -> bool:  # F.7.46.36
    """Set enable flag of linkerCommandFile.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.
        enable: Boolean value or SystemVerilog expression source.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.36.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    _set_lcf_boolean(lcf, "enable", enable)
    return True


def setLinkerCommandFileName(linkerCommandFileID: str, name: str) -> bool:  # F.7.46.37
    """Set the linker command file name expression.

    Args:
        linkerCommandFileID: Handle or handles supplied by the TGI caller.
        name: Value or expression source for this operation.

    Returns:
        True when the operation succeeds.

    Section: F.7.46.37.
    """
    lcf = _require_linker_command_file(linkerCommandFileID)
    from org.accellera.ipxact.v1685_2022 import StringExpression

    _set_lcf_expression(lcf, "name", name, StringExpression)
    return True
