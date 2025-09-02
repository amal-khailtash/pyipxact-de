"""Repository scanner and persistent registry loader.

This module discovers IP-XACT/SPIRIT XML files under user-provided paths
and the IPXACT_XML_PATHS environment variable, parses them, and registers
their root objects in the global VLNV registry. It maintains a small cache
to avoid reparsing unchanged files and to drop entries for files that were
removed.

Design notes:
- Caching: a simple JSON cache keyed by absolute file path storing mtime,
  root tag, standard, version, and VLNV quadruple. On startup we compare
  mtimes to decide whether to reparse.
- Persistence: we recompute the full registry on each invocation based on
  the current filesystem view, clearing the registry first to reflect
  additions/removals.
- VLNV validation: for catalog files we traverse ipxact:ipxactFile entries
  and verify the referenced file's VLNV matches the vlnv attributes; we log
  a warning on mismatch.

This intentionally has no external dependencies beyond lxml and xsdata
already used by the project.
"""
# ruff: noqa: I001
from collections.abc import Iterable
from dataclasses import dataclass
import json
import os
from pathlib import Path

from lxml import etree

from amal.utilities import ARROW, logger
from .tgi.ipxact.v1685_2022.core import VLNV, registry
from .xml_document import XmlDocument


CACHE_BASENAME = ".ipxact-de-cache.json"
SUPPORTED_STANDARD = "ipxact"
SUPPORTED_VERSION = "1685-2022"


@dataclass(slots=True)
class CacheEntry:
    """Cache entry for a single XML file.

    Attributes:
        path: Absolute path to XML.
        mtime: Last modification time at cache write.
        element: Root element localname.
        standard: "ipxact" or "spirit".
        version: Version string e.g. "1685-2022" or "1.5".
        vlnv: VLNV quadruple for the root element when available, else None.
    """

    path: str
    mtime: float
    element: str
    standard: str
    version: str
    vlnv: VLNV | None


def _default_cache_dir() -> Path:
    """Return default cache directory.

    Uses the current working directory.
    """
    return Path.cwd()


def _load_cache(cache_path: Path) -> dict[str, CacheEntry]:
    """Load cache file (array of records) into a dict keyed by absolute path."""
    if not cache_path.exists():
        return {}
    try:
        items = json.loads(cache_path.read_text())
        out: dict[str, CacheEntry] = {}
        if not isinstance(items, list):  # expect array; otherwise ignore
            return {}
        for v in items:
            ce = CacheEntry(
                path=v["path"],
                mtime=v["mtime"],
                element=v.get("element", ""),
                standard=v.get("standard", ""),
                version=v.get("version", ""),
                vlnv=tuple(v["vlnv"]) if v.get("vlnv") else None,  # type: ignore[arg-type]
            )
            out[ce.path] = ce
        return out
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(f"Failed to load cache '{cache_path}': {exc}")
        return {}


def _save_cache(cache_path: Path, cache: dict[str, CacheEntry]) -> None:
    """Persist cache to disk as an array of entries."""
    payload = [
        {
            "path": e.path,
            "mtime": e.mtime,
            "element": e.element,
            "standard": e.standard,
            "version": e.version,
            "vlnv": list(e.vlnv) if e.vlnv else None,
        }
        for e in cache.values()
    ]
    cache_path.write_text(json.dumps(payload, indent=2))


def load_registry_from_cache(*, cache_dir: Path | None = None) -> bool:
    """Load the in-memory registry solely from the on-disk cache.

    This does not touch the filesystem for discovery. It reads the cache file
    (from the current working directory by default) and re-registers cached
    entries into the global VLNV registry. Unsupported standards/versions are
    skipped. Returns True if any entries were loaded.

    Args:
        cache_dir: Optional explicit directory containing the cache file.

    Returns:
        True if at least one cached entry was re-registered; False otherwise.
    """
    cache_base = cache_dir or _default_cache_dir()
    cache_path = cache_base / CACHE_BASENAME
    cache = _load_cache(cache_path)
    if not cache:
        return False
    registry.clear()
    loaded = 0
    for f, ce in cache.items():
        if not ce.vlnv:
            continue
        if (ce.standard or "").lower() != SUPPORTED_STANDARD or (ce.version or "") != SUPPORTED_VERSION:
            continue
        path = Path(f)
        try:
            class _CachedProxy:
                """Proxy used for re-registration from cache only."""
                __slots__ = ("vendor", "library", "name", "version", "xml_path")
                def __init__(self, v: VLNV, p: Path) -> None:
                    self.vendor, self.library, self.name, self.version = v
                    self.xml_path = str(p)
            proxy = _CachedProxy(ce.vlnv, path)
            # Derive element type from cached element local name
            etype = (ce.element[:1].upper() + ce.element[1:]) if ce.element else None
            registry.register(
                proxy,
                ce.vlnv,
                file_name=f,
                replace=True,
                element_type=etype,
            )
            loaded += 1
        except Exception:  # pragma: no cover - defensive
            continue
    return loaded > 0


