"""Complete Annex F file-builder BASE and EXTENDED operation coverage."""

import csv
import inspect
from pathlib import Path

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as aggregate
from amal.eda.accellera.ipxact.v1685_2022.tgi import file_builder as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentGenerator,
    ComponentGenerators,
    ExecutableImage,
    File,
    FileBuilderType,
    FileType,
    GeneratorRef,
    IpxactUri,
    LinkerCommandFile,
    SimpleFileType,
    StringExpression,
    UnsignedBitExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2022.component_type import ComponentType

SCHEMA_PATH = "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"


def _validate(model):
    xml = XmlDocument.serializer().render(model)
    schema = etree.XMLSchema(etree.parse(SCHEMA_PATH))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    return xml


def test_file_builder_exports_and_public_contract_docstrings():
    with Path(".ai/tgi-coverage.csv").open(newline="") as stream:
        ledger = {row[2] for row in csv.reader(stream) if len(row) > 2 and row[0].startswith(("F.7.45.", "F.7.46."))}
    assert set(api.__all__) == ledger
    assert len(api.__all__) == 91
    for name in api.__all__:
        operation = getattr(api, name)
        assert getattr(aggregate, name) is operation
        doc = inspect.getdoc(operation)
        assert doc is not None
        assert "Args:" in doc
        assert "Returns:" in doc
        assert "Section: F.7." in doc
    expected_parameters = {
        "addExecutableImageFileBuilderID": ["executableImageID", "fileType", "command"],
        "addExecutableImageLinkerCommandFile": ["executableImageID", "name", "commandLineSwitch", "enable"],
        "addLanguageToolsFileBuilder": ["languageToolsID", "fileType", "command"],
        "addLinkerCommandFileGeneratorRef": ["linkerCommandFileID", "generatorRef"],
        "removeExecutableImageLinkerCommandFile": ["linkerCommandFileID"],
        "removeLinkerCommandFileGeneratorRef": ["generatorRefID"],
        "setExecutableImageLanguageTools": ["executableImageID"],
        "setFileBuildCommand": ["fileID"],
        "setLanguageToolsLinkerCommandFile": ["languageToolsID", "name", "commandLineSwitch", "enable", "linker"],
        "setLanguageToolsLinkerFlags": ["languageToolsID", "linkerFlags", "linker"],
        "setLinkerCommandFileCommandLineSwitch": ["linkerCommandFileID", "commandLineSwitch"],
    }
    for name, parameters in expected_parameters.items():
        assert list(inspect.signature(getattr(api, name)).parameters) == parameters
    assert inspect.signature(api.setExecutableImageLanguageTools).return_annotation == "bool"
    assert inspect.signature(api.setFileBuildCommand).return_annotation == "bool"
    assert inspect.signature(api.setLanguageToolsLinkerCommandFile).return_annotation == "bool"


