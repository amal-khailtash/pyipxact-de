"""Resolution support for the BASE Element attribute ``*ByID`` functions.

Annex F F.7.43.2, .4, .9, .14, .16, .19, .24, .26, .40, .53, .65, .66,
.85, .87, .93, .97, .101, .105, and .120 return handles to generated model
objects. This helper resolves the local IP-XACT reference value inside the
registered document containing the source element. References to component
ports and interfaces follow the component-instance VLNV through the TGI
registry; no files are loaded as a side effect.
"""

from collections.abc import Iterator
from dataclasses import fields, is_dataclass
from typing import Any

from .core import TgiError, TgiFaultCode, get_handle, register_parent, registry, resolve_handle

# For each XML attribute name, list the generated schema-module and class
# name which represents its destination element. These predicates deliberately
# distinguish similarly named generated types such as views and banks.
_TARGET_TYPES: dict[str, tuple[tuple[str, str], ...]] = {
    "addressBlockRef": (("address_block", "AddressBlock"),),
    "addressSpaceRef": (("address_spaces", "AddressSpace"),),
    "alternateRegisterRef": (("alternate_registers", "AlternateRegister"),),
    "bankRef": (
        ("bank", "Bank"),
        ("address_bank_type", "Bank"),
        ("address_bank_definition_type", "Bank"),
        ("bank_definitions", "Bank"),
        ("banked_bank_type", "Bank"),
        ("banked_definition_bank_type", "Bank"),
        ("memory_remap_definition_type", "Bank"),
    ),
    "busRef": (("bus_interface", "BusInterface"),),
    "choiceRef": (("choices", "Choice"),),
    "componentInstanceRef": (("component_instance", "ComponentInstance"),),
    "componentRef": (("component_instance", "ComponentInstance"),),
    "fieldRef": (("field_definitions", "FieldDefinition"), ("field_type", "FieldType")),
    "initiatorRef": (("bus_interface", "BusInterface"),),
    "memoryMapRef": (("memory_map_type", "MemoryMapType"),),
    "memoryRemapRef": (("memory_remap", "MemoryRemap"),),
    "portRef": (("port", "Port"),),
    "powerDomainRef": (("component_type", "PowerDomain"),),
    "registerFileRef": (("register_file", "RegisterFile"),),
    "resetTypeRef": (("component_type", "ResetType"),),
    "segmentRef": (("address_spaces", "Segment"),),
    "subPortRef": (("sub_port_type", "SubPortType"),),
    "viewRef": (("model_type", "View"),),
}

_QUALIFIER_TYPES: dict[str, tuple[tuple[str, str], ...]] = {
    "address_block_ref": _TARGET_TYPES["addressBlockRef"],
    "address_space_ref": _TARGET_TYPES["addressSpaceRef"],
    "alternate_register_ref": _TARGET_TYPES["alternateRegisterRef"],
    "bank_ref": _TARGET_TYPES["bankRef"],
    "choice_ref": _TARGET_TYPES["choiceRef"],
    "memory_map_ref": _TARGET_TYPES["memoryMapRef"],
    "memory_remap_ref": _TARGET_TYPES["memoryRemapRef"],
    "register_file_ref": _TARGET_TYPES["registerFileRef"],
    "reset_type_ref": _TARGET_TYPES["resetTypeRef"],
    "segment_ref": _TARGET_TYPES["segmentRef"],
    "register_ref": (
        ("address_block_type", "Register"),
        ("register_file", "Register"),
        ("register_file_definitions", "Register"),
        ("banked_block_type", "Register"),
    ),
}

_QUALIFIER_XML_NAMES = {
    "address_block_ref": "addressBlockRef",
    "address_space_ref": "addressSpaceRef",
    "alternate_register_ref": "alternateRegisterRef",
    "bank_ref": "bankRef",
    "choice_ref": "choiceRef",
    "memory_map_ref": "memoryMapRef",
    "memory_remap_ref": "memoryRemapRef",
    "register_file_ref": "registerFileRef",
    "reset_type_ref": "resetTypeRef",
    "segment_ref": "segmentRef",
    "register_ref": "registerRef",
}

