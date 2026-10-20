from __future__ import annotations

"""XML validation helpers for IP-XACT documents.

This module provides a small, typed wrapper around the lower-level
`XmlValidator` utility so it can be reused from different front-ends
(CLI, web APIs, and MCP servers) without duplicating logic.
"""

from dataclasses import dataclass
from pathlib import Path

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


def validate_ipxact_xml(xml: str | Path) -> ValidationResult:
    """Validate an IP-XACT XML document using strict XSD rules.

    This helper always uses the existing :class:`XmlValidator` in ``xmllint``
    mode, matching the current CLI behaviour, so that diagnostics remain
    consistent across interfaces.

    Args:
        xml: Either a filesystem path to the XML document or a string that can
            be interpreted as such.

    Returns:
        A :class:`ValidationResult` instance summarising validation outcome.
    """

    xml_path = Path(xml)

    schema_path, version, standard, root_element = _resolve_schema_for_xml(xml_path)

    if not schema_path:
        return ValidationResult(
            ok=False,
            issues=[ValidationIssue("No schema path could be determined for XML document.")],
            schema_path=None,
            version=version,
            standard=standard,
            root_element=root_element,
        )

    validator = XmlValidator(schema_path, use_lxml=False)
    ok = validator.validate(str(xml_path))

    issues: list[ValidationIssue]
    if ok:
        issues = []
    else:
        # The current backend prints diagnostics directly to the console and
        # only returns a boolean. For now we surface a single generic issue
        # while retaining strict XSD behaviour.
        issues = [ValidationIssue("XML document failed XSD validation. See xmllint output for details.")]

    return ValidationResult(
        ok=ok,
        issues=issues,
        schema_path=schema_path,
        version=version,
        standard=standard,
        root_element=root_element,
    )