@pytest.mark.parametrize("parsed", [False, True])
def test_file_builder_metadata_choices_roundtrip_and_lifetimes(parsed):
    image = ExecutableImage(name="application", image_id="app")
    image_id = get_handle(image)

    assert api.setExecutableImageLanguageTools(image_id) is True
    tools_id = api.getExecutableImageLanguageToolsID(image_id)
    assert resolve_handle(tools_id) is image.language_tools
    assert api.getLanguageToolsFileBuilderIDs(tools_id) == []

    builder_id = api.addLanguageToolsFileBuilder(tools_id, "cSource", "cc -c ${SOURCE}")
    builder = resolve_handle(builder_id)
    assert api.getExecutableImageFileBuilderIDs(image_id) == [builder_id]
    assert api.getLanguageToolsFileBuilderIDs(tools_id) == [builder_id]
    assert api.getFileBuilderCommand(builder_id) == "cc -c ${SOURCE}"
    assert api.getFileBuilderCommandExpression(builder_id) == "cc -c ${SOURCE}"
    assert api.getFileBuilderFileType(builder_id) == "cSource"
    file_type_id = api.getFileBuilderFileTypeID(builder_id)
    assert resolve_handle(file_type_id) is builder.file_type
    command_id = api.getFileBuilderCommandID(builder_id)
    command = resolve_handle(command_id)
    command.other_attributes["{urn:test}source"] = "retained"
    builder.file_type.user = "custom"
    builder.file_type.libext = ".c"
    original_file_type_id = api.getFileBuilderFileTypeID(builder_id)
    assert api.setFileBuilderCommand(builder_id, "") is True
    assert builder.command is command
    assert command.other_attributes["{urn:test}source"] == "retained"
    assert api.setFileBuilderCommand(builder_id, "cc -c ${SOURCE}") is True
    assert api.setFileBuilderFlags(builder_id, "-O2") is True
    assert api.getFileBuilderFlagsID(builder_id) is not None
    assert api.getFileBuilderFlags(builder_id) == "-O2"
    assert api.getFileBuilderFlagsExpression(builder_id) == "-O2"
    assert api.setFileBuilderReplaceDefaultFlags(builder_id, "1'b1") is True
    assert api.getFileBuilderReplaceDefaultFlagsID(builder_id) is not None
    assert api.getFileBuilderReplaceDefaultFlagsExpression(builder_id) == "1'b1"
    assert api.getFileBuilderReplaceDefaultFlags(builder_id) is True

    for setter, args in (
        (api.setFileBuilderCommand, (builder_id, None)),
        (api.setFileBuilderFlags, (builder_id, True)),
        (api.setFileBuilderReplaceDefaultFlags, (builder_id, 1)),
        (api.setFileBuilderFileType, (builder_id, "notAFileType")),
    ):
        before = (
            builder.command.value,
            builder.flags.value,
            builder.replace_default_flags.value,
            builder.file_type.value,
        )
        with pytest.raises(TgiError):
            setter(*args)
        assert (
            builder.command.value,
            builder.flags.value,
            builder.replace_default_flags.value,
            builder.file_type.value,
        ) == before

    assert api.setFileBuilderFileType(builder_id, "cppSource") is True
    assert builder.file_type.value is SimpleFileType.CPP_SOURCE
    assert api.getFileBuilderFileTypeID(builder_id) == original_file_type_id
    assert builder.file_type.user == "custom"
    assert builder.file_type.libext == ".c"
    assert api.setLanguageToolsLinker(tools_id, "ld -o ${OUTPUT}") is True
    linker_id = api.getLanguageToolsLinkerID(tools_id)
    linker = resolve_handle(linker_id)
    linker.other_attributes["{urn:test}source"] = "linker"
    assert api.getLanguageToolsLinker(tools_id) == "ld -o ${OUTPUT}"
    assert api.getLanguageToolsLinkerExpression(tools_id) == "ld -o ${OUTPUT}"

    assert api.setLanguageToolsLinkerFlags(tools_id, "-L${LIB}", "ld -o ${OUTPUT}") is True
    linker_flags_id = api.getLanguageToolsLinkerFlagsID(tools_id)
    assert resolve_handle(linker_flags_id) is not None
    assert api.getLanguageToolsLinkerFlags(tools_id) == "-L${LIB}"
    assert api.getLanguageToolsLinkerFlagsExpression(tools_id) == "-L${LIB}"
    assert api.getLanguageToolsLinkerID(tools_id) == linker_id
    assert linker.other_attributes["{urn:test}source"] == "linker"

    assert api.setLanguageToolsLinkerCommandFile(tools_id, "link.ld", "-T", "1'b1", "ld") is True
    lcf_id = api.getLanguageToolsLinkerCommandFileID(tools_id)
    assert resolve_handle(lcf_id) is not None
    name_id = api.getLinkerCommandFileNameID(lcf_id)
    switch_id = api.getLinkerCommandFileCommandLineSwitchID(lcf_id)
    enable_id = api.getLinkerCommandFileEnableID(lcf_id)
    assert api.getExecutableImageLinkerCommandFileID(image_id) == lcf_id
    assert api.getLinkerCommandFileName(lcf_id) == "link.ld"
    assert api.getLinkerCommandFileNameExpression(lcf_id) == "link.ld"
    assert api.getLinkerCommandFileNameValue(lcf_id) == "link.ld"
    assert api.getLinkerCommandFileLineSwitch(lcf_id) == "-T"
    assert api.getLinkerCommandFileLineSwitchExpression(lcf_id) == "-T"
    assert api.getLinkerCommandFileCommandLineSwitch(lcf_id) == "-T"
    assert api.getLinkerCommandFileCommandLineSwitchExpression(lcf_id) == "-T"
    assert api.getLinkerCommandFileEnable(lcf_id) is True
    assert api.getLinkerCommandFileEnableExpression(lcf_id) == "1'b1"
    assert api.setLinkerCommandFileName(lcf_id, "${OUTPUT}.ld") is True
    assert api.setLinkerCommandFileCommandLineSwitch(lcf_id, "-T") is True
    assert api.setLinkerCommandFileEnable(lcf_id, "0") is True
    assert api.getLinkerCommandFileEnable(lcf_id) is False
    assert api.setLinkerCommandFileEnable(lcf_id, "1'b1") is True
    assert api.getLinkerCommandFileNameID(lcf_id) == name_id
    assert api.getLinkerCommandFileCommandLineSwitchID(lcf_id) == switch_id
    assert api.getLinkerCommandFileEnableID(lcf_id) == enable_id
    assert api.setLanguageToolsLinkerCommandFile(tools_id, "link.ld", "-T", "1'b1", "ld") is True
    assert api.getLanguageToolsLinkerCommandFileID(tools_id) == lcf_id
    assert api.getLinkerCommandFileNameID(lcf_id) == name_id
    assert api.getLinkerCommandFileCommandLineSwitchID(lcf_id) == switch_id
    assert api.getLinkerCommandFileEnableID(lcf_id) == enable_id

    first_ref = api.addLinkerCommandFileGeneratorRef(lcf_id, "build")
    second_ref = api.addLinkerCommandFileGeneratorRef(lcf_id, "package")
    assert api.getLinkerCommandFileGeneratorRefIDs(lcf_id) == [first_ref, second_ref]
    assert api.getLinkerCommandFileGeneratorRefByNames(lcf_id) == ["build", "package"]
    assert api.getLinkerCommandFileGeneratorRefByID(lcf_id, "notRegistered") is None
    assert api.getGeneratorRefByID(first_ref) is None
    assert api.removeLinkerCommandFileGeneratorRef(first_ref) is True
    assert resolve_handle(first_ref) is None
    assert api.getLinkerCommandFileGeneratorRefByNames(lcf_id) == ["package"]

    default_builder = FileBuilderType(
        file_type=FileType(value=SimpleFileType.VHDL_SOURCE),
        command=StringExpression(value="vcom ${SOURCE}"),
    )
    default_id = get_handle(default_builder)
    assert api.getFileBuilderCommand(default_id) == "vcom ${SOURCE}"
    assert api.getFileBuilderFileType(default_id) == "vhdlSource"
    default_command_id = api.getFileBuilderCommandID(default_id)
    assert api.setFileBuilderFlags(default_id, "-2008") is True
    assert api.getFileBuilderFlags(default_id) == "-2008"
    default_flags_id = api.getFileBuilderFlagsID(default_id)
    assert api.removeFileBuilderFlags(default_id) is True
    assert resolve_handle(default_flags_id) is None
    assert api.removeDefaultFileBuilderCommand(default_id) is True
    assert api.getFileBuilderCommand(default_id) is None
    assert resolve_handle(default_command_id) is None

    empty_image = ExecutableImage(name="empty", image_id="empty")
    empty_id = get_handle(empty_image)
    with pytest.raises(TgiError):
        api.addExecutableImageFileBuilderID(empty_id, "unsupported", "cc")
    assert empty_image.language_tools is None
    with pytest.raises(TgiError):
        api.addExecutableImageLinkerCommandFile(empty_id, None, "-T", True)
    assert empty_image.language_tools is None
    with pytest.raises(TgiError):
        api.setLanguageToolsLinkerCommandFile(tools_id, "link.ld", "-T", "bad", None)
    assert api.getLanguageToolsLinkerCommandFileID(tools_id) == lcf_id

    xml = _validate(image)
    if parsed:
        image = XmlDocument.parser().from_string(xml, ExecutableImage)
        image_id = get_handle(image)
        tools_id = api.getExecutableImageLanguageToolsID(image_id)
        linker_id = api.getLanguageToolsLinkerID(tools_id)
        builder_id = api.getLanguageToolsFileBuilderIDs(tools_id)[0]
        lcf_id = api.getLanguageToolsLinkerCommandFileID(tools_id)
        assert resolve_handle(lcf_id) is not None
        name_id = api.getLinkerCommandFileNameID(lcf_id)
        switch_id = api.getLinkerCommandFileCommandLineSwitchID(lcf_id)
        enable_id = api.getLinkerCommandFileEnableID(lcf_id)
        linker_flags_id = api.getLanguageToolsLinkerFlagsID(tools_id)
        assert resolve_handle(linker_flags_id) is not None

    assert api.getExecutableImageLinker(image_id) == "ld"
    assert api.getExecutableImageLinkerExpression(image_id) == "ld"
    assert api.getExecutableImageLinkerFlags(image_id) == "-L${LIB}"
    assert api.getExecutableImageLinkerFlagsExpression(image_id) == "-L${LIB}"
    assert api.getExecutableImageFileSetRefIDs(image_id) == []
    assert api.removeLanguageToolsLinkerFlags(tools_id) is True
    assert resolve_handle(linker_flags_id) is None
    assert api.removeExecutableImageLinkerCommandFile(lcf_id) is True
    assert resolve_handle(lcf_id) is None
    assert resolve_handle(name_id) is None
    assert resolve_handle(switch_id) is None
    assert resolve_handle(enable_id) is None
    assert api.getLanguageToolsLinkerCommandFileID(tools_id) is None
    assert api.removeLanguageToolsFileBuilder(builder_id) is True
    assert resolve_handle(builder_id) is None
    assert api.getLanguageToolsFileBuilderIDs(tools_id) == []
    assert api.removeExecutableImageLanguageTools(image_id) is True
    assert resolve_handle(tools_id) is None
    assert resolve_handle(linker_id) is None
    assert api.getExecutableImageLanguageToolsID(image_id) is None