_VALUE_FIELDS: dict[str, tuple[str, ...]] = {
    "addressBlockRef": ("address_block_ref",),
    "addressSpaceRef": ("address_space_ref",),
    "alternateRegisterRef": ("alternate_register_ref",),
    "bankRef": ("bank_ref",),
    "busRef": ("bus_ref",),
    "choiceRef": ("choice_ref",),
    "componentInstanceRef": ("component_instance_ref",),
    # Annex F F.7.43.26 is the ``componentRef`` attribute on the
    # design-configuration ``interfaceRef`` model; it names a component
    # instance in the associated design.
    "componentRef": ("component_ref",),
    "fieldRef": ("field_ref",),
    "initiatorRef": ("initiator_ref",),
    "memoryMapRef": ("memory_map_ref",),
    "memoryRemapRef": ("memory_remap_ref",),
    "portRef": ("port_ref",),
    "powerDomainRef": ("power_domain_ref", "value"),
    "registerFileRef": ("register_file_ref",),
    "resetTypeRef": ("reset_type_ref",),
    "registerRef": ("register_ref",),
    "segmentRef": ("segment_ref",),
    "subPortRef": ("sub_port_ref",),
    "viewRef": ("view_ref", "value"),
}


def _children(obj: object) -> Iterator[object]:
    """Yield generated-model children without descending into scalar values."""
    if not is_dataclass(obj) or isinstance(obj, type):
        return
    for item in fields(obj):
        value = getattr(obj, item.name)
        if is_dataclass(value) and not isinstance(value, type):
            yield value
        elif isinstance(value, (list, tuple)):
            yield from (child for child in value if is_dataclass(child) and not isinstance(child, type))


def _walk(root: object) -> Iterator[tuple[object, tuple[object, ...]]]:
    """Yield (object, ancestor path) for each generated dataclass once."""
    pending = [(root, ())]
    seen: set[int] = set()
    while pending:
        obj, ancestors = pending.pop()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        yield obj, ancestors
        pending.extend((child, (*ancestors, obj)) for child in _children(obj))


def _contains(root: Any, wanted: Any) -> bool:
    return any(obj is wanted for obj, _ in _walk(root))


def _root_for(element: Any) -> Any:
    """Find the registered model root containing ``element`` if available."""
    roots = [
        resolve_handle(root_id)
        for root_id in registry.iter_by_predicate(lambda _root: True)
    ]
    containing = [root for root in roots if root is not None and _contains(root, element)]
    if len(containing) == 1:
        return containing[0]
    if len(containing) > 1:
        # A registered root can itself be nested in another registered root.
        # Prefer the smallest containing graph so same-name objects in another
        # registered design cannot participate in resolution.
        sizes = [(sum(1 for _ in _walk(root)), root) for root in containing]
        return min(sizes, key=lambda item: item[0])[1]
    # Parent links are registered incrementally by the TGI API. They provide a
    # useful local scope for edited subtrees even when no VLNV root is present.
    current = element
    seen: set[int] = set()
    from .core import get_parent_info

    while id(current) not in seen:
        seen.add(id(current))
        info = get_parent_info(get_handle(current))
        parent = resolve_handle(info.parent_handle) if info is not None else None
        if parent is None:
            break
        current = parent
    return current


def _reference_value(element: Any, xml_name: str) -> str | None:
    if xml_name == "viewRef":
        selected_view = getattr(element, "view", None)
        selected_name = getattr(selected_view, "view_ref", None)
        if isinstance(selected_name, str):
            return selected_name
    for field_name in _VALUE_FIELDS[xml_name]:
        value = getattr(element, field_name, None)
        if isinstance(value, str):
            return value
        if value is not None:
            wrapped = getattr(value, "value", None)
            if isinstance(wrapped, str):
                return wrapped
    return None


def _is_target(obj: Any, xml_name: str) -> bool:
    module = type(obj).__module__.rsplit(".", 1)[-1]
    name = type(obj).__name__
    return (module, name) in _TARGET_TYPES[xml_name]


def _is_qualified_target(obj: Any, target_types: tuple[tuple[str, str], ...]) -> bool:
    return (type(obj).__module__.rsplit(".", 1)[-1], type(obj).__name__) in target_types