def _iter_xml_files(paths: Iterable[Path]) -> Iterable[Path]:
    """Yield XML files under given paths.

    Directories are traversed recursively; files are yielded if they have
    a .xml extension.
    """
    for p in paths:
        if p.is_dir():
            yield from p.rglob("*.xml")
        elif p.is_file() and p.suffix.lower() == ".xml":
            yield p


def _extract_vlnv_from_root(root: etree._Element) -> VLNV | None:
    """Try to extract VLNV from a root element using common child tags.

    This covers typical root elements like catalog/component/busDefinition
    which carry vendor/library/name/version children in the same namespace.
    Returns None if not all parts are present.
    """
    ns = root.nsmap.get("ipxact") or root.nsmap.get("spirit")
    if not ns:
        return None
    def _t(tag: str) -> str:
        return f"{{{ns}}}{tag}"
    vendor = root.findtext(_t("vendor"))
    library = root.findtext(_t("library"))
    name = root.findtext(_t("name"))
    version = root.findtext(_t("version"))
    if all([vendor, library, name, version]):
        return (vendor or "", library or "", name or "", version or "")
    return None


def _validate_catalog_ipxact_files(doc: XmlDocument, base_dir: Path) -> None:
    """Validate ipxactFile entries in a catalog match underlying file VLNVs.

    If an entry path is relative, it is resolved against `base_dir`.
    Logs warnings for missing files or VLNV mismatches.
    """
    if doc.tree is None:
        return
    root = doc.tree.getroot()
    ns = root.nsmap.get("ipxact")
    if not ns:
        return
    q_ipxactFile = f".//{{{ns}}}ipxactFile"
    q_vlnv = f"{{{ns}}}vlnv"
    q_name = f"{{{ns}}}name"
    for ipf in root.findall(q_ipxactFile):
        vlnv_elem = ipf.find(q_vlnv)
        name_elem = ipf.find(q_name)
        if vlnv_elem is None or name_elem is None:
            continue
        expected: VLNV = (
            vlnv_elem.get("vendor", ""),
            vlnv_elem.get("library", ""),
            vlnv_elem.get("name", ""),
            vlnv_elem.get("version", ""),
        )
        rel_path = (name_elem.text or "").strip()
        if not rel_path:
            continue
        target = (base_dir / rel_path).resolve()
        if not target.exists():
            logger.warning(f"ipxactFile target missing: {target}")
            continue
        try:
            t_doc = XmlDocument(target)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Failed parsing ipxactFile target {target}: {exc}")
            continue
        if t_doc.tree is None:
            continue
        v_actual = _extract_vlnv_from_root(t_doc.tree.getroot())
        if v_actual and v_actual != expected:
            logger.warning(
                f"VLNV mismatch for {target}: catalog {expected} vs file {v_actual}"
            )


def _register_root(doc: XmlDocument) -> VLNV | None:
    """Register root object of `doc` in the global registry.

    Returns the VLNV used for registration when available.
    """
    if doc.tree is None:
        return None
    root = doc.tree.getroot()
    vlnv = _extract_vlnv_from_root(root)
    if vlnv is None:
        return None
    # Create a minimal proxy object if the parsed root is not a dataclass
    # from xsdata. Here we simply attach attributes to the lxml root via a
    # lightweight wrapper to store vendor/library/name/version and xml_path.
    class _RootProxy:
        """Lightweight proxy storing root VLNV and XML path."""
        __slots__ = ("vendor", "library", "name", "version", "xml_path")
        def __init__(self, v: VLNV, path: Path) -> None:
            self.vendor, self.library, self.name, self.version = v
            self.xml_path = str(path)

    proxy = _RootProxy(vlnv, doc.path)
    # Normalize element type from tag local name (e.g., 'component' -> 'Component')
    try:
        tag_local = etree.QName(root).localname
        element_type = tag_local[:1].upper() + tag_local[1:]
    except Exception:
        element_type = None
    registry.register(
        proxy,
        vlnv,
        file_name=str(doc.path),
        replace=True,
        element_type=element_type,
    )
    return vlnv


