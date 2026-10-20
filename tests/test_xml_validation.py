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


def test_missing_document_returns_issue(tmp_path):
    result = validate_ipxact_xml(tmp_path / "missing.xml")
    assert not result.ok
    assert result.issues
    assert result.schema_path is None


def test_malformed_document_returns_location(tmp_path):
    path = tmp_path / "broken.xml"
    path.write_text("<component>\n<unclosed>\n</component>")
    result = validate_ipxact_xml(path)
    assert not result.ok
    assert result.issues[0].line == 3
    assert result.issues[0].column is not None


def write_bus(path, direct="true"):
    path.write_text('<busDefinition xmlns="http://www.accellera.org/XMLSchema/IPXACT/1685-2022">\n'
                    '<vendor>acme</vendor><library>bus</library><name>test</name><version>1</version>\n'
                    f'<directConnection>{direct}</directConnection><isAddressable>false</isAddressable>\n'
                    '</busDefinition>')


def test_local_schema_validation_without_external_process(tmp_path, monkeypatch):
    import subprocess

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline validation must not launch xmllint")

    monkeypatch.setattr(subprocess, "check_output", forbidden)
    path = tmp_path / "bus.xml"
    write_bus(path)
    result = validate_ipxact_xml(path, schema_root="submodules/accellera-schemas")
    assert result.ok
    assert result.issues == []
    assert result.standard == "IPXACT"
    assert result.version == "1685-2022"
    assert result.root_element == "busDefinition"
    assert result.schema_path.endswith("IPXACT/1685-2022/index.xsd")


def test_local_schema_reports_actual_validation_diagnostics(tmp_path):
    path = tmp_path / "invalid.xml"
    write_bus(path, direct="not-a-boolean")
    result = validate_ipxact_xml(path, schema_root="submodules/accellera-schemas")
    assert not result.ok
    assert any("not-a-boolean" in issue.message for issue in result.issues)
    assert result.issues[0].line == 3


def test_unavailable_and_invalid_local_schema(tmp_path):
    path = tmp_path / "bus.xml"
    write_bus(path)
    root = tmp_path / "schemas"
    for invalid in [False, True]:
        if invalid:
            schema = root / "IPXACT" / "1685-2022" / "index.xsd"
            schema.parent.mkdir(parents=True)
            schema.write_text("<not-a-schema/>")
        result = validate_ipxact_xml(path, schema_root=root)
        assert not result.ok
        assert "Schema could not be loaded" in result.issues[0].message
        assert result.root_element == "busDefinition"


def test_offline_validation_of_older_standard(tmp_path):
    path = tmp_path / "legacy.xml"
    path.write_text('<spirit:busDefinition xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5">'
                    '<spirit:vendor>acme</spirit:vendor><spirit:library>bus</spirit:library>'
                    '<spirit:name>legacy</spirit:name><spirit:version>1</spirit:version>'
                    '<spirit:directConnection>true</spirit:directConnection>'
                    '<spirit:isAddressable>false</spirit:isAddressable></spirit:busDefinition>')
    result = validate_ipxact_xml(path, schema_root="submodules/accellera-schemas")
    assert result.ok
    assert result.standard == "SPIRIT"
    assert result.version == "1.5"