def _model_name(obj: Any) -> str | None:
    """Read the IP-XACT name represented by a common generated model type."""
    value = getattr(obj, "name", None)
    if isinstance(value, str):
        return value
    for field_name in ("instance_name", "name"):
        child = getattr(obj, field_name, None)
        child_value = getattr(child, "value", None)
        if isinstance(child_value, str):
            return child_value
    return None


def _source_ancestors(root: Any, element: Any) -> tuple[Any, ...]:
    for obj, ancestors in _walk(root):
        if obj is element:
            return (*ancestors, obj)
    return (element,)


def _component_root_for_instance(root: Any, source_path: tuple[Any, ...]) -> Any | None:
    """Follow a component-instance reference to its registered Component, if present."""
    instance_name = next(
        (
            value
            for node in reversed(source_path)
            for value in (
                getattr(node, "component_instance_ref", None),
                getattr(node, "component_ref", None),
                getattr(getattr(node, "instance_name", None), "value", None),
            )
            if isinstance(value, str)
        ),
        None,
    )
    if instance_name is None:
        return None
    design_root = _design_root(root)
    instance = next(
        (
            obj
            for obj, _ in _walk(design_root)
            if type(obj).__name__ == "ComponentInstance" and _model_name(obj) == instance_name
        ),
        None,
    )
    ref = getattr(instance, "component_ref", None) if instance is not None else None
    vlnv = tuple(getattr(ref, part, None) for part in ("vendor", "library", "name", "version"))
    if any(not isinstance(part, str) or not part for part in vlnv):
        return None
    handle = registry.get_id(vlnv)
    target = resolve_handle(handle) if handle is not None else None
    if target is None or type(target).__name__ != "Component":
        return None
    return target


def _design_root(root: Any) -> Any:
    """Return the registered Design associated with a DesignConfiguration."""
    design_ref = getattr(root, "design_ref", None)
    design_vlnv = tuple(getattr(design_ref, part, None) for part in ("vendor", "library", "name", "version"))
    if all(isinstance(part, str) and part for part in design_vlnv):
        design_handle = registry.get_id(design_vlnv)
        registered_design = resolve_handle(design_handle) if design_handle is not None else None
        if registered_design is not None and type(registered_design).__name__ == "Design":
            return registered_design
    return root


def _context_root(root: Any, source_path: tuple[Any, ...], xml_name: str) -> Any:
    """Apply standard reference context for cross-component target types."""
    if xml_name == "componentRef":
        return _design_root(root)
    if xml_name in {"busRef", "portRef", "subPortRef", "viewRef"}:
        external = _component_root_for_instance(root, source_path)
        if external is not None:
            return external
        if _has_instance_reference_context(source_path):
            raise TgiError("Referenced component instance is unavailable", TgiFaultCode.NOT_FOUND)
    return root


def _has_instance_reference_context(source_path: tuple[Any, ...]) -> bool:
    return any(
        isinstance(getattr(node, field_name, None), str)
        for node in source_path
        for field_name in ("component_instance_ref", "component_ref")
    ) or any(isinstance(getattr(getattr(node, "instance_name", None), "value", None), str) for node in source_path)


def _shared_ancestor_score(source_path: tuple[Any, ...], target_path: tuple[Any, ...]) -> int:
    score = 0
    for source, target in zip(source_path, target_path, strict=False):
        if source is not target:
            break
        score += 1
    return score


def _reference_qualifiers(source_path: tuple[Any, ...]) -> list[tuple[tuple[tuple[str, str], ...], str]]:
    """Collect sibling local refs that constrain a hierarchical target path."""
    qualifiers: list[tuple[tuple[tuple[str, str], ...], str]] = []
    for node in source_path:
        for field_name, target_types in _QUALIFIER_TYPES.items():
            value = getattr(node, field_name, None)
            values = value if isinstance(value, (list, tuple)) else (value,)
            xml_name = _QUALIFIER_XML_NAMES[field_name]
            for item in values:
                name = item if isinstance(item, str) else _reference_value(item, xml_name)
                if isinstance(name, str) and name.strip():
                    qualifiers.append((target_types, name))
    return qualifiers