def test_add_aliases_and_removal_paths_are_typed_and_complete():
    image = ExecutableImage(name="app", image_id="app")
    image_id = get_handle(image)
    builder_id = api.addExecutableImageFileBuilderID(image_id, "cSource", "cc ${SOURCE}")
    assert resolve_handle(builder_id) is not None
    assert api.getFileBuilderCommand(builder_id) == "cc ${SOURCE}"
    _validate(image)
    assert api.removeExecutableImageFileBuilderID(builder_id) is True
    assert resolve_handle(builder_id) is None

    assert api.setExecutableImageLinker(image_id, "ld") is True
    assert api.setExecutableImageLinkerFlags(image_id, "-Llib") is True
    assert api.getExecutableImageLinkerFlags(image_id) == "-Llib"
    lcf_id = api.addExecutableImageLinkerCommandFile(image_id, "link.ld", "-T", True)
    lcf = resolve_handle(lcf_id)
    assert lcf.name.value == "link.ld"
    assert lcf.command_line_switch.value == "-T"
    assert api.getExecutableImageLinkerCommandFileID(image_id) == lcf_id
    _validate(image)
    assert api.removeLanguageToolsLinkerCommandFile(api.getExecutableImageLanguageToolsID(image_id)) is True
    assert resolve_handle(lcf_id) is None

    # A default FileBuilderType can be edited through the common setters, but
    # executable-list removers must reject it as the wrong generated subtype.
    default_id = get_handle(FileBuilderType(file_type=FileType(value=SimpleFileType.USER)))
    with pytest.raises(TgiError):
        api.removeLanguageToolsFileBuilder(default_id)
    assert api.removeFileBuilderReplaceDefaultFlags(default_id) is False

    for operation, wrong_id in (
        (api.getFileBuilderFlags, image_id),
        (api.getLinkerCommandFileName, builder_id),
        (api.setLinkerCommandFileName, builder_id),
        (api.removeLinkerCommandFileGeneratorRef, image_id),
    ):
        with pytest.raises(TgiError):
            operation(wrong_id) if operation != api.setLinkerCommandFileName else operation(wrong_id, "x")