def load_registry_from_paths(paths: Iterable[str], *, cache_dir: Path | None = None) -> None:
    """Scan paths and IPXACT_XML_PATHS, update the global registry.

    Args:
        paths: Iterable of path strings passed on the command line.
        cache_dir: Optional explicit cache directory.
    """
    search_paths: list[Path] = []
    # CLI provided paths
    for p in paths:
        if p:
            search_paths.append(Path(p).expanduser().resolve())
    # Environment paths (colon-separated)
    env = os.environ.get("IPXACT_XML_PATHS", "")
    for p in (e for e in env.split(":") if e):
        search_paths.append(Path(p).expanduser().resolve())
    # De-duplicate while preserving order
    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for p in search_paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)
    if not unique_paths:
        return

    cache_base = cache_dir or _default_cache_dir()
    cache_path = cache_base / CACHE_BASENAME
    cache = _load_cache(cache_path)

    # Compute current file set
    files = sorted({str(p.resolve()) for p in _iter_xml_files(unique_paths)})

    # Clear registry; we'll rebuild from current files
    registry.clear()

    new_cache: dict[str, CacheEntry] = {}
    for f in files:
        path = Path(f)
        mtime = path.stat().st_mtime
        ce = cache.get(f)
        if ce and abs(ce.mtime - mtime) < 1e-6 and ce.vlnv:
            # Skip unsupported standards/versions even if cached
            if (ce.standard or "").lower() != SUPPORTED_STANDARD or (ce.version or "") != SUPPORTED_VERSION:
                logger.warning(
                    f"{ARROW} Skipping unsupported XML for scan: '{f}' "
                    f"(detected {ce.standard}/{ce.version}); only {SUPPORTED_STANDARD}/{SUPPORTED_VERSION} is supported"
                )
                continue
            # unchanged; fast register using cached VLNV
            try:
                class _CachedProxy:
                    """Proxy used for fast re-registration from cache."""
                    __slots__ = ("vendor", "library", "name", "version", "xml_path")
                    def __init__(self, v: VLNV, p: Path) -> None:
                        self.vendor, self.library, self.name, self.version = v
                        self.xml_path = str(p)
                proxy = _CachedProxy(ce.vlnv, path)
                # Derive element type from cached element local name
                etype = (ce.element[:1].upper() + ce.element[1:]) if ce.element else None
                registry.register(
                    proxy,
                    ce.vlnv,
                    file_name=f,
                    replace=True,
                    element_type=etype,
                )
                new_cache[f] = CacheEntry(
                    path=f,
                    mtime=mtime,
                    element=ce.element,
                    standard=ce.standard,
                    version=ce.version,
                    vlnv=ce.vlnv,
                )
                continue
            except Exception:
                # fall through to reparse on any issue
                pass

        # Parse fresh
        try:
            doc = XmlDocument(path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"{ARROW} Failed parsing '{f}': {exc}")
            continue
        # Filter to supported standard/version only
        if (doc.standard or "").lower() != SUPPORTED_STANDARD or (doc.version or "") != SUPPORTED_VERSION:
            logger.warning(
                f"{ARROW} Skipping unsupported XML for scan: '{f}' "
                f"(detected {doc.standard}/{doc.version}); only {SUPPORTED_STANDARD}/{SUPPORTED_VERSION} is supported"
            )
            continue
        vlnv = _register_root(doc)
        if doc.tree is not None:
            # If catalog, validate its ipxactFile entries
            tag_local = etree.QName(doc.tree.getroot()).localname
            if tag_local.lower() == "catalog":
                _validate_catalog_ipxact_files(doc, base_dir=path.parent)
            standard = doc.standard
            version = doc.version
            new_cache[f] = CacheEntry(
                path=f,
                mtime=mtime,
                element=tag_local,
                standard=standard,
                version=version,
                vlnv=vlnv,
            )

    # Persist cache for next run
    _save_cache(cache_path, new_cache)