def _matches_reference_context(
    obj: Any,
    ancestors: tuple[Any, ...],
    qualifiers: list[tuple[tuple[tuple[str, str], ...], str]],
) -> bool:
    lineage = (*ancestors, obj)
    for target_types, name in qualifiers:
        if any(
            _is_qualified_target(candidate, target_types) and _model_name(candidate) == name
            for candidate in lineage
        ):
            continue
        return False
    return True


def _register_target_owner(root: Any, target: Any) -> None:
    """Record the generated-model field that owns a returned target object."""
    for parent, _ in _walk(root):
        if not is_dataclass(parent) or isinstance(parent, type):
            continue
        for model_field in fields(parent):
            value = getattr(parent, model_field.name)
            if value is target:
                register_parent(target, parent, (model_field.name,), "single")
                return
            if isinstance(value, (list, tuple)) and any(child is target for child in value):
                register_parent(target, parent, (model_field.name,), "list")
                return


def _segment_candidates(
    root: Any, source_path: tuple[Any, ...], candidates: list[tuple[Any, tuple[Any, ...]]],
) -> list[tuple[Any, tuple[Any, ...]]]:
    """Restrict segment refs to the addressSpace named by the bridge initiator."""
    initiator_name = next(
        (
            value
            for node in reversed(source_path)
            if isinstance((value := getattr(node, "initiator_ref", None)), str)
        ),
        None,
    )
    if initiator_name is None:
        return candidates
    bus = next(
        (
            obj
            for obj, _ in _walk(root)
            if type(obj).__name__ == "BusInterface" and _model_name(obj) == initiator_name
        ),
        None,
    )
    if bus is None:
        raise TgiError(f"No busInterface named {initiator_name!r} was found", TgiFaultCode.NOT_FOUND)
    initiator = getattr(bus, "choice", None)
    address_space_ref = getattr(initiator, "address_space_ref", None)
    address_space_name = getattr(address_space_ref, "address_space_ref", None)
    if not isinstance(address_space_name, str):
        raise TgiError(
            f"Initiator busInterface {initiator_name!r} has no addressSpaceRef",
            TgiFaultCode.NOT_FOUND,
        )
    spaces = [
        obj
        for obj, _ in _walk(root)
        if _is_target(obj, "addressSpaceRef") and _model_name(obj) == address_space_name
    ]
    if not spaces:
        raise TgiError(f"No addressSpace named {address_space_name!r} was found", TgiFaultCode.NOT_FOUND)
    if len(spaces) > 1:
        raise TgiError(
            f"AddressSpace reference {address_space_name!r} is ambiguous",
            TgiFaultCode.INVALID_ARGUMENT,
        )
    space = spaces[0]
    return [pair for pair in candidates if any(ancestor is space for ancestor in pair[1])]


def _sub_port_target(root: Any, source_path: tuple[Any, ...], reference: str) -> Any | None:
    """Resolve one subPortReference along its ordered structured-port path."""
    port_ref = next(
        (
            value
            for node in reversed(source_path)
            if isinstance((value := getattr(node, "port_ref", None)), str)
        ),
        None,
    )
    if port_ref is None:
        return None
    target_root = _component_root_for_instance(root, source_path)
    if target_root is None:
        if _has_instance_reference_context(source_path):
            raise TgiError("Referenced component instance is unavailable", TgiFaultCode.NOT_FOUND)
        target_root = root
    ports = [
        obj
        for obj, _ in _walk(target_root)
        if _is_target(obj, "portRef") and _model_name(obj) == port_ref
    ]
    if len(ports) != 1:
        if not ports:
            raise TgiError(f"No port target named {port_ref!r} was found", TgiFaultCode.NOT_FOUND)
        raise TgiError(f"Port reference {port_ref!r} is ambiguous", TgiFaultCode.INVALID_ARGUMENT)

    source = source_path[-1]
    owner = source_path[-2] if len(source_path) > 1 else None
    path_refs = getattr(owner, "sub_port_reference", None)
    if not isinstance(path_refs, (list, tuple)) or not any(candidate is source for candidate in path_refs):
        return None
    through_index = next(index for index, candidate in enumerate(path_refs) if candidate is source)

    current: Any = ports[0]
    for index, path_ref in enumerate(path_refs[: through_index + 1]):
        structure = getattr(current, "wire_or_transactional_or_structured", None)
        if structure is None:
            structure = getattr(current, "wire_or_structured", None)
        sub_ports = getattr(getattr(structure, "sub_ports", None), "sub_port", None)
        matches = [
            candidate
            for candidate in sub_ports or ()
            if _is_target(candidate, "subPortRef")
            and _model_name(candidate) == _reference_value(path_ref, "subPortRef")
        ]
        if len(matches) != 1:
            name = _reference_value(path_ref, "subPortRef")
            if not matches:
                raise TgiError(f"No subPort target named {name!r} was found", TgiFaultCode.NOT_FOUND)
            raise TgiError(f"SubPort reference {name!r} is ambiguous", TgiFaultCode.INVALID_ARGUMENT)
        current = matches[0]
        if index == through_index:
            return current if _reference_value(path_ref, "subPortRef") == reference else None
    return None


