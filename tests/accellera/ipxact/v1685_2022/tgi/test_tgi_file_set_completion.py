"""Annex F file-set operations preserve typed XML models and owner identity."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import file_set as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    BusInterface,
    BusInterfaces,
    Component,
    ConfigurableLibraryRefType,
    Dependency,
    ExecutableImage,
    File,
    FileSet,
    FileSetRef,
    FileSets,
    FileSetType,
    FileType,
    IpxactUri,
    SimpleFileType,
    StringExpression,
    UnsignedBitExpression,
)
from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


def _assert_schema_valid(model):
    xml = XmlDocument.serializer().render(model)
    parsed = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(parsed), _SCHEMA.error_log
    return xml


def _component(name, target="source", set_name=None):
    set_name = set_name or name
    file_set = FileSet(
        name=set_name,
        file=[File(name=IpxactUri(value=f"{set_name}.c"), file_id=target,
                   file_type=[FileType(value=SimpleFileType.C_SOURCE)])],
    )
    group = BusInterfaceType.Target.FileSetRefGroup(file_set_ref=[FileSetRef(local_name=set_name)])
    bus = BusInterface(
        name="software",
        bus_type=ConfigurableLibraryRefType(vendor="v", library="l", name="bus", version="1"),
        choice=BusInterfaceType.Target(file_set_ref_group=[group]),
    )
    return Component(
        vendor="v",
        library="l",
        name=name,
        version="1",
        bus_interfaces=BusInterfaces(bus_interface=[bus]),
        file_sets=FileSets(file_set=[file_set]),
    )


def test_build_command_expression_uses_build_command_handle_and_parsed_xml():
    file = File(
        name=IpxactUri(value="source.c"),
        file_type=[FileType(value=SimpleFileType.C_SOURCE)],
        build_command=File.BuildCommand(replace_default_flags=UnsignedBitExpression(value="${CLEAR_FLAGS}")),
    )
    xml = _assert_schema_valid(file)
    parsed = XmlDocument.parser().from_string(xml, File)
    command_id = get_handle(parsed.build_command)
    assert api.getBuildCommandReplaceDefaultFlagsExpression(command_id) == "${CLEAR_FLAGS}"
    with pytest.raises(TgiError):
        api.getBuildCommandReplaceDefaultFlagsExpression(get_handle(parsed))


def test_file_reference_resolution_is_local_to_owning_file_set_and_removal_invalidates():
    roots = [_component("first", "shared", "common"), _component("second", "shared", "common")]
    registered = []
    for index, root in enumerate(roots):
        xml = _assert_schema_valid(root)
        parsed = XmlDocument.parser().from_string(xml, Component)
        vlnv = ("v", "l", f"root{index}", "1")
        registry.register(parsed, vlnv)
        registered.append(vlnv)

    parsed_first = resolve_handle(registry.get_id(("v", "l", "root0", "1")))
    set_handle = get_handle(parsed_first.file_sets.file_set[0])
    function = FileSetType.Function(file_ref="shared")
    parsed_first.file_sets.file_set[0].function.append(function)
    function_id = api.getFileSetFunctionIDs(set_handle)[0]
    file_id = api.getFunctionFileID(function_id)
    assert file_id is not None
    assert resolve_handle(file_id) is parsed_first.file_sets.file_set[0].file[0]
    assert api.getFunctionFileRefByID(function_id) == file_id
    assert api.getFunctionFileRefByName(function_id) == "shared"

    bus = parsed_first.bus_interfaces.bus_interface[0]
    group = bus.choice.file_set_ref_group[0]
    group_id = get_handle(group)
    refs = api.getFileSetRefGroupFileSetRefIDs(group_id)
    assert len(refs) == 1
    assert api.getFileSetGroupFileSetRefIDs(group_id) == refs
    target_id = api.getFileSetRefByID(refs[0])
    assert target_id == api.getFileSetRefLocalNameRefByID(refs[0])
    assert resolve_handle(target_id) is parsed_first.file_sets.file_set[0]
    assert resolve_handle(target_id) is not resolve_handle(
        get_handle(resolve_handle(registry.get_id(("v", "l", "root1", "1"))).file_sets.file_set[0])
    )

    descendant = get_handle(resolve_handle(file_id).file_type[0])
    assert api.removeFileSetFile(file_id)
    assert resolve_handle(file_id) is None
    assert resolve_handle(descendant) is None
    for vlnv in registered:
        registry.unregister(vlnv)


def test_reference_group_operations_support_schema_choices_and_references():
    root = _component("drivers")
    bus_group = root.bus_interfaces.bus_interface[0].choice.file_set_ref_group[0]
    outer_id = get_handle(bus_group)
    assert api.getFileSetGroupFileSetRefIDs(outer_id) == [get_handle(bus_group.file_set_ref[0])]
    added_id = api.addFileSetRefGroupFileSetRef(outer_id, "drivers")
    assert api.getFileSetRefGroupFileSetRefIDs(outer_id) == [get_handle(bus_group.file_set_ref[0]), added_id]
    executable_group = ExecutableImage.FileSetRefGroup()
    executable_group_id = get_handle(executable_group)
    executable_ref_id = api.addFileSetRefGroupFileSetRef(executable_group_id, "drivers")
    assert api.getFileSetGroupFileSetRefIDs(executable_group_id) == [executable_ref_id]
    xml = _assert_schema_valid(root)
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_bus_group = parsed.bus_interfaces.bus_interface[0].choice.file_set_ref_group[0]
    parsed_root_handle = get_handle(parsed)
    vlnv = ("v", "l", "nested-groups", "1")
    registry.register(parsed, vlnv)
    try:
        ref_id = api.getFileSetGroupFileSetRefIDs(get_handle(parsed_bus_group))[0]
        assert api.getFileSetRefByID(ref_id) == get_handle(parsed.file_sets.file_set[0])
        assert parsed_root_handle == registry.get_id(vlnv)
    finally:
        registry.unregister(vlnv)


def test_extended_file_set_operations_build_schema_typed_values_and_preserve_order():
    root = FileSet(
        name="all-sources",
        file=[File(name=IpxactUri(value="base.c"), file_type=[FileType(value=SimpleFileType.C_SOURCE)])],
    )
    root_id = get_handle(root)
    file_id = api.getFileSetFileIDs(root_id)[0]
    define_id = api.addFileDefine(file_id, "SIZE", "1 + 2")
    file_dependency_id = api.addFileDependency(file_id, "generated.h")
    exported_id = api.addFileExportedName(file_id, "run")
    extra_type_id = api.addFileFileType(file_id, "user")
    image_type_id = api.addFileImageType(file_id, "boot")
    set_dependency_id = api.addFileSetDependency(root_id, "common")
    builder_id = api.addFileSetDefaultFileBuilder(root_id, "cSource")
    added_file_id = api.addFileSetFile(root_id, "main.c", ["cSource", "systemVerilogSource"])
    function_id = api.addFileSetFunction(root_id, "main-file")
    group_id = api.addFileSetGroup(root_id, "application")
    argument_id = api.addFunctionArgument(function_id, "count", "4", "int")
    source_id = api.addFunctionSourceFile(function_id, "main.c", "cSource")
    assert api.setFunctionArgumentDataType(argument_id, "unsigned int")

    assert resolve_handle(define_id).value.value == "1 + 2"
    assert resolve_handle(argument_id).value.value == "4"
    assert api.getFileSetFileIDs(root_id) == [file_id, added_file_id]
    assert api.getFunctionArgumentIDs(function_id) == [argument_id]
    assert api.getFunctionSourceFileIDs(function_id) == [source_id]
    assert api.getFunctionArgumentDataType(argument_id) == "unsigned int"
    assert api.getFunctionSourceFileName(source_id) == "main.c"
    assert api.getSourceFileFileType(source_id) == "cSource"
    assert api.getSourceFileFileTypeID(source_id) == get_handle(resolve_handle(source_id).file_type)
    assert api.getSourceFileSourceName(source_id) == "main.c"
    assert api.getFileDefineIDs(file_id) == [define_id]
    assert api.getFileDependencyIDs(file_id) == [file_dependency_id]
    assert api.getFileExportedNameIDs(file_id) == [exported_id]
    assert api.getFileExportedNames(file_id) == ["run"]
    assert api.getFileFileTypeIDs(file_id) == [get_handle(resolve_handle(file_id).file_type[0]), extra_type_id]
    assert api.getFileFileTypes(file_id) == ["cSource", "user"]
    assert api.getFileImageTypeIDs(file_id) == [image_type_id]
    assert api.getFileImageTypes(file_id) == ["boot"]
    assert api.getFileSetDefaultFileBuilderIDs(root_id) == [builder_id]
    assert api.getFileSetDependencyIDs(root_id) == [set_dependency_id]
    assert api.getFileSetGroupIDs(root_id) == [group_id]
    assert api.getFileSetGroups(root_id) == ["application"]

    xml = _assert_schema_valid(root)
    loaded = XmlDocument.parser().from_string(xml, FileSet)
    assert XmlDocument.serializer().render(loaded) == xml
    assert [entry.name.value for entry in loaded.file] == ["base.c", "main.c"]


def test_remove_operations_validate_child_kind_owner_and_invalidate_equal_sibling_descendants():
    root = FileSet(
        name="remove-me",
        file=[
            File(name=IpxactUri(value="same.c"), file_id="one", file_type=[FileType(value=SimpleFileType.C_SOURCE)]),
            File(name=IpxactUri(value="same.c"), file_id="two", file_type=[FileType(value=SimpleFileType.C_SOURCE)]),
        ],
        dependency=[Dependency(value="first"), Dependency(value="second")],
    )
    root_id = get_handle(root)
    first, second = api.getFileSetFileIDs(root_id)
    first_descendant = get_handle(resolve_handle(first).file_type[0])
    dependency_ids = api.getFileSetDependencyIDs(root_id)
    with pytest.raises(TgiError):
        api.removeFileSetFile(dependency_ids[0])
    with pytest.raises(TgiError):
        api.removeFileDependency(dependency_ids[0])
    assert api.removeFileSetDependency(dependency_ids[0])
    assert resolve_handle(dependency_ids[0]) is None
    assert api.getFileSetDependencyIDs(root_id) == [dependency_ids[1]]
    assert api.removeFileSetFile(first)
    assert resolve_handle(first) is None
    assert resolve_handle(first_descendant) is None
    assert api.getFileSetFileIDs(root_id) == [second]
    assert resolve_handle(second).file_id == "two"


def test_optional_child_setters_preserve_handles_and_invalid_values_are_atomic():
    function = FileSetType.Function(
        file_ref="source",
        source_file=[
            FileSetType.Function.SourceFile(
                source_name=IpxactUri(value="before.c"),
                file_type=FileType(value=SimpleFileType.C_SOURCE),
            )
        ],
    )
    file = File(name=IpxactUri(value="before.c"), file_type=[FileType(value=SimpleFileType.C_SOURCE)])
    root = FileSet(name="mutations", file=[file], function=[function])
    root_id = get_handle(root)
    file_id = api.getFileSetFileIDs(root_id)[0]
    function_id = api.getFileSetFunctionIDs(root_id)[0]
    source_id = api.getFunctionSourceFileIDs(function_id)[0]
    argument_id = api.addFunctionArgument(function_id, "stable", "1", "int")

    assert api.setFileIsIncludeFile(file_id, True)
    include_id = api.getFileIsIncludeFileID(file_id)
    assert api.getFileIsIncludeFileID(file_id) == include_id
    assert api.setFileIsIncludeFile(file_id, False)
    assert api.getFileIsIncludeFileID(file_id) == include_id
    assert api.setFileLogicalName(file_id, "work")
    logical_id = api.getFileLogicalNameID(file_id)
    assert api.getFileLogicalNameID(file_id) == logical_id
    assert api.setFileLogicalName(file_id, "work-again")
    assert api.getFileLogicalNameID(file_id) == logical_id
    assert api.setFileIsStructural(file_id, True)
    assert api.setFileName(file_id, "after.c")
    assert api.setFunctionDisabled(function_id, "1 + 1")
    disabled_id = api.getFunctionDisabledID(function_id)
    assert api.getFunctionDisabled(function_id) is True
    assert api.setFunctionEntryPoint(function_id, "start")
    assert api.setFunctionFileRef(function_id, "updated")
    assert api.setFunctionReplicate(function_id, True)
    assert api.setFunctionReturnType(function_id, "int")
    assert api.setFunctionSourceFileName(function_id, "new-source.c")
    assert api.setSourceFileFileType(source_id, "systemVerilogSource")
    assert api.setSourceFileSourceName(source_id, "final.c")
    assert api.getFunctionDisabledID(function_id) == disabled_id
    assert api.getFunctionDisabledExpression(function_id) == "1 + 1"
    assert api.getFunctionSourceFileName(source_id) == "final.c"
    assert api.getFunctionSourceFileType(source_id) == "systemVerilogSource"
    assert api.getFileIsStructural(file_id) is True
    assert api.getFileLogicalName(file_id) == "work-again"
    assert api.getFunctionFileRefByName(function_id) == "updated"
    assert api.getFunctionFileID(function_id) is None

    before = XmlDocument.serializer().render(root)
    invalid_calls = [
        lambda: api.addFileFileType(file_id, "custom"),
        lambda: api.addFileSetFile(root_id, "bad.c", ["cSource", "invalid"]),
        lambda: api.addFunctionArgument(function_id, "bad", "1", "not-a-type"),
        lambda: api.setFunctionArgumentDataType(argument_id, "bad"),
        lambda: api.setFileIsIncludeFile(file_id, 1),
        lambda: api.setFileIsStructural(file_id, "true"),
        lambda: api.setFunctionReplicate(function_id, 1),
        lambda: api.setFunctionReturnType(function_id, "long"),
        lambda: api.setSourceFileFileType(source_id, "unknown-custom-file-type"),
        lambda: api.setFileName(file_id, None),
    ]
    for invalid_call in invalid_calls:
        snapshot = XmlDocument.serializer().render(root)
        with pytest.raises(TgiError):
            invalid_call()
        assert XmlDocument.serializer().render(root) == snapshot
    assert before == XmlDocument.serializer().render(root)


def test_disabled_evaluation_handles_absent_unresolved_and_self_contained_expressions():
    functions = [
        FileSetType.Function(file_ref="a"),
        FileSetType.Function(file_ref="b", disabled=UnsignedBitExpression(value="0")),
        FileSetType.Function(file_ref="c", disabled=UnsignedBitExpression(value="1 + 1")),
        FileSetType.Function(file_ref="d", disabled=UnsignedBitExpression(value="${DISABLED}")),
    ]
    ids = [get_handle(function) for function in functions]
    assert [api.getFunctionDisabled(function_id) for function_id in ids] == [False, False, True, False]
    assert api.getFunctionDisabledExpression(ids[3]) == "${DISABLED}"
    owner = FileSet(name="no-sources", function=[functions[0]])
    owner_id = get_handle(owner)
    function_id = api.getFileSetFunctionIDs(owner_id)[0]
    before = XmlDocument.serializer().render(owner)
    assert not api.setFunctionSourceFileName(function_id, "orphan.c")
    assert XmlDocument.serializer().render(owner) == before


def test_all_file_and_function_child_removers_detach_exact_typed_children():
    root = FileSet(name="removable")
    root_id = get_handle(root)
    file_id = api.addFileSetFile(root_id, "source.c", ["cSource"])
    file = resolve_handle(file_id)
    build_command = File.BuildCommand(command=StringExpression(value="cc"))
    file.build_command = build_command
    api.setFileIsIncludeFile(file_id, True)
    api.setFileIsStructural(file_id, True)
    api.setFileLogicalName(file_id, "library")
    define_id = api.addFileDefine(file_id, "LEVEL", "3")
    file_dependency_id = api.addFileDependency(file_id, "header.h")
    exported_name_id = api.addFileExportedName(file_id, "main")
    extra_file_type_id = api.addFileFileType(file_id, "user")
    image_type_id = api.addFileImageType(file_id, "boot")

    function_id = api.addFileSetFunction(root_id, "source-id")
    argument_id = api.addFunctionArgument(function_id, "mode", "1", "int")
    source_file_id = api.addFunctionSourceFile(function_id, "source.c", "cSource")
    api.setFunctionDisabled(function_id, "1")
    api.setFunctionEntryPoint(function_id, "main")
    api.setFunctionReturnType(function_id, "int")
    set_dependency_id = api.addFileSetDependency(root_id, "common")
    group_id = api.addFileSetGroup(root_id, "software")

    command_descendant_id = get_handle(build_command.command)
    is_include_id = api.getFileIsIncludeFileID(file_id)
    logical_name_id = api.getFileLogicalNameID(file_id)
    disabled_id = api.getFunctionDisabledID(function_id)
    assert api.getFileDefineIDs(file_id) == [define_id]
    assert api.getFileDependencyIDs(file_id) == [file_dependency_id]
    assert api.getFileExportedNameIDs(file_id) == [exported_name_id]
    assert api.getFileImageTypeIDs(file_id) == [image_type_id]
    assert api.getFileFileTypeIDs(file_id) == [get_handle(file.file_type[0]), extra_file_type_id]
    assert api.getFunctionArgumentIDs(function_id) == [argument_id]
    assert api.getFunctionSourceFileIDs(function_id) == [source_file_id]
    _assert_schema_valid(root)

    assert api.removeFileBuildCommand(file_id)
    assert resolve_handle(command_descendant_id) is None
    assert api.removeFileDefine(define_id)
    assert api.removeFileDependency(file_dependency_id)
    assert api.removeFileExportedName(exported_name_id)
    assert api.removeFileFileType(extra_file_type_id)
    assert api.getFileFileTypeIDs(file_id) == [get_handle(file.file_type[0])]
    assert not api.removeFileFileType(get_handle(file.file_type[0]))
    assert api.removeFileImageType(image_type_id)
    assert api.removeFileIsIncludeFile(file_id)
    assert api.removeFileIsStructural(file_id)
    assert api.removeFileLogicalName(file_id)
    assert resolve_handle(is_include_id) is None
    assert resolve_handle(logical_name_id) is None

    assert api.removeFileSetDependency(set_dependency_id)
    assert api.removeFileSetGroup(group_id)
    assert api.removeFunctionArgument(argument_id)
    assert api.removeFunctionDisabled(function_id)
    assert resolve_handle(disabled_id) is None
    assert api.removeFunctionEntryPoint(function_id)
    assert api.removeFunctionReturnType(function_id)
    assert api.removeFunctionSourceFile(source_file_id)
    assert api.removeFileSetFunction(function_id)
    assert resolve_handle(function_id) is None
    assert not api.removeFileBuildCommand(file_id)


def test_removing_function_invalidates_its_registered_descendants():
    root = FileSet(name="function-owner")
    root_id = get_handle(root)
    function_id = api.addFileSetFunction(root_id, "source-id")
    argument_id = api.addFunctionArgument(function_id, "size", "8", "int")
    source_id = api.addFunctionSourceFile(function_id, "source.c", "cSource")
    api.setFunctionDisabled(function_id, "0")
    disabled_id = api.getFunctionDisabledID(function_id)
    assert api.getFunctionArgumentIDs(function_id) == [argument_id]
    assert api.getFunctionSourceFileIDs(function_id) == [source_id]
    assert api.removeFileSetFunction(function_id)
    assert resolve_handle(function_id) is None
    assert resolve_handle(argument_id) is None
    assert resolve_handle(source_id) is None
    assert resolve_handle(disabled_id) is None
