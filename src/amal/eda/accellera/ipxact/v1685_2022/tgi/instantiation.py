# ruff: noqa: I001
"""Instantiation functions from IEEE 1685-2022 Annex F, sections F.7.55-F.7.56.

The BASE surface in F.7.55 reads ``componentInstantiation``,
``designConfigurationInstantiation``, and ``designInstantiation`` values and
reference nodes, along with the listed ``abstractionType``,
``abstractorInstance``, ``componentInstance``, ``externalTypeDefinitions``,
``fileSetRef``, and ``generatorChainSelector`` reference helpers. The EXTENDED
surface in F.7.56 edits component and design instantiation metadata and their
VLNV references. The functions operate on generated IP-XACT 1685-2022 model
objects; handles identify those objects and reference nodes rather than their
serialized text.

For ``*RefID`` functions, the returned handle identifies the reference element.
The ``*RefByID`` functions for design and design-configuration instantiations
resolve that reference's complete VLNV through the TGI registry and return the
registered root only when its generated model type matches. The registry must
already contain the target; these functions do not load files or traverse a
catalog. A missing reference target or a registered root of another type raises
``TgiError`` with ``NOT_FOUND``. VLNV getters report the source attributes,
including ``None`` for absent reference nodes. Local ``fileSetRef`` names are
returned as stored; this category does not resolve the referenced file set.

Reference-node getters restore immediate generated-model ownership so later
handle operations remain scoped to the owning object. List getters likewise
restore parent paths before returning their handles. Setters validate all input
before mutation and update existing reference nodes in place, preserving their
handles; removal operations use the registered ownership path and invalidate
removed subtrees. Invalid or wrong-kind handles raise ``INVALID_ID`` and
invalid setter arguments raise ``INVALID_ARGUMENT``. Optional absent values
return ``None`` or empty lists as specified by Annex F.
This module exports only the functions enumerated in F.7.55 and F.7.56.
"""

from collections.abc import Sequence

from org.accellera.ipxact.v1685_2022 import (
    ComponentInstance,
    ComponentInstantiationType,
    Design,
    DesignConfiguration,
    DesignConfigurationInstantiationType,
    DesignInstantiationType,
    ExternalTypeDefinitions,
    GeneratorChain,
)
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.clearbox_element_ref_type import ClearboxElementRefType
from org.accellera.ipxact.v1685_2022.constraint_set_ref import ConstraintSetRef
from org.accellera.ipxact.v1685_2022.file_builder_type import FileBuilderType
from org.accellera.ipxact.v1685_2022.file_set_ref import FileSetRef
from org.accellera.ipxact.v1685_2022.language_type import LanguageType
from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType

from .core import (
    TgiError,
    TgiFaultCode,
    resolve_handle,
    get_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.55)
    "getAbstractionTypeAbstractionRefID",
    "getAbstractorInstanceAbstractorRefID",
    "getComponentInstanceComponentRefID",
    "getComponentInstantiationArchitectureName",
    "getComponentInstantiationClearboxElementRefIDs",
    "getComponentInstantiationConfigurationName",
    "getComponentInstantiationConstraintSetRefIDs",
    "getComponentInstantiationDefaultFileBuilderIDs",
    "getComponentInstantiationFileSetRefIDs",
    "getComponentInstantiationIsVirtual",
    "getComponentInstantiationLanguage",
    "getComponentInstantiationLanguageID",
    "getComponentInstantiationLibraryName",
    "getComponentInstantiationModuleName",
    "getComponentInstantiationPackageName",
    "getDesignConfigurationInstantiationDesignConfigurationRefByID",
    "getDesignConfigurationInstantiationDesignConfigurationRefByVLNV",
    "getDesignConfigurationInstantiationDesignConfigurationRefID",
    "getDesignConfigurationInstantiationLanguage",
    "getDesignConfigurationInstantiationLanguageID",
    "getDesignInstantiationDesignRefByID",
    "getDesignInstantiationDesignRefByVLNV",
    "getDesignInstantiationDesignRefID",
    "getExternalTypeDefinitionsTypeDefinitionsRefID",
    "getFileSetRefLocalName",
    "getGeneratorChainSelectorGeneratorChainRefID",
    # EXTENDED (F.7.56)
    "addComponentInstantiationClearboxElementRef",
    "addComponentInstantiationConstraintSetRef",
    "addComponentInstantiationDefaultFileBuilder",
    "addComponentInstantiationFileSetRef",
    "removeComponentInstantiationArchitectureName",
    "removeComponentInstantiationClearboxElementRef",
    "removeComponentInstantiationConfigurationName",
    "removeComponentInstantiationConstraintSetRef",
    "removeComponentInstantiationDefaultFileBuilder",
    "removeComponentInstantiationFileSetRef",
    "removeComponentInstantiationIsVirtual",
    "removeComponentInstantiationLanguage",
    "removeComponentInstantiationLibraryName",
    "removeComponentInstantiationModuleName",
    "removeComponentInstantiationPackageName",
    "removeDesignConfigurationInstantiationLanguage",
    "setComponentInstantiationArchitectureName",
    "setComponentInstantiationConfigurationName",
    "setComponentInstantiationIsVirtual",
    "setComponentInstantiationLanguage",
    "setComponentInstantiationLibraryName",
    "setComponentInstantiationModuleName",
    "setComponentInstantiationPackageName",
    "setDesignConfigurationInstantiationDesignConfigurationRef",
    "setDesignConfigurationInstantiationLanguage",
    "setDesignInstantiationDesignRef",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------