def resolve_attribute_reference(elementID: str, xml_name: str) -> str | None:
    """Return the handle of the typed object referenced by an XML attribute.

    Args:
        elementID: TGI handle for an IP-XACT generated model element.
        xml_name: XML reference attribute name, such as ``addressSpaceRef``.

    Returns:
        The handle of the referenced generated model object, or ``None`` when
        the optional reference is not set.

    Raises:
        TgiError: ``INVALID_ID`` for a stale source handle, ``INVALID_ARGUMENT``
            for an unsupported reference name or ambiguous target, and
            ``NOT_FOUND`` when a set reference has no target in its standard
            context.

    Section: IEEE 1685-2022 F.7.43.* ``*AttributeByID`` functions.
    """
    # F.7.43.66 spells the operation ``MemoryReMap`` while the schema field is
    # ``memoryRemapRef``; callers may provide either spelling.
    if xml_name == "memoryReMapRef":
        xml_name = "memoryRemapRef"
    if xml_name not in _TARGET_TYPES:
        raise TgiError(f"Unsupported reference attribute {xml_name!r}", TgiFaultCode.INVALID_ARGUMENT)
    if not isinstance(elementID, str):
        raise TgiError("Invalid element handle", TgiFaultCode.INVALID_ID)
    element = resolve_handle(elementID)
    if element is None:
        raise TgiError("Invalid element handle", TgiFaultCode.INVALID_ID)
    reference = _reference_value(element, xml_name)
    if reference is None or not reference.strip():
        return None

    root = _root_for(element)
    source_path = _source_ancestors(root, element)
    target_root = _context_root(root, source_path, xml_name)
    if xml_name == "subPortRef":
        target = _sub_port_target(root, source_path, reference)
        if target is not None:
            _register_target_owner(target_root, target)
            return get_handle(target)
    candidates = [
        (obj, ancestors)
        for obj, ancestors in _walk(target_root)
        if _is_target(obj, xml_name) and _model_name(obj) == reference
    ]

    if xml_name == "segmentRef":
        candidates = _segment_candidates(root, source_path, candidates)

    qualifiers = _reference_qualifiers(source_path)
    if qualifiers:
        candidates = [pair for pair in candidates if _matches_reference_context(pair[0], pair[1], qualifiers)]

    if not candidates:
        raise TgiError(f"No {xml_name} target named {reference!r} was found", TgiFaultCode.NOT_FOUND)

    scored = [(_shared_ancestor_score(source_path, (*ancestors, obj)), obj) for obj, ancestors in candidates]
    best = max(score for score, _ in scored)
    matches = list(dict.fromkeys(id(obj) for score, obj in scored if score == best))
    if len(matches) != 1:
        raise TgiError(f"Reference {xml_name}={reference!r} is ambiguous", TgiFaultCode.INVALID_ARGUMENT)
    target = next(obj for score, obj in scored if score == best)
    _register_target_owner(target_root, target)
    return get_handle(target)


__all__ = ["resolve_attribute_reference"]
