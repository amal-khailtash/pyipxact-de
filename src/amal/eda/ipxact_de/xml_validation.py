"""XML validation helpers for IP-XACT documents.

This module provides a small, typed wrapper around the lower-level
`XmlValidator` utility so it can be reused from different front-ends
(CLI, web APIs, and MCP servers) without duplicating logic.
"""


from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from amal.eda.ipxact_de.xml_document import XmlDocument
from amal.utilities import XmlValidator


@dataclass(slots=True)
class ValidationIssue:
    """Single validation issue discovered while checking an XML document.

    Attributes:
        message: Human-readable description of the problem reported by the
            underlying validator.
    """

    message: str
    line: int | None = None
    column: int | None = None
    rule_id: str | None = None
    path: str | None = None


@dataclass(slots=True)
class ValidationResult:
    """Result of strict XML validation against an Accellera IP-XACT schema.

    Attributes:
        ok: True when the document validates successfully.
        issues: Iterable of discovered problems when ``ok`` is False; empty
            when validation succeeds.
        schema_path: Optional path to the XSD schema that was used.
        version: Optional IP-XACT version string as detected from the
            document (for example ``"1685-2022"``).
        standard: Optional standard name (e.g., "IPXACT", "SPIRIT").
        root_element: Optional root element name (e.g., "component", "design").
    """

    ok: bool
    issues: list[ValidationIssue]
    schema_path: str | None
    version: str | None
    standard: str | None
    root_element: str | None
    checked_semantic_rules: tuple[str, ...] = ()


def _resolve_schema_for_xml(xml_path: Path) -> tuple[str | None, str | None, str | None, str | None]:
    """Infer schema path, IP-XACT version, standard, and root element from an XML file.

    This relies on :class:`~amal.eda.ipxact_de.xml_document.XmlDocument` to
    perform the heavy lifting of parsing and identifying the appropriate
    schema.

    Args:
        xml_path: Path to the XML instance document.

    Returns:
        A tuple of ``(schema_path, version, standard, root_element)`` where any element may be
        ``None`` if it cannot be determined.
    """

    try:
        document = XmlDocument(xml_path)
    except ValueError:
        # Raised for non-IP-XACT/SPIRIT namespaces; treat as
        # "schema could not be determined" so callers can surface a
        # structured failure instead of propagating the exception.
        return None, None, None, None

    schema_path: str | None = document.schema or None
    version: str | None = document.version or None
    standard: str | None = document.standard or None
    root_element: str | None = document.root_name or None
    return schema_path, version, standard, root_element


def _validate_schema(xml: str | Path, *, schema_root: str | Path | None = None) -> ValidationResult:
    """Validate an IP-XACT XML document using strict XSD rules.

    With ``schema_root``, resolve schemas as FAMILY/version/index.xsd under
    that directory and validate in-process without network access. Otherwise
    retain the existing xmllint backend.

    Args:
        xml: Either a filesystem path to the XML document or a string that can
            be interpreted as such.
        schema_root: Optional local Accellera schema tree containing IPXACT/
            and SPIRIT/ directories.

    Returns:
        A :class:`ValidationResult` instance summarising validation outcome.
    """

    xml_path = Path(xml)

    try:
        schema_path, version, standard, root_element = _resolve_schema_for_xml(xml_path)
    except (OSError, etree.XMLSyntaxError) as error:
        line, column = getattr(error, "position", (None, None))
        return ValidationResult(False, [ValidationIssue(str(error), line, column)], None, None, None, None)

    if not schema_path:
        return ValidationResult(
            ok=False,
            issues=[ValidationIssue("No schema path could be determined for XML document.")],
            schema_path=None,
            version=version,
            standard=standard,
            root_element=root_element,
        )

    if schema_root is not None:
        local_schema = Path(schema_root) / standard / version / "index.xsd"
        schema_path = str(local_schema)
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        try:
            schema = etree.XMLSchema(etree.parse(str(local_schema), parser))
        except (OSError, etree.XMLSyntaxError, etree.XMLSchemaParseError) as error:
            return ValidationResult(False, [ValidationIssue(f"Schema could not be loaded: {error}")],
                                    schema_path, version, standard, root_element)
        try:
            tree = etree.parse(str(xml_path), parser)
            ok = schema.validate(tree)
            issues = [ValidationIssue(entry.message, entry.line or None, entry.column or None)
                      for entry in schema.error_log]
        except (OSError, etree.XMLSyntaxError) as error:
            line, column = getattr(error, "position", (None, None))
            ok, issues = False, [ValidationIssue(str(error), line, column)]
        return ValidationResult(ok, issues, schema_path, version, standard, root_element)

    validator = XmlValidator(schema_path, use_lxml=False)
    ok = validator.validate(str(xml_path))

    issues = [] if ok else [ValidationIssue("XML document failed XSD validation. See xmllint output for details.")]

    return ValidationResult(
        ok=ok,
        issues=issues,
        schema_path=schema_path,
        version=version,
        standard=standard,
        root_element=root_element,
    )


def validate_ipxact_xml(
    xml: str | Path, *, schema_root: str | Path | None = None, semantic: bool = False,
) -> ValidationResult:
    """Validate XSD and optionally the implemented local IEEE semantic rules.

    Semantic checks run only after successful XSD validation. Currently supported
    scope is IEEE 1685-2022 abstractionDefinition and component constraints. An unsupported root
    or version returns a diagnostic when semantic checks are requested, rather than
    implying that unimplemented rules passed. checked_semantic_rules identifies
    the exact coverage; success does not establish complete semantic conformance.
    """
    result = _validate_schema(xml, schema_root=schema_root)
    if not semantic or not result.ok:
        return result
    if result.standard != "IPXACT" or result.version != "1685-2022" or result.root_element not in {
        "abstractionDefinition", "component",
    }:
        result.ok = False
        result.issues.append(ValidationIssue("Semantic checks are available only for IEEE 1685-2022 "
                                             "abstractionDefinition and component constraints."))
        return result
    from amal.eda.ipxact_de.semantic_validation import (
        validate_abstraction_constraints,
        validate_component_constraints,
    )
    from org.accellera.ipxact.v1685_2022 import AbstractionDefinition, Component

    model_type = AbstractionDefinition if result.root_element == "abstractionDefinition" else Component
    validate_model = (validate_abstraction_constraints if model_type is AbstractionDefinition
                      else validate_component_constraints)
    parser = etree.XMLParser(no_network=True, resolve_entities=False)
    try:
        tree = etree.parse(str(xml), parser)
        document = XmlDocument.parser().from_string(etree.tostring(tree, encoding="unicode"), model_type)
    except (OSError, etree.XMLSyntaxError, ValueError) as error:
        result.ok = False
        result.issues.append(ValidationIssue(f"Semantic model could not be loaded: {error}"))
        return result
    semantic_result = validate_model(document)
    result.checked_semantic_rules = semantic_result.checked_rules
    for issue in semantic_result.issues:
        element_path = issue.path.rsplit("/@", 1)[0]
        elements = tree.xpath(element_path, namespaces={"ipxact": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"})
        line = elements[0].sourceline if elements else None
        result.issues.append(ValidationIssue(issue.message, line=line, rule_id=issue.rule_id, path=issue.path))
    result.ok = semantic_result.ok
    return result