def test_generator_ref_resolution_is_scoped_to_owning_component():
    registry.clear()

    def make_component(vendor):
        image = ExecutableImage(
            name="application",
            image_id="app",
            language_tools=ExecutableImage.LanguageTools(
                linker=StringExpression(value="ld"),
                linker_flags_or_linker_command_file=[
                    # XML reference names are local componentGenerator names.
                    LinkerCommandFile(
                        name=StringExpression(value="link.ld"),
                        command_line_switch=StringExpression(value="-T"),
                        enable=UnsignedBitExpression(value="1"),
                        generator_ref=[GeneratorRef(value="build")],
                    )
                ],
            ),
        )
        component = Component(
            vendor=vendor,
            library="lib",
            name="device",
            version="1.0",
            component_generators=ComponentGenerators(
                component_generator=[
                    ComponentGenerator(name="build", generator_exe=IpxactUri(value="build.py")),
                    ComponentGenerator(name="other", generator_exe=IpxactUri(value="other.py")),
                ]
            ),
            cpus=ComponentType.Cpus(
                cpu=[
                    ComponentType.Cpus.Cpu(
                        name="cpu",
                        range=UnsignedPositiveLongintExpression(value="1"),
                        width=UnsignedPositiveIntExpression(value="32"),
                        executable_image=[image],
                        memory_map_ref="map",
                    )
                ]
            ),
        )
        registry.register(component, (vendor, "lib", "device", "1.0"))
        return component, image

    first_component, first_image = make_component("vendor.one")
    second_component, _ = make_component("vendor.two")
    first_generator, second_generator = (
        first_component.component_generators.component_generator[0],
        second_component.component_generators.component_generator[0],
    )
    image_id = get_handle(first_image)
    lcf_id = api.getExecutableImageLinkerCommandFileID(image_id)
    ref_id = api.getLinkerCommandFileGeneratorRefIDs(lcf_id)[0]
    assert api.getGeneratorRefByID(ref_id) == get_handle(first_generator)
    assert api.getLinkerCommandFileGeneratorRefByID(lcf_id, "build") == get_handle(first_generator)
    assert api.getGeneratorRefByID(ref_id) != get_handle(second_generator)
    assert api.getLinkerCommandFileGeneratorRefByID(lcf_id, "missing") is None
    registry.clear()


