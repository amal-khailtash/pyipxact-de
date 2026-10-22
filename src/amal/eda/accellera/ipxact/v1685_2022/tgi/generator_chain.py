"""Generator-chain TGI functions for IEEE 1685-2022 Annex F.7.51 and F.7.52.

The BASE operations traverse generator-chain groups, choices, generators,
selectors, and group selectors. The EXTENDED operations edit those same
schema objects. Child handles follow the generated IP-XACT 1685-2022 model in
``org.accellera.ipxact.v1685_2022.generator_chain``: the three selector and
generator alternatives share one ordered mixed-content list, while a
generator-chain selector stores either a group selector or a library
reference in a single choice field.

Mutations validate arguments and ownership before changing the model. A bad
handle raises :class:`TgiError` with ``INVALID_ID``; invalid values or edits
that would violate required schema content raise ``INVALID_ARGUMENT``.
Resolved generator-chain references use the TGI VLNV registry, as required
for the Annex F ByID operation.
"""

# ruff: noqa: I001
from org.accellera.ipxact.v1685_2022.choices import Choices
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.generator import Generator
from org.accellera.ipxact.v1685_2022.generator_chain import GeneratorChain as SchemaGeneratorChain
from org.accellera.ipxact.v1685_2022.generator_selector_type import GeneratorSelectorType
from org.accellera.ipxact.v1685_2022.group_selector import GroupSelector
from org.accellera.ipxact.v1685_2022.ipxact_uri import IpxactUri

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
    # BASE (F.7.51)
    "getComponentGeneratorSelectorGroupSelectorID",
    "getGeneratorChainChainGroupIDs",
    "getGeneratorChainChoiceIDs",
    "getGeneratorChainComponentGeneratorSelectorIDs",
    "getGeneratorChainGeneratorChainSelectorIDs",
    "getGeneratorChainGeneratorIDs",
    "getGeneratorChainSelectorGeneratorChainRefByID",
    "getGeneratorChainSelectorGeneratorChainRefByVLNV",
    "getGeneratorChainSelectorGroupSelectorID",
    "getGroupSelectorNameIDs",
    "getGroupSelectorSelectionNames",
    "getGroupSelectorSelectionOperator",
    # EXTENDED (F.7.52)
    "addGeneratorChainChainGroup",
    "addGeneratorChainChoice",
    "addGeneratorChainComponentGeneratorSelector",
    "addGeneratorChainGenerator",
    "addGeneratorChainGeneratorChainSelector",
    "addGroupSelectorName",
    "removeGeneratorChainChainGroup",
    "removeGeneratorChainChoice",
    "removeGeneratorChainComponentGeneratorSelector",
    "removeGeneratorChainGenerator",
    "removeGeneratorChainGeneratorChainSelector",
    "removeGroupSelectorName",
    "setComponentGeneratorSelectorGroupSelector",
    "setGeneratorChainSelectorGeneratorChainRef",
    "setGeneratorChainSelectorGroupSelector",
]

_MIXED_CHILDREN = "generator_chain_selector_or_component_generator_selector_or_generator"
_CHAIN_GROUP_PATH = ("chain_group",)
_CHOICE_PATH = ("choices", "choice")
_GROUP_NAME_PATH = ("name",)
_CHAIN_SELECTOR_PATH = (_MIXED_CHILDREN,)


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _resolve_chain(chain_id: str) -> SchemaGeneratorChain | None:
    obj = resolve_handle(chain_id)
    return obj if isinstance(obj, SchemaGeneratorChain) else None


def _resolve_chain_selector(selector_id: str) -> SchemaGeneratorChain.GeneratorChainSelector | None:
    obj = resolve_handle(selector_id)
    return obj if isinstance(obj, SchemaGeneratorChain.GeneratorChainSelector) else None


def _resolve_component_selector(selector_id: str) -> GeneratorSelectorType | None:
    obj = resolve_handle(selector_id)
    return obj if isinstance(obj, GeneratorSelectorType) else None