def _validate_local_reference_name(value: str, schema_type: str) -> None:
    """Validate XML lexical names without imposing ASCII-only restrictions."""
    from lxml import etree

    if not isinstance(value, str):
        raise TgiError("Expected a local-name string", TgiFaultCode.INVALID_ARGUMENT)
    schema = etree.XMLSchema(etree.fromstring(
        f'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
        f'<xs:element name="name" type="xs:{schema_type}"/></xs:schema>'.encode()
    ))
    element = etree.Element("name")
    try:
        element.text = value
    except ValueError as exc:
        raise TgiError("Invalid XML name", TgiFaultCode.INVALID_ARGUMENT) from exc
    if not schema.validate(element):
        raise TgiError(f"Expected an XML {schema_type}", TgiFaultCode.INVALID_ARGUMENT)


def _detach_instantiation_reference(handle: str, field: str) -> bool:
    """Detach only references owned by the named component-instantiation list."""
    from .core import get_parent_info

    info = get_parent_info(handle)
    if info is None:
        return False
    if info.path != (field,) or not isinstance(resolve_handle(info.parent_handle), ComponentInstantiationType):
        raise TgiError("Reference is not owned by a component instantiation", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(handle)


def _resolve_component_instantiation(handle: str) -> ComponentInstantiationType | None:
    obj = resolve_handle(handle)
    return obj if isinstance(obj, ComponentInstantiationType) else None


def _resolve_design_config_instantiation(handle: str) -> DesignConfigurationInstantiationType | None:
    obj = resolve_handle(handle)
    return obj if isinstance(obj, DesignConfigurationInstantiationType) else None


def _registered_reference_target[T](
    ref: ConfigurableLibraryRefType | LibraryRefType | None,
    target_type: type[T],
    reference_name: str,
) -> T:
    """Resolve a top-level VLNV reference through the TGI registry."""
    from .core import registry

    if ref is None:
        raise TgiError(f"{reference_name} is absent", TgiFaultCode.NOT_FOUND)
    vlnv = (ref.vendor, ref.library, ref.name, ref.version)
    if any(not isinstance(part, str) or not part for part in vlnv):
        raise TgiError(f"{reference_name} has an incomplete VLNV", TgiFaultCode.NOT_FOUND)
    target_id = registry.get_id(vlnv)
    target = resolve_handle(target_id) if target_id is not None else None
    if not isinstance(target, target_type):
        raise TgiError(f"{reference_name} target is missing or has the wrong type", TgiFaultCode.NOT_FOUND)
    return target


def _validated_vlnv(value: Sequence[str] | str) -> tuple[str, str, str, str]:
    """Normalize a setter VLNV and reject malformed values before mutation."""
    from .core import vlnv_to_tuple

    try:
        parts = vlnv_to_tuple(value)
    except (TypeError, ValueError) as exc:
        raise TgiError("Expected a four-part VLNV", TgiFaultCode.INVALID_ARGUMENT) from exc
    if any(not isinstance(part, str) or not part.strip() for part in parts):
        raise TgiError("Expected four nonempty VLNV strings", TgiFaultCode.INVALID_ARGUMENT)
    return parts


def _require[T](obj: T | None, fault: str = TgiFaultCode.INVALID_ID) -> T:  # pragma: no cover - trivial
    # Wrapper to standardize None checking.
    if obj is None:
        raise TgiError("Invalid ID", fault)
    return obj


# ---------------------------------------------------------------------------
# BASE (F.7.55)
# ---------------------------------------------------------------------------

def getAbstractionTypeAbstractionRefID(abstractionTypeID: str) -> str | None:
    """Return handle of ``abstractionRef`` inside an abstractionType.

    Args:
        abstractionTypeID: Handle to an abstractionType element.

    Returns:
        Handle to its abstractionRef, or None if absent.

    Section: F.7.55.1.
    """
    at = resolve_handle(abstractionTypeID)
    from org.accellera.ipxact.v1685_2022.abstraction_types import AbstractionTypes

    if not isinstance(at, AbstractionTypes.AbstractionType):  # type: ignore[attr-defined]
        raise TgiError("Invalid abstractionType handle", TgiFaultCode.INVALID_ID)
    ref = getattr(at, "abstraction_ref", None)
    if ref is not None:
        register_parent(ref, at, ("abstraction_ref",), "single")
    return None if ref is None else get_handle(ref)


def getAbstractorInstanceAbstractorRefID(abstractorInstanceID: str) -> str | None:
    """Return handle of the ``abstractorRef`` of an abstractorInstance.

    Args:
        abstractorInstanceID: Handle to an abstractorInstance element.

    Returns:
        Handle to its abstractorRef, or None if absent.

    Section: F.7.55.2.
    """
    ai = resolve_handle(abstractorInstanceID)
    # AbstractorInstance is a nested dataclass inside
    # DesignConfiguration.InterconnectionConfiguration.AbstractorInstances
    from org.accellera.ipxact.v1685_2022.design_configuration import DesignConfiguration

    AbstractorInstanceCls = (
        DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance
    )
    if not isinstance(ai, AbstractorInstanceCls):
        raise TgiError("Invalid abstractorInstance handle", TgiFaultCode.INVALID_ID)
    ref = getattr(ai, "abstractor_ref", None)
    if ref is not None:
        register_parent(ref, ai, ("abstractor_ref",), "single")
    return None if ref is None else get_handle(ref)


def getComponentInstanceComponentRefID(componentInstanceID: str) -> str | None:
    """Return handle of the ``componentRef`` inside a componentInstance.

    Args:
        componentInstanceID: Handle to a componentInstance element.

    Returns:
        Handle to its componentRef, or None if absent.

    Section: F.7.55.3.
    """
    ci = resolve_handle(componentInstanceID)
    if not isinstance(ci, ComponentInstance):
        raise TgiError("Invalid componentInstance handle", TgiFaultCode.INVALID_ID)
    ref = getattr(ci, "component_ref", None)
    if ref is not None:
        register_parent(ref, ci, ("component_ref",), "single")
    return None if ref is None else get_handle(ref)


def getComponentInstantiationArchitectureName(componentInstantiationID: str) -> str | None:
    """Return ``architectureName`` value.

    Return None when absent; preserve explicit empty strings and whitespace.
    This source getter does not synthesize configured model defaults.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        The architectureName string, or None when absent.

    Section: F.7.55.4.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    return getattr(inst, "architecture_name", None)


def getComponentInstantiationClearboxElementRefIDs(componentInstantiationID: str) -> list[str]:
    """Return handles of all ``clearboxElementRef`` elements.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        Handles to its clearboxElementRef elements in document order, or an empty list.

    Section: F.7.55.5.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    refs_container = getattr(inst, "clearbox_element_refs", None)
    if refs_container is None:
        return []
    for ref in refs_container.clearbox_element_ref:
        register_parent(ref, inst, ("clearbox_element_refs", "clearbox_element_ref"), "list")
    return [get_handle(ref) for ref in refs_container.clearbox_element_ref]


def getComponentInstantiationConfigurationName(componentInstantiationID: str) -> str | None:
    """Return ``configurationName`` value.

    Return None when absent; preserve explicit empty strings and whitespace.
    This source getter does not synthesize configured model defaults.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        The configurationName string, or None when absent.

    Section: F.7.55.6.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    return getattr(inst, "configuration_name", None)


def getComponentInstantiationConstraintSetRefIDs(componentInstantiationID: str) -> list[str]:
    """Return handles of ``constraintSetRef`` elements.

    Restore ownership for parsed references before returning stable handles.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        Handles to its constraintSetRef elements in document order.

    Section: F.7.55.7.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    refs = inst.constraint_set_ref
    for ref in refs:
        register_parent(ref, inst, ("constraint_set_ref",), "list")
    return [get_handle(ref) for ref in refs]


def getComponentInstantiationDefaultFileBuilderIDs(componentInstantiationID: str) -> list[str]:
    """Return stable defaultFileBuilder handles and restore parsed ownership.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        Handles to its defaultFileBuilder elements in document order.

    Section: F.7.55.8.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    for fb in inst.default_file_builder:
        register_parent(fb, inst, ("default_file_builder",), "list")
    return [get_handle(fb) for fb in inst.default_file_builder]


def getComponentInstantiationFileSetRefIDs(componentInstantiationID: str) -> list[str]:
    """Return handles of ``fileSetRef`` elements.

    Restore ownership for parsed references before returning stable handles.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        Handles to its fileSetRef elements in document order.

    Section: F.7.55.9.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    refs = inst.file_set_ref
    for ref in refs:
        register_parent(ref, inst, ("file_set_ref",), "list")
    return [get_handle(ref) for ref in refs]


def getComponentInstantiationIsVirtual(componentInstantiationID: str) -> bool | None:
    """Return value of ``isVirtual``.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        The isVirtual value, or None when absent.

    Section: F.7.55.10.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    return getattr(inst, "is_virtual", None)


def getComponentInstantiationLanguage(componentInstantiationID: str) -> str | None:
    """Return language value (string) if present.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        The language string, or None when absent.

    Section: F.7.55.11.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    lang = getattr(inst, "language", None)
    if lang is None:
        return None
    return lang.value


def getComponentInstantiationLanguageID(componentInstantiationID: str) -> str | None:
    """Return handle of the ``language`` element.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        Handle to the language element, or None when absent.

    Section: F.7.55.12.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    lang = getattr(inst, "language", None)
    if lang is None:
        return None
    register_parent(lang, inst, ("language",), "single")
    return get_handle(lang)


def getComponentInstantiationLibraryName(componentInstantiationID: str) -> str | None:
    """Return libraryName value.

    Return None when absent; preserve explicit empty strings and whitespace.
    This source getter does not synthesize configured model defaults.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        The libraryName string, or None when absent.

    Section: F.7.55.13.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    return getattr(inst, "library_name", None)


def getComponentInstantiationModuleName(componentInstantiationID: str) -> str | None:
    """Return moduleName value.

    Return None when absent; preserve explicit empty strings and whitespace.
    This source getter does not synthesize configured model defaults.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        The moduleName string, or None when absent.

    Section: F.7.55.14.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    return getattr(inst, "module_name", None)


def getComponentInstantiationPackageName(componentInstantiationID: str) -> str | None:
    """Return packageName value.

    Return None when absent; preserve explicit empty strings and whitespace.
    This source getter does not synthesize configured model defaults.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        The packageName string, or None when absent.

    Section: F.7.55.15.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    return getattr(inst, "package_name", None)


def getDesignConfigurationInstantiationDesignConfigurationRefByID(
    designConfigurationInstantiationID: str,
) -> str:
    """Resolve the referenced designConfiguration object through the VLNV registry.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.

    Returns:
        Handle to the referenced designConfiguration object.

    Raises:
        TgiError: With NOT_FOUND when the target is absent or has the wrong type.

    Section: F.7.55.16.
    """
    dci = _require(_resolve_design_config_instantiation(designConfigurationInstantiationID))
    ref = getattr(dci, "design_configuration_ref", None)
    target = _registered_reference_target(ref, DesignConfiguration, "designConfigurationRef")
    return get_handle(target)


def getDesignConfigurationInstantiationDesignConfigurationRefByVLNV(
    designConfigurationInstantiationID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return VLNV tuple of the designConfigurationRef.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.

    Returns:
        The vendor, library, name, and version tuple, or four None values if absent.

    Section: F.7.55.17. Returns (None, None, None, None) if absent.
    """
    dci = _require(_resolve_design_config_instantiation(designConfigurationInstantiationID))
    ref = getattr(dci, "design_configuration_ref", None)
    if ref is None:
        return (None, None, None, None)
    return (ref.vendor, ref.library, ref.name, ref.version)


def getDesignConfigurationInstantiationDesignConfigurationRefID(designConfigurationInstantiationID: str) -> str | None:
    """Return the handle to the designConfigurationRef node.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.

    Returns:
        Handle to its designConfigurationRef element, or None if absent.

    Section: F.7.55.18.
    """
    dci = _require(_resolve_design_config_instantiation(designConfigurationInstantiationID))
    ref = getattr(dci, "design_configuration_ref", None)
    if ref is None:
        return None
    register_parent(ref, dci, ("design_configuration_ref",), "single")
    return get_handle(ref)


def getDesignConfigurationInstantiationLanguage(designConfigurationInstantiationID: str) -> str | None:
    """Return language value of a designConfigurationInstantiation.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.

    Returns:
        The language string, or None when absent.

    Section: F.7.55.19.
    """
    dci = _require(_resolve_design_config_instantiation(designConfigurationInstantiationID))
    lang = getattr(dci, "language", None)
    if lang is None:
        return None
    return lang.value


def getDesignConfigurationInstantiationLanguageID(designConfigurationInstantiationID: str) -> str | None:
    """Return handle of the language element.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.

    Returns:
        Handle to the language element, or None when absent.

    Section: F.7.55.20.
    """
    dci = _require(_resolve_design_config_instantiation(designConfigurationInstantiationID))
    lang = getattr(dci, "language", None)
    if lang is None:
        return None
    register_parent(lang, dci, ("language",), "single")
    return get_handle(lang)


def getDesignInstantiationDesignRefByID(designInstantiationID: str) -> str:
    """Resolve the referenced design object through the VLNV registry.

    Args:
        designInstantiationID: Handle to a designInstantiation element.

    Returns:
        Handle to the referenced design object.

    Raises:
        TgiError: With NOT_FOUND when the target is absent or has the wrong type.

    Section: F.7.55.21.
    """
    inst = resolve_handle(designInstantiationID)
    if not isinstance(inst, DesignInstantiationType):
        raise TgiError("Invalid designInstantiation handle", TgiFaultCode.INVALID_ID)
    target = _registered_reference_target(getattr(inst, "design_ref", None), Design, "designRef")
    return get_handle(target)


def getDesignInstantiationDesignRefByVLNV(
    designInstantiationID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return the stored designRef VLNV.

    Args:
        designInstantiationID: Handle to a designInstantiation element.

    Returns:
        The vendor, library, name, and version tuple, or four None values if absent.

    Section: F.7.55.22.
    """
    inst = resolve_handle(designInstantiationID)
    if not isinstance(inst, DesignInstantiationType):
        raise TgiError("Invalid designInstantiation handle", TgiFaultCode.INVALID_ID)
    ref = getattr(inst, "design_ref", None)
    if ref is None:
        return (None, None, None, None)
    return (ref.vendor, ref.library, ref.name, ref.version)


def getDesignInstantiationDesignRefID(designInstantiationID: str) -> str | None:
    """Return the designRef node handle.

    Args:
        designInstantiationID: Handle to a designInstantiation element.

    Returns:
        Handle to its designRef element, or None if absent.

    Section: F.7.55.23.
    """
    inst = resolve_handle(designInstantiationID)
    if not isinstance(inst, DesignInstantiationType):
        raise TgiError("Invalid designInstantiation handle", TgiFaultCode.INVALID_ID)
    ref = getattr(inst, "design_ref", None)
    if ref is None:
        return None
    register_parent(ref, inst, ("design_ref",), "single")
    return get_handle(ref)


def getExternalTypeDefinitionsTypeDefinitionsRefID(externalTypeDefinitionsID: str) -> str | None:
    """Return the nested typeDefinitionsRef node handle.

    Args:
        externalTypeDefinitionsID: Handle to an externalTypeDefinitions element.

    Returns:
        Handle to its typeDefinitionsRef element, or None if absent.

    Section: F.7.55.24.
    """
    external_types = resolve_handle(externalTypeDefinitionsID)
    if not isinstance(external_types, ExternalTypeDefinitions):
        raise TgiError("Invalid externalTypeDefinitions handle", TgiFaultCode.INVALID_ID)
    ref = getattr(external_types, "type_definitions_ref", None)
    if ref is None:
        return None
    register_parent(ref, external_types, ("type_definitions_ref",), "single")
    return get_handle(ref)


def getFileSetRefLocalName(fileSetRefID: str) -> str:
    """Return the localName stored on a fileSetRef.

    Args:
        fileSetRefID: Handle to a fileSetRef element.

    Returns:
        The localName string.

    Section: F.7.55.25.
    """
    ref = resolve_handle(fileSetRefID)
    if not isinstance(ref, FileSetRef):
        raise TgiError("Invalid fileSetRef handle", TgiFaultCode.INVALID_ID)
    return ref.local_name


def getGeneratorChainSelectorGeneratorChainRefID(generatorChainSelectorID: str) -> str | None:
    """Return the generatorChainRef node handle when selected (F.7.55.26).

    A selector using groupSelector has no generatorChainRef and returns None.

    Args:
        generatorChainSelectorID: Handle to a generatorChainSelector element.

    Returns:
        Handle to its generatorChainRef, or None when the selector uses groupSelector.

    Section: F.7.55.26.
    """
    selector = resolve_handle(generatorChainSelectorID)
    if not isinstance(selector, GeneratorChain.GeneratorChainSelector):
        raise TgiError("Invalid generatorChainSelector handle", TgiFaultCode.INVALID_ID)
    ref = selector.group_selector_or_generator_chain_ref
    from org.accellera.ipxact.v1685_2022.group_selector import GroupSelector

    if isinstance(ref, GroupSelector) or ref is None:
        return None
    if not isinstance(ref, ConfigurableLibraryRefType):
        raise TgiError("Invalid generatorChainRef value", TgiFaultCode.INVALID_ID)
    register_parent(ref, selector, ("group_selector_or_generator_chain_ref",), "single")
    return get_handle(ref)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.56)
# ---------------------------------------------------------------------------

def addComponentInstantiationClearboxElementRef(componentInstantiationID: str, name: str, pathSegmentValue: str) -> str:
    """Add a ``clearboxElementRef`` element.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        name: Clearbox element name, validated as an XML Name.
        pathSegmentValue: Value for the reference's pathSegment.

    Returns:
        Handle to the new clearboxElementRef.

    Section: F.7.56.1.
    """
    from .clearbox import _new_location

    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    _validate_local_reference_name(name, "Name")
    loc = _new_location(pathSegmentValue)
    ref = ClearboxElementRefType(name=name, location=[loc])
    if inst.clearbox_element_refs is None:
        inst.clearbox_element_refs = ComponentInstantiationType.ClearboxElementRefs()
    inst.clearbox_element_refs.clearbox_element_ref.append(ref)
    register_parent(ref, inst, ("clearbox_element_refs", "clearbox_element_ref"), "list")
    return get_handle(ref)


def addComponentInstantiationConstraintSetRef(componentInstantiationID: str, localName: str) -> str:
    """Add a ``constraintSetRef``.

    Validate localName as xs:NMTOKEN before mutation. Register immediate ownership;
    target existence and configured resolution are separate checks.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        localName: ConstraintSetRef localName, validated as an XML NMTOKEN.

    Returns:
        Handle to the new constraintSetRef.

    Section: F.7.56.2.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    _validate_local_reference_name(localName, "NMTOKEN")
    csr = ConstraintSetRef(local_name=localName)
    inst.constraint_set_ref.append(csr)  # type: ignore[attr-defined]
    register_parent(csr, inst, ("constraint_set_ref",), "list")
    return get_handle(csr)


def addComponentInstantiationDefaultFileBuilder(componentInstantiationID: str, fileType: str) -> str:
    """Add a ``defaultFileBuilder`` element.

    Accept standard fileType values (including user); reject invalid values
    before mutation and register immediate ownership.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        fileType: Standard fileType value for the defaultFileBuilder.

    Returns:
        Handle to the new defaultFileBuilder.

    Section: F.7.56.3.
    """
    from .file_set import _enum_file_type

    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    fb = FileBuilderType(file_type=_enum_file_type(fileType))
    inst.default_file_builder.append(fb)
    register_parent(fb, inst, ("default_file_builder",), "list")
    return get_handle(fb)


def addComponentInstantiationFileSetRef(componentInstantiationID: str, localName: str) -> str:
    """Add a ``fileSetRef`` element.

    Validate localName as xs:Name before mutation. Register immediate ownership;
    target existence and configured resolution are separate checks.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        localName: FileSetRef localName, validated as an XML Name.

    Returns:
        Handle to the new fileSetRef.

    Section: F.7.56.4.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    _validate_local_reference_name(localName, "Name")
    fsr = FileSetRef(local_name=localName)
    inst.file_set_ref.append(fsr)  # type: ignore[attr-defined]
    register_parent(fsr, inst, ("file_set_ref",), "list")
    return get_handle(fsr)


def removeComponentInstantiationArchitectureName(componentInstantiationID: str) -> bool:
    """Remove (clear) ``architectureName``.

    Repeated removal succeeds when already absent. Sibling fields and the
    instantiation handle remain intact; invalid handles raise INVALID_ID.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        True when architectureName has been removed.

    Section: F.7.56.5.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    inst.architecture_name = None
    return True


def removeComponentInstantiationClearboxElementRef(clearboxElementRefID: str) -> bool:
    """Remove a specific ``clearboxElementRef`` by handle.

    Args:
        clearboxElementRefID: Handle to the clearboxElementRef element to remove.

    Returns:
        True when the owned reference is removed, or False if it has no owner.

    Section: F.7.56.6.
    """
    ref = resolve_handle(clearboxElementRefID)
    if not isinstance(ref, ClearboxElementRefType):
        raise TgiError("Invalid clearboxElementRef handle", TgiFaultCode.INVALID_ID)
    return detach_child_by_handle(clearboxElementRefID)


def removeComponentInstantiationConfigurationName(componentInstantiationID: str) -> bool:
    """Clear ``configurationName``.

    Repeated removal succeeds when already absent. Sibling fields and the
    instantiation handle remain intact; invalid handles raise INVALID_ID.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        True when configurationName has been removed.

    Section: F.7.56.7.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    inst.configuration_name = None
    return True


def removeComponentInstantiationConstraintSetRef(constraintSetRefID: str) -> bool:
    """Remove a ``constraintSetRef`` by handle.

    Invalidate the removed subtree. Return False for an unowned reference;
    restore parsed ownership through the corresponding instantiation getter.

    Args:
        constraintSetRefID: Handle to the constraintSetRef element to remove.

    Returns:
        True when removed, or False when it has no registered owner.

    Section: F.7.56.8.
    """
    csr = resolve_handle(constraintSetRefID)
    if not isinstance(csr, ConstraintSetRef):
        raise TgiError("Invalid constraintSetRef handle", TgiFaultCode.INVALID_ID)
    return _detach_instantiation_reference(constraintSetRefID, "constraint_set_ref")


def removeComponentInstantiationDefaultFileBuilder(fileBuilderID: str) -> bool:
    """Remove an instantiation-owned builder and invalidate its descendants.

    Args:
        fileBuilderID: Handle to the defaultFileBuilder element to remove.

    Returns:
        True when removed, or False when it has no registered owner.

    Section: F.7.56.9.
    """
    fb = resolve_handle(fileBuilderID)
    if not isinstance(fb, FileBuilderType):
        raise TgiError("Invalid fileBuilder handle", TgiFaultCode.INVALID_ID)
    return _detach_instantiation_reference(fileBuilderID, "default_file_builder")


def removeComponentInstantiationFileSetRef(fileSetRefID: str) -> bool:
    """Remove a ``fileSetRef``.

    Invalidate the removed subtree. Return False for an unowned reference;
    restore parsed ownership through the corresponding instantiation getter.

    Args:
        fileSetRefID: Handle to the fileSetRef element to remove.

    Returns:
        True when removed, or False when it has no registered owner.

    Section: F.7.56.10.
    """
    fsr = resolve_handle(fileSetRefID)
    if not isinstance(fsr, FileSetRef):
        raise TgiError("Invalid fileSetRef handle", TgiFaultCode.INVALID_ID)
    return _detach_instantiation_reference(fileSetRefID, "file_set_ref")


def removeComponentInstantiationIsVirtual(componentInstantiationID: str) -> bool:
    """Clear ``isVirtual`` element.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        True when isVirtual has been removed.

    Section: F.7.56.11.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    inst.is_virtual = None
    return True


def removeComponentInstantiationLanguage(componentInstantiationID: str) -> bool:
    """Remove ``language`` element.

    Removal invalidates the language handle and descendants; repeated removal
    of an absent language succeeds. Parsed ownership is restored before removal.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        True when language has been removed.

    Section: F.7.56.12.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    if inst.language is not None:
        register_parent(inst.language, inst, ("language",), "single")
        return detach_child_by_handle(get_handle(inst.language))
    return True


def removeComponentInstantiationLibraryName(componentInstantiationID: str) -> bool:
    """Clear ``libraryName``.

    Repeated removal succeeds when already absent. Sibling fields and the
    instantiation handle remain intact; invalid handles raise INVALID_ID.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        True when libraryName has been removed.

    Section: F.7.56.13.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    inst.library_name = None
    return True


def removeComponentInstantiationModuleName(componentInstantiationID: str) -> bool:
    """Clear ``moduleName``.

    Repeated removal succeeds when already absent. Sibling fields and the
    instantiation handle remain intact; invalid handles raise INVALID_ID.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        True when moduleName has been removed.

    Section: F.7.56.14.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    inst.module_name = None
    return True


def removeComponentInstantiationPackageName(componentInstantiationID: str) -> bool:
    """Clear ``packageName``.

    Repeated removal succeeds when already absent. Sibling fields and the
    instantiation handle remain intact; invalid handles raise INVALID_ID.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        True when packageName has been removed.

    Section: F.7.56.15.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    inst.package_name = None
    return True


def removeDesignConfigurationInstantiationLanguage(designConfigurationInstantiationID: str) -> bool:
    """Remove language element from designConfigurationInstantiation.

    Removal invalidates the language handle and descendants; repeated removal
    of an absent language succeeds. Parsed ownership is restored before removal.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.

    Returns:
        True when language has been removed.

    Section: F.7.56.16.
    """
    dci = _require(_resolve_design_config_instantiation(designConfigurationInstantiationID))
    if dci.language is not None:
        register_parent(dci.language, dci, ("language",), "single")
        return detach_child_by_handle(get_handle(dci.language))
    return True


def setComponentInstantiationArchitectureName(componentInstantiationID: str, architectureName: str) -> bool:
    """Set ``architectureName`` source text, including empty strings and whitespace.

    Non-string values raise INVALID_ARGUMENT before mutation.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        architectureName: Source value to set.

    Returns:
        True when architectureName is set.

    Section: F.7.56.17.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    if not isinstance(architectureName, str):
        raise TgiError("Expected a string for architectureName", TgiFaultCode.INVALID_ARGUMENT)
    inst.architecture_name = architectureName
    return True


def setComponentInstantiationConfigurationName(componentInstantiationID: str, configurationName: str) -> bool:
    """Set ``configurationName`` source text, including empty strings and whitespace.

    Non-string values raise INVALID_ARGUMENT before mutation.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        configurationName: Source value to set.

    Returns:
        True when configurationName is set.

    Section: F.7.56.18.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    if not isinstance(configurationName, str):
        raise TgiError("Expected a string for configurationName", TgiFaultCode.INVALID_ARGUMENT)
    inst.configuration_name = configurationName
    return True


def setComponentInstantiationIsVirtual(componentInstantiationID: str, value: bool) -> bool:
    """Set ``isVirtual`` to a Boolean; reject other types before mutation.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        value: Boolean isVirtual value to set.

    Returns:
        True when isVirtual is set.

    Section: F.7.56.19.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    if not isinstance(value, bool):
        raise TgiError("Expected a Boolean virtual state", TgiFaultCode.INVALID_ARGUMENT)
    inst.is_virtual = value
    return True


def setComponentInstantiationLanguage(componentInstantiationID: str, language: str) -> bool:
    """Set generated language source text, preserving existing strict metadata.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        language: Nonempty language string to set.

    Returns:
        True when language is set.

    Section: F.7.56.20. Invalid text raises INVALID_ARGUMENT before mutation.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    if not isinstance(language, str) or not language.strip():
        raise TgiError("Expected a nonempty language string", TgiFaultCode.INVALID_ARGUMENT)
    if inst.language is None:
        inst.language = LanguageType(value=language)
    else:
        inst.language.value = language
    register_parent(inst.language, inst, ("language",), "single")
    return True


def setComponentInstantiationLibraryName(componentInstantiationID: str, libraryName: str) -> bool:
    """Set ``libraryName`` source text, including empty strings and whitespace.

    Non-string values raise INVALID_ARGUMENT before mutation.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        libraryName: Source value to set.

    Returns:
        True when libraryName is set.

    Section: F.7.56.21.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    if not isinstance(libraryName, str):
        raise TgiError("Expected a string for libraryName", TgiFaultCode.INVALID_ARGUMENT)
    inst.library_name = libraryName
    return True


def setComponentInstantiationModuleName(componentInstantiationID: str, moduleName: str) -> bool:
    """Set ``moduleName`` source text, including empty strings and whitespace.

    Non-string values raise INVALID_ARGUMENT before mutation.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        moduleName: Source value to set.

    Returns:
        True when moduleName is set.

    Section: F.7.56.22.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    if not isinstance(moduleName, str):
        raise TgiError("Expected a string for moduleName", TgiFaultCode.INVALID_ARGUMENT)
    inst.module_name = moduleName
    return True


def setComponentInstantiationPackageName(componentInstantiationID: str, packageName: str) -> bool:
    """Set ``packageName`` source text, including empty strings and whitespace.

    Non-string values raise INVALID_ARGUMENT before mutation.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.
        packageName: Source value to set.

    Returns:
        True when packageName is set.

    Section: F.7.56.23.
    """
    inst = _require(_resolve_component_instantiation(componentInstantiationID))
    if not isinstance(packageName, str):
        raise TgiError("Expected a string for packageName", TgiFaultCode.INVALID_ARGUMENT)
    inst.package_name = packageName
    return True


def setDesignConfigurationInstantiationDesignConfigurationRef(
    designConfigurationInstantiationID: str, designConfigurationVLNV: tuple[str, str, str, str],
) -> bool:
    """Update the generated reference in place after validating VLNV (F.7.56.24).

    Preserve existing configuration values and reference identity. Invalid input
    raises INVALID_ARGUMENT before mutation; target lookup remains separate.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.
        designConfigurationVLNV: Vendor, library, name, and version for the reference.

    Returns:
        True when the reference is set.

    Raises:
        TgiError: With INVALID_ID for an invalid handle or INVALID_ARGUMENT for an invalid VLNV.

    Section: F.7.56.24.
    """
    dci = _require(_resolve_design_config_instantiation(designConfigurationInstantiationID))
    parts = _validated_vlnv(designConfigurationVLNV)
    ref = dci.design_configuration_ref
    if ref is None:
        ref = ConfigurableLibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])
        dci.design_configuration_ref = ref
    else:
        ref.vendor, ref.library, ref.name, ref.version = parts
    register_parent(ref, dci, ("design_configuration_ref",), "single")
    return True


def setDesignConfigurationInstantiationLanguage(designConfigurationInstantiationID: str, language: str) -> bool:
    """Set generated language source text, preserving existing strict metadata.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.
        language: Nonempty language string to set.

    Returns:
        True when language is set.

    Section: F.7.56.25. Invalid text raises INVALID_ARGUMENT before mutation.
    """
    inst = _require(_resolve_design_config_instantiation(designConfigurationInstantiationID))
    if not isinstance(language, str) or not language.strip():
        raise TgiError("Expected a nonempty language string", TgiFaultCode.INVALID_ARGUMENT)
    if inst.language is None:
        inst.language = LanguageType(value=language)
    else:
        inst.language.value = language
    register_parent(inst.language, inst, ("language",), "single")
    return True


def setDesignInstantiationDesignRef(designInstantiationID: str, designVLNV: tuple[str, str, str, str]) -> bool:
    """Set designRef VLNV while preserving an existing parsed node handle.

    Validate all four nonempty VLNV strings before changing the generated reference.
    If a reference node already exists, update it in place so its handle stays valid.

    Args:
        designInstantiationID: Handle to a designInstantiation element.
        designVLNV: Vendor, library, name, and version for the design reference.

    Returns:
        True when the reference is set.

    Raises:
        TgiError: With INVALID_ID for an invalid handle or INVALID_ARGUMENT for an invalid VLNV.

    Section: F.7.56.26.
    """
    inst = resolve_handle(designInstantiationID)
    if not isinstance(inst, DesignInstantiationType):
        raise TgiError("Invalid designInstantiation handle", TgiFaultCode.INVALID_ID)
    parts = _validated_vlnv(designVLNV)
    ref = inst.design_ref
    if ref is None:
        ref = ConfigurableLibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])
        inst.design_ref = ref
    else:
        ref.vendor, ref.library, ref.name, ref.version = parts
    register_parent(ref, inst, ("design_ref",), "single")
    return True
