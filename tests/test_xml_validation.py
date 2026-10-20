from pathlib import Path

from amal.eda.ipxact_de.xml_validation import ValidationResult, validate_ipxact_xml


def test_validate_ipxact_xml_no_schema(tmp_path):
    """Validation should fail cleanly when no schema can be resolved."""

    xml_path = tmp_path / "dummy.xml"
    xml_path.write_text("<root />")

    result: ValidationResult = validate_ipxact_xml(xml_path)

    assert result.ok is False
    assert result.schema_path is None
    assert result.standard is None
    assert result.root_element is None
    assert result.issues


def test_validate_ipxact_xml_path_roundtrip(tmp_path, monkeypatch):
    """Ensure the helper delegates to the underlying XmlValidator.

    This test stubs out the heavier XML document and validator machinery so
    that we can assert basic wiring behaviour in isolation.
    """

    # Lazily import here to avoid circular imports at module import time
    from amal.eda.ipxact_de import xml_validation as xv

    calls: list[Path] = []

    def fake_resolve_schema_for_xml(path: Path):
        calls.append(path)
        return "dummy.xsd", "1685-2022", "IPXACT", "component"

    class DummyValidator:
        def __init__(self, xsd_filename: str, use_lxml: bool = True):  # noqa: D401
            self.xsd_filename = xsd_filename
            self.use_lxml = use_lxml

        def validate(self, xml_filename: str) -> bool:  # noqa: D401
            return True

    monkeypatch.setattr(xv, "_resolve_schema_for_xml", fake_resolve_schema_for_xml)
    monkeypatch.setattr(xv, "XmlValidator", DummyValidator)

    xml_path = tmp_path / "ok.xml"
    xml_path.write_text("<root />")

    result: ValidationResult = validate_ipxact_xml(xml_path)

    assert result.ok is True
    assert result.schema_path == "dummy.xsd"
    assert result.version == "1685-2022"
    assert result.standard == "IPXACT"
    assert result.root_element == "component"
    assert calls == [xml_path]