def _resolve_group_selector(group_selector_id: str) -> GroupSelector | None:
    obj = resolve_handle(group_selector_id)
    return obj if isinstance(obj, GroupSelector) else None


def _resolve_group_name(name_id: str) -> GroupSelector.Name | None:
    obj = resolve_handle(name_id)
    return obj if isinstance(obj, GroupSelector.Name) else None


def _resolve_choice(choice_id: str) -> Choices.Choice | None:
    obj = resolve_handle(choice_id)
    return obj if isinstance(obj, Choices.Choice) else None


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TgiError(f"{label} must be a string", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _string_list(values: object, label: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(values, (list, tuple)) or (nonempty and not values):
        requirement = "a nonempty string list" if nonempty else "a string list"
        raise TgiError(f"{label} must be {requirement}", TgiFaultCode.INVALID_ARGUMENT)
    if any(not isinstance(value, str) for value in values):
        raise TgiError(f"{label} must contain only strings", TgiFaultCode.INVALID_ARGUMENT)
    return list(values)


def _chain_children(chain: SchemaGeneratorChain, kind: type) -> list[str]:
    children = [child for child in getattr(chain, _MIXED_CHILDREN) if isinstance(child, kind)]
    for child in children:
        register_parent(child, chain, _CHAIN_SELECTOR_PATH, "list")
    return [get_handle(child) for child in children]


def _owned_child(
    child_id: str,
    child: object | None,
    parent_type: type,
    path: tuple[str, ...],
) -> tuple[object, object]:
    """Require a typed handle with the expected registered model owner."""
    if child is None:
        raise TgiError("Invalid child handle", TgiFaultCode.INVALID_ID)
    info = get_parent_info(child_id)
    parent = resolve_handle(info.parent_handle) if info is not None else None
    if info is None or not isinstance(parent, parent_type) or info.path != path or info.container != "list":
        raise TgiError("Handle is not owned by the expected IP-XACT element", TgiFaultCode.INVALID_ID)
    return child, parent


def _detach_owned(child_id: str, child: object | None, parent_type: type, path: tuple[str, ...]) -> bool:
    _owned_child(child_id, child, parent_type, path)
    if not detach_child_by_handle(child_id):
        raise TgiError("Child handle is no longer attached to its owner", TgiFaultCode.INVALID_ID)
    return True


def _replace_choice_child(owner: object, attribute: str, path: tuple[str, ...], new_child: object) -> None:
    old_child = getattr(owner, attribute)
    if old_child is not None:
        register_parent(old_child, owner, path, "single")
        if not detach_child_by_handle(get_handle(old_child)):
            raise TgiError("Existing child could not be replaced", TgiFaultCode.INVALID_ID)
    setattr(owner, attribute, new_child)
    register_parent(new_child, owner, path, "single")


# ---------------------------------------------------------------------------
# BASE (F.7.51)
# ---------------------------------------------------------------------------


def getComponentGeneratorSelectorGroupSelectorID(componentGeneratorSelectorID: str) -> str | None:
    """Return the component selector's groupSelector handle.

    Args:
        componentGeneratorSelectorID: Handle to a componentGeneratorSelector.

    Returns:
        The groupSelector handle, or ``None`` if the optional object is absent.

    Section: IEEE 1685-2022 Annex F.7.51.1.
    """
    selector = _resolve_component_selector(componentGeneratorSelectorID)
    if selector is None:
        raise TgiError("Invalid componentGeneratorSelector handle", TgiFaultCode.INVALID_ID)
    group_selector = selector.group_selector
    if group_selector is None:
        return None
    register_parent(group_selector, selector, ("group_selector",), "single")
    return get_handle(group_selector)


def getGeneratorChainChainGroupIDs(generatorChainID: str) -> list[str]:
    """Return handles of all chainGroup elements in document order.

    Args:
        generatorChainID: Handle to a generatorChain.

    Returns:
        Handles to the chainGroup elements.

    Section: IEEE 1685-2022 Annex F.7.51.2.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    for child in chain.chain_group:
        register_parent(child, chain, _CHAIN_GROUP_PATH, "list")
    return [get_handle(child) for child in chain.chain_group]


def getGeneratorChainChoiceIDs(generatorChainID: str) -> list[str]:
    """Return handles of all choices defined by a generatorChain.

    Args:
        generatorChainID: Handle to a generatorChain.

    Returns:
        Handles to the choice elements, or an empty list when choices is absent.

    Section: IEEE 1685-2022 Annex F.7.51.3.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    if chain.choices is None:
        return []
    for child in chain.choices.choice:
        register_parent(child, chain, _CHOICE_PATH, "list")
    return [get_handle(child) for child in chain.choices.choice]


def getGeneratorChainComponentGeneratorSelectorIDs(generatorChainID: str) -> list[str]:
    """Return componentGeneratorSelector handles in document order.

    Args:
        generatorChainID: Handle to a generatorChain.

    Returns:
        Handles to the componentGeneratorSelector elements.

    Section: IEEE 1685-2022 Annex F.7.51.4.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    return _chain_children(chain, GeneratorSelectorType)


def getGeneratorChainGeneratorChainSelectorIDs(generatorChainID: str) -> list[str]:
    """Return generatorChainSelector handles in document order.

    Args:
        generatorChainID: Handle to a generatorChain.

    Returns:
        Handles to the generatorChainSelector elements.

    Section: IEEE 1685-2022 Annex F.7.51.5.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    return _chain_children(chain, SchemaGeneratorChain.GeneratorChainSelector)


def getGeneratorChainGeneratorIDs(generatorChainID: str) -> list[str]:
    """Return generator handles in document order.

    Args:
        generatorChainID: Handle to a generatorChain.

    Returns:
        Handles to the generator elements.

    Section: IEEE 1685-2022 Annex F.7.51.6.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    return _chain_children(chain, Generator)


def getGeneratorChainSelectorGeneratorChainRefByID(generatorChainSelectorID: str) -> str:
    """Resolve a selector's generatorChainRef through the VLNV registry.

    Args:
        generatorChainSelectorID: Handle to a generatorChainSelector.

    Returns:
        Handle to the registered generatorChain document referenced by the selector.

    Raises:
        TgiError: ``NOT_FOUND`` if the selector has no reference or its target is not registered.

    Section: IEEE 1685-2022 Annex F.7.51.7.
    """
    selector = _resolve_chain_selector(generatorChainSelectorID)
    if selector is None:
        raise TgiError("Invalid generatorChainSelector handle", TgiFaultCode.INVALID_ID)
    ref = selector.group_selector_or_generator_chain_ref
    if not isinstance(ref, ConfigurableLibraryRefType):
        raise TgiError("generatorChainRef is absent", TgiFaultCode.NOT_FOUND)
    vlnv = (ref.vendor, ref.library, ref.name, ref.version)
    target_id = registry.get_id(vlnv)
    target = resolve_handle(target_id) if target_id is not None else None
    if not isinstance(target, SchemaGeneratorChain):
        raise TgiError("generatorChainRef target is missing or has the wrong type", TgiFaultCode.NOT_FOUND)
    return get_handle(target)


def getGeneratorChainSelectorGeneratorChainRefByVLNV(
    generatorChainSelectorID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return the stored VLNV tuple of a selector's generatorChainRef.

    Args:
        generatorChainSelectorID: Handle to a generatorChainSelector.

    Returns:
        The vendor, library, name, and version strings, or four ``None`` values when absent.

    Section: IEEE 1685-2022 Annex F.7.51.8.
    """
    selector = _resolve_chain_selector(generatorChainSelectorID)
    if selector is None:
        raise TgiError("Invalid generatorChainSelector handle", TgiFaultCode.INVALID_ID)
    ref = selector.group_selector_or_generator_chain_ref
    if not isinstance(ref, ConfigurableLibraryRefType):
        return (None, None, None, None)
    return (ref.vendor, ref.library, ref.name, ref.version)


def getGeneratorChainSelectorGroupSelectorID(generatorChainSelectorID: str) -> str | None:
    """Return the groupSelector handle selected by a generatorChainSelector.

    Args:
        generatorChainSelectorID: Handle to a generatorChainSelector.

    Returns:
        The groupSelector handle, or ``None`` when the selector contains a generatorChainRef.

    Section: IEEE 1685-2022 Annex F.7.51.9.
    """
    selector = _resolve_chain_selector(generatorChainSelectorID)
    if selector is None:
        raise TgiError("Invalid generatorChainSelector handle", TgiFaultCode.INVALID_ID)
    group_selector = selector.group_selector_or_generator_chain_ref
    if not isinstance(group_selector, GroupSelector):
        return None
    register_parent(group_selector, selector, ("group_selector_or_generator_chain_ref",), "single")
    return get_handle(group_selector)


def getGroupSelectorNameIDs(groupSelectorID: str) -> list[str]:
    """Return handles of all Name elements in a groupSelector.

    Args:
        groupSelectorID: Handle to a groupSelector.

    Returns:
        Handles to the Name elements in their schema order.

    Section: IEEE 1685-2022 Annex F.7.51.10.
    """
    group_selector = _resolve_group_selector(groupSelectorID)
    if group_selector is None:
        raise TgiError("Invalid groupSelector handle", TgiFaultCode.INVALID_ID)
    for child in group_selector.name:
        register_parent(child, group_selector, _GROUP_NAME_PATH, "list")
    return [get_handle(child) for child in group_selector.name]


def getGroupSelectorSelectionNames(groupSelectorID: str) -> list[str]:
    """Return the selected generator or generator-chain group names.

    Args:
        groupSelectorID: Handle to a groupSelector.

    Returns:
        The string values of its Name elements.

    Section: IEEE 1685-2022 Annex F.7.51.11.
    """
    group_selector = _resolve_group_selector(groupSelectorID)
    if group_selector is None:
        raise TgiError("Invalid groupSelector handle", TgiFaultCode.INVALID_ID)
    return [child.value for child in group_selector.name]


def getGroupSelectorSelectionOperator(groupSelectorID: str) -> str:
    """Return the selector's multiple-group operator.

    Args:
        groupSelectorID: Handle to a groupSelector.

    Returns:
        ``"and"`` or ``"or"``; the generated model supplies the schema default ``"or"``.

    Section: IEEE 1685-2022 Annex F.7.51.12.
    """
    group_selector = _resolve_group_selector(groupSelectorID)
    if group_selector is None:
        raise TgiError("Invalid groupSelector handle", TgiFaultCode.INVALID_ID)
    operator = group_selector.multiple_group_selection_operator
    return operator.value


# ---------------------------------------------------------------------------
# EXTENDED (F.7.52)
# ---------------------------------------------------------------------------


def addGeneratorChainChainGroup(generatorChainID: str, group: str) -> bool:
    """Append a chainGroup to a generatorChain.

    Args:
        generatorChainID: Handle to a generatorChain.
        group: Name identifying the generator-chain group.

    Returns:
        ``True`` after adding the chainGroup.

    Section: IEEE 1685-2022 Annex F.7.52.1.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    value = _string(group, "group")
    child = SchemaGeneratorChain.ChainGroup(value=value)
    chain.chain_group.append(child)
    register_parent(child, chain, _CHAIN_GROUP_PATH, "list")
    return True


def addGeneratorChainChoice(generatorChainID: str, name: str, enumerations: list[str]) -> str:
    """Add a choice with its required enumeration values.

    Args:
        generatorChainID: Handle to a generatorChain.
        name: Choice name used by ``ipxact:choiceRef``.
        enumerations: One or more legal expression strings for this choice.

    Returns:
        Handle to the created choice.

    Section: IEEE 1685-2022 Annex F.7.52.2.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    choice_name = _string(name, "name")
    values = _string_list(enumerations, "enumerations")
    child = Choices.Choice(
        name=choice_name,
        enumeration=[Choices.Choice.Enumeration(value=value) for value in values],
    )
    choices = chain.choices if chain.choices is not None else Choices()
    choices.choice.append(child)
    if chain.choices is None:
        chain.choices = choices
    register_parent(child, chain, _CHOICE_PATH, "list")
    return get_handle(child)


def addGeneratorChainComponentGeneratorSelector(generatorChainID: str, name: str) -> str:
    """Add a componentGeneratorSelector selecting one named group.

    Args:
        generatorChainID: Handle to a generatorChain.
        name: Generator group name placed in the selector's groupSelector.

    Returns:
        Handle to the created componentGeneratorSelector.

    Section: IEEE 1685-2022 Annex F.7.52.3.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    group_name = _string(name, "name")
    group_selector = GroupSelector(name=[GroupSelector.Name(value=group_name)])
    child = GeneratorSelectorType(group_selector=group_selector)
    getattr(chain, _MIXED_CHILDREN).append(child)
    register_parent(child, chain, _CHAIN_SELECTOR_PATH, "list")
    register_parent(group_selector, child, ("group_selector",), "single")
    return get_handle(child)


def addGeneratorChainGenerator(generatorChainID: str, name: str, generatorExecutable: str) -> str:
    """Add a generator with its required name and executable URI.

    Args:
        generatorChainID: Handle to a generatorChain.
        name: Name identifying the generator.
        generatorExecutable: URI for the generator executable.

    Returns:
        Handle to the created generator.

    Section: IEEE 1685-2022 Annex F.7.52.4.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    generator_name = _string(name, "name")
    executable = _string(generatorExecutable, "generatorExecutable")
    child = Generator(name=generator_name, generator_exe=IpxactUri(value=executable))
    getattr(chain, _MIXED_CHILDREN).append(child)
    register_parent(child, chain, _CHAIN_SELECTOR_PATH, "list")
    return get_handle(child)


def addGeneratorChainGeneratorChainSelector(generatorChainID: str, name: str) -> str:
    """Add a generatorChainSelector with a one-name groupSelector.

    Args:
        generatorChainID: Handle to a generatorChain.
        name: Generator-chain group name selected by the new selector.

    Returns:
        Handle to the created generatorChainSelector.

    Section: IEEE 1685-2022 Annex F.7.52.5.
    """
    chain = _resolve_chain(generatorChainID)
    if chain is None:
        raise TgiError("Invalid generatorChain handle", TgiFaultCode.INVALID_ID)
    group_name = _string(name, "name")
    group_selector = GroupSelector(name=[GroupSelector.Name(value=group_name)])
    child = SchemaGeneratorChain.GeneratorChainSelector(group_selector_or_generator_chain_ref=group_selector)
    getattr(chain, _MIXED_CHILDREN).append(child)
    register_parent(child, chain, _CHAIN_SELECTOR_PATH, "list")
    register_parent(group_selector, child, ("group_selector_or_generator_chain_ref",), "single")
    return get_handle(child)


def addGroupSelectorName(groupSelectorID: str, name: str) -> str:
    """Append a Name element to a groupSelector.

    Args:
        groupSelectorID: Handle to a groupSelector.
        name: Generator or generator-chain group name.

    Returns:
        Handle to the created Name element.

    Section: IEEE 1685-2022 Annex F.7.52.6.
    """
    group_selector = _resolve_group_selector(groupSelectorID)
    if group_selector is None:
        raise TgiError("Invalid groupSelector handle", TgiFaultCode.INVALID_ID)
    value = _string(name, "name")
    child = GroupSelector.Name(value=value)
    group_selector.name.append(child)
    register_parent(child, group_selector, _GROUP_NAME_PATH, "list")
    return get_handle(child)


def removeGeneratorChainChainGroup(chainGroupID: str) -> bool:
    """Remove an owned chainGroup and invalidate its handle.

    Args:
        chainGroupID: Handle to a chainGroup element.

    Returns:
        ``True`` when the element was removed.

    Raises:
        TgiError: If the handle is invalid or is not owned by a generatorChain.

    Section: IEEE 1685-2022 Annex F.7.52.7.
    """
    child = resolve_handle(chainGroupID)
    return _detach_owned(
        chainGroupID,
        child if isinstance(child, SchemaGeneratorChain.ChainGroup) else None,
        SchemaGeneratorChain,
        _CHAIN_GROUP_PATH,
    )


def removeGeneratorChainChoice(choiceID: str) -> bool:
    """Remove an owned choice and clear an empty optional choices container.

    Args:
        choiceID: Handle to a choice element.

    Returns:
        ``True`` when the element was removed.

    Raises:
        TgiError: If the handle is invalid or is not owned by a generatorChain.

    Section: IEEE 1685-2022 Annex F.7.52.8.
    """
    child = _resolve_choice(choiceID)
    _, parent = _owned_child(choiceID, child, SchemaGeneratorChain, _CHOICE_PATH)
    chain = parent
    if not detach_child_by_handle(choiceID):
        raise TgiError("Choice is no longer attached to its generatorChain", TgiFaultCode.INVALID_ID)
    if chain.choices is not None and not chain.choices.choice:
        chain.choices = None
    return True


def removeGeneratorChainComponentGeneratorSelector(componentGeneratorSelectorID: str) -> bool:
    """Remove an owned componentGeneratorSelector and its descendants.

    Args:
        componentGeneratorSelectorID: Handle to a componentGeneratorSelector.

    Returns:
        ``True`` when the element was removed.

    Raises:
        TgiError: If the handle is invalid or is not owned by a generatorChain.

    Section: IEEE 1685-2022 Annex F.7.52.9.
    """
    child = _resolve_component_selector(componentGeneratorSelectorID)
    return _detach_owned(componentGeneratorSelectorID, child, SchemaGeneratorChain, _CHAIN_SELECTOR_PATH)


def removeGeneratorChainGenerator(generatorID: str) -> bool:
    """Remove an owned generator and invalidate its handle.

    Args:
        generatorID: Handle to a generator element.

    Returns:
        ``True`` when the element was removed.

    Raises:
        TgiError: If the handle is invalid or is not owned by a generatorChain.

    Section: IEEE 1685-2022 Annex F.7.52.10.
    """
    child = resolve_handle(generatorID)
    return _detach_owned(
        generatorID, child if isinstance(child, Generator) else None, SchemaGeneratorChain, _CHAIN_SELECTOR_PATH
    )


def removeGeneratorChainGeneratorChainSelector(generatorChainSelectorID: str) -> bool:
    """Remove an owned generatorChainSelector and its descendants.

    Args:
        generatorChainSelectorID: Handle to a generatorChainSelector.

    Returns:
        ``True`` when the element was removed.

    Raises:
        TgiError: If the handle is invalid or is not owned by a generatorChain.

    Section: IEEE 1685-2022 Annex F.7.52.11.
    """
    child = _resolve_chain_selector(generatorChainSelectorID)
    return _detach_owned(generatorChainSelectorID, child, SchemaGeneratorChain, _CHAIN_SELECTOR_PATH)


def removeGroupSelectorName(groupSelectorNameID: str) -> bool:
    """Remove a Name while retaining at least one required group selection.

    Args:
        groupSelectorNameID: Handle to a Name child of a groupSelector.

    Returns:
        ``True`` when the element was removed.

    Raises:
        TgiError: If the handle is invalid, has the wrong owner, or removing it would leave
            its required groupSelector without a name.

    Section: IEEE 1685-2022 Annex F.7.52.12.
    """
    child = _resolve_group_name(groupSelectorNameID)
    _, parent = _owned_child(groupSelectorNameID, child, GroupSelector, _GROUP_NAME_PATH)
    if len(parent.name) <= 1:
        raise TgiError("A groupSelector must contain at least one name", TgiFaultCode.INVALID_ARGUMENT)
    return _detach_owned(groupSelectorNameID, child, GroupSelector, _GROUP_NAME_PATH)


def setComponentGeneratorSelectorGroupSelector(componentGeneratorSelectorID: str, names: list[str]) -> bool:
    """Replace a componentGeneratorSelector's groupSelector.

    Args:
        componentGeneratorSelectorID: Handle to a componentGeneratorSelector.
        names: One or more generator group names.

    Returns:
        ``True`` after setting the groupSelector.

    Raises:
        TgiError: If the handle is invalid or names is empty or contains non-strings.

    Section: IEEE 1685-2022 Annex F.7.52.13.
    """
    selector = _resolve_component_selector(componentGeneratorSelectorID)
    if selector is None:
        raise TgiError("Invalid componentGeneratorSelector handle", TgiFaultCode.INVALID_ID)
    values = _string_list(names, "names")
    child = GroupSelector(name=[GroupSelector.Name(value=value) for value in values])
    _replace_choice_child(selector, "group_selector", ("group_selector",), child)
    return True


def setGeneratorChainSelectorGeneratorChainRef(
    generatorChainSelectorID: str,
    generatorChainVLNV: tuple[str, str, str, str],
) -> bool:
    """Set a generatorChainSelector's generatorChainRef VLNV.

    Args:
        generatorChainSelectorID: Handle to a generatorChainSelector.
        generatorChainVLNV: Four nonempty strings: vendor, library, name, and version.

    Returns:
        ``True`` after setting the reference.

    Raises:
        TgiError: If the selector handle is invalid or the VLNV is malformed.

    Section: IEEE 1685-2022 Annex F.7.52.14.
    """
    selector = _resolve_chain_selector(generatorChainSelectorID)
    if selector is None:
        raise TgiError("Invalid generatorChainSelector handle", TgiFaultCode.INVALID_ID)
    values = _string_list(generatorChainVLNV, "generatorChainVLNV")
    if len(values) != 4 or any(not value.strip() for value in values):
        raise TgiError("generatorChainVLNV must contain four nonempty strings", TgiFaultCode.INVALID_ARGUMENT)
    child = ConfigurableLibraryRefType(vendor=values[0], library=values[1], name=values[2], version=values[3])
    _replace_choice_child(
        selector,
        "group_selector_or_generator_chain_ref",
        ("group_selector_or_generator_chain_ref",),
        child,
    )
    return True


def setGeneratorChainSelectorGroupSelector(generatorChainSelectorID: str, names: list[str]) -> bool:
    """Set a generatorChainSelector's groupSelector names.

    Args:
        generatorChainSelectorID: Handle to a generatorChainSelector.
        names: One or more generator-chain group names.

    Returns:
        ``True`` after setting the groupSelector.

    Raises:
        TgiError: If the selector handle is invalid or names is empty or contains non-strings.

    Section: IEEE 1685-2022 Annex F.7.52.15.
    """
    selector = _resolve_chain_selector(generatorChainSelectorID)
    if selector is None:
        raise TgiError("Invalid generatorChainSelector handle", TgiFaultCode.INVALID_ID)
    values = _string_list(names, "names")
    child = GroupSelector(name=[GroupSelector.Name(value=value) for value in values])
    _replace_choice_child(
        selector,
        "group_selector_or_generator_chain_ref",
        ("group_selector_or_generator_chain_ref",),
        child,
    )
    return True