def test_build_command_boolean_expression_uses_slang_and_setter_status():
    file = File(name=IpxactUri(value="source.c"), file_type=[FileType(value=SimpleFileType.C_SOURCE)])
    file_id = get_handle(file)
    assert api.setFileBuildCommand(file_id) is True
    command_id = api.getFileBuildCommandID(file_id)
    assert isinstance(command_id, str)
    assert api.setBuildCommandReplaceDefaultFlags(command_id, "1'b0") is True
    assert api.getBuildCommandReplaceDefaultFlags(command_id) is False
    assert api.setBuildCommandReplaceDefaultFlags(command_id, "2 + 2 == 4") is True
    assert api.getBuildCommandReplaceDefaultFlags(command_id) is True
    assert api.getBuildCommandReplaceDefaultFlagsID(command_id) is not None
    assert api.setBuildCommandCommand(command_id, "cc ${SOURCE}") is True
    assert api.getBuildCommandCommand(file_id) == "cc ${SOURCE}"
    assert api.getBuildCommandCommandExpression(command_id) == "cc ${SOURCE}"
    assert api.getBuildCommandCommandID(command_id) is not None
    assert api.setBuildCommandFlags(command_id, "-O2") is True
    assert api.getBuildCommandFlags(file_id) == "-O2"
    assert api.getBuildCommandFlagsExpression(command_id) == "-O2"
    assert api.getBuildCommandFlagsID(command_id) is not None
    assert api.setBuildCommandTargetName(command_id, "${SOURCE}.o") is True
    assert api.getBuildCommandTargetName(file_id) == "${SOURCE}.o"
    assert api.getBuildCommandTargetNameExpression(command_id) == "${SOURCE}.o"
