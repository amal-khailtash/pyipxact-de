"""XML parsing utilities for IP-XACT / SPIRIT documents.
"""
from pathlib import Path
from typing import TypeVar

from lxml import etree
from rich import print
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.formats.dataclass.serializers.xml import XmlSerializer

from amal.utilities import ARROW, CHECK

from org.accellera.standard import STANDARDS, Standard

T = TypeVar("T")


class XmlDocument:
    """Represents a parsed IP-XACT/SPIRIT XML document.

    Attributes
    ----------
    path: Path
        Path to the original XML file.
    tree: etree._ElementTree | None
        Parsed XML tree (None until parsing succeeds).
    schema: str | None
        Resolved schema location (index.xsd path) if discovered.
    version: str | None
        Version string in the form 'IPXACT/1685-2022' or 'SPIRIT/1.5'.
    root_name: str | None
        Root element name.
    is_spirit: bool
        True if the file namespace matches SPIRIT.
    is_ipxact: bool
        True if the file namespace matches IP-XACT.
    """

    def __init__(self, path: Path, *, auto_parse: bool = True) -> None:
        """Create a new XML document representation.

        Parameters
        ----------
        path: Path
            Path to the XML file to be parsed.
        auto_parse: bool, default True
            If True (default) the file is parsed immediately; set to False to
            defer parsing and call parse() manually.
        """
        # Initialize slot attributes
        self.path: Path = path
        self.tree: etree._ElementTree | None = None
        self.schema: str = ""
        self.standard: str = ""
        self.version: str = ""
        self.root_name: str = ""
        self.is_spirit: bool = False
        self.is_ipxact: bool = False
        if auto_parse:
            self.parse()

    # ------------------------------------------------------------------
    # Shared serializer/parser singletons
    # ------------------------------------------------------------------
    _XML_CONTEXT: XmlContext = XmlContext()
    _SCHEMA_LOCATION = Standard.schema_location_for("ipxact", "1685-2022")
    _SERIALIZER: XmlSerializer = XmlSerializer(
        context=_XML_CONTEXT,
        config=SerializerConfig(indent="  ", schema_location=_SCHEMA_LOCATION)
    )
    _PARSER: XmlParser = XmlParser(context=_XML_CONTEXT)

    @classmethod
    def serializer(cls) -> XmlSerializer:
        """Return a shared ``XmlSerializer`` instance.

        Returns
        -------
        XmlSerializer
            The singleton serializer configured with two-space indentation.
        """
        return cls._SERIALIZER

    @classmethod
    def parser(cls) -> XmlParser:
        """Return a shared ``XmlParser`` instance.

        Returns
        -------
        XmlParser
            The singleton parser bound to the shared XML context.
        """
        return cls._PARSER

    # ------------------------------------------------------------------
    def parse(self) -> None:
        """Parse the XML document if not already parsed.

        This populates tree, schema, standard, version, root_name, and flags.
        Subsequent calls are no-ops.
        """
        if self.tree is not None:
            return  # already parsed

        print(f"{ARROW} Parsing ...")
        # Identify the expanded root name, independent of namespace prefix choices.
        # Keep parsed state local until identification succeeds so a failed parse
        # can be retried after the source document has been corrected.
        tree = etree.parse(str(self.path))
        root = tree.getroot()
        namespace = etree.QName(root).namespace
        for meta in STANDARDS.values():
            base = f"{meta.schema_root}/{meta.token}/"
            if namespace and namespace.startswith(base):
                version = namespace[len(base):]
                Standard.validate(meta.name, version)
                standard = meta.token
                break
        else:
            raise ValueError("Unsupported XML namespace for IP-XACT/SPIRIT")

        self.tree = tree
        self.root_name = etree.QName(root).localname
        self.standard = standard
        self.version = version
        self.schema = f"{namespace}/index.xsd"
        self.is_spirit = meta.name == "spirit"
        self.is_ipxact = meta.name == "ipxact"
        print(f"  {ARROW} Success {CHECK}")
        print(f"{ARROW} Found       : '{self.root_name}'")
        print(f"  {ARROW} Standard  : '{self.standard}'")
        print(f"  {ARROW} Version   : '{self.version}'")
        return None

    # Note: Legacy builder/to_xml helpers were removed (no backward compatibility required).

    # ------------------------------------------------------------------
    def serialize(self, obj: object) -> str:
        """Serialize ``obj`` using the shared serializer.

        Parameters
        ----------
        obj: object
            The dataclass instance to serialize.

        Returns
        -------
        str
            The serialized XML content.
        """
        return self.serializer().render(obj)

    # ------------------------------------------------------------------
    @classmethod
    def deserialize(cls, xml: str, cls_type: type[T]) -> T:
        """Deserialize ``xml`` string into an instance of ``cls_type``.

        Parameters
        ----------
        xml: str
            XML text to parse.
        cls_type: type[T]
            Target dataclass type.

        Returns
        -------
        T
            The deserialized object instance.
        """
        return cls.parser().from_string(xml, cls_type)
