"""Executable-image BASE getters traverse generated mixed linker metadata."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import file_builder as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ExecutableImage,
    FileSetRef,
    FileType,
    LinkerCommandFile,
    SimpleFileType,
    StringExpression,
    UnsignedBitExpression,
)


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
def test_mixed_linker_sources_and_lifetime(parsed, reverse):
    command = LinkerCommandFile(
        name=StringExpression(value="link.ld"),
        command_line_switch=StringExpression(value="-T"),
        enable=UnsignedBitExpression(value="1"),
    )
    choices = [StringExpression(value="-L${LIB}"), command]
    if reverse:
        choices.reverse()
    root = ExecutableImage(
        name="image", image_id="image",
        language_tools=ExecutableImage.LanguageTools(
            linker=StringExpression(value="ld"),
            linker_flags_or_linker_command_file=choices,
            file_builder=[
                ExecutableImage.LanguageTools.FileBuilder(
                    file_type=FileType(value=SimpleFileType.C_SOURCE), command=StringExpression(value="cc")
                )
            ],
        ),
        file_set_ref_group=ExecutableImage.FileSetRefGroup(file_set_ref=[FileSetRef(local_name="sources")]),
    )
    xml = XmlDocument.serializer().render(root)
    if parsed:
        root = XmlDocument.parser().from_string(xml, ExecutableImage)
    handle = get_handle(root)
    before = XmlDocument.serializer().render(root)
    assert api.getExecutableImageLinker(handle) == "ld"
    assert api.getExecutableImageLinkerExpression(handle) == "ld"
    assert api.getExecutableImageLinkerFlags(handle) == "-L${LIB}"
    assert api.getExecutableImageLinkerFlagsExpression(handle) == "-L${LIB}"
    command_id = api.getExecutableImageLinkerCommandFileID(handle)
    assert resolve_handle(command_id).name.value == "link.ld"
    builders = api.getExecutableImageFileBuilderIDs(handle)
    refs = api.getExecutableImageFileSetRefIDs(handle)
    tools = api.getExecutableImageLanguageToolsID(handle)
    assert api.getExecutableImageFileBuilderIDs(handle) == builders
    assert resolve_handle(refs[0]).local_name == "sources"
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(command_id)
    assert api.getExecutableImageLinkerCommandFileID(handle) is None
    assert api.getExecutableImageLinkerFlagsExpression(handle) == "-L${LIB}"
    assert detach_child_by_handle(tools)
    assert resolve_handle(builders[0]) is None
    assert resolve_handle(refs[0]) is not None


def test_absent_and_wrong_handles():
    handle = get_handle(ExecutableImage(name="empty", image_id="empty"))
    funcs = [
        getattr(api, "getExecutableImage" + suffix)
        for suffix in [
            "FileBuilderIDs",
            "FileSetRefIDs",
            "LanguageToolsID",
            "Linker",
            "LinkerExpression",
            "LinkerFlags",
            "LinkerFlagsExpression",
            "LinkerCommandFileID",
        ]
    ]
    assert [f(handle) for f in funcs] == [[], [], None, None, None, None, None, None]
    for f in funcs:
        with pytest.raises(TgiError):
            f("missing-image")
