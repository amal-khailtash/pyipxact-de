"""Repository scanner and persistent registry loader.

This module discovers IP-XACT/SPIRIT XML files under user-provided paths
and the IPXACT_XML_PATHS environment variable, parses them, and registers
their root objects in the global VLNV registry. It maintains a small cache
to avoid reparsing unchanged files and to drop entries for files that were
removed.

Design notes:
- Caching: a simple JSON cache keyed by absolute file path storing mtime,
  root tag, standard, version, and VLNV quadruple. On startup we compare
  mtimes to reuse registry metadata. Dependency discovery reparses current files
  to recheck catalog references, including references outside the search paths.
- Persistence: we recompute the full registry on each invocation based on
  the current filesystem view, clearing the registry first to reflect
  additions/removals.
- Search precedence: explicit paths precede environment paths; first duplicate VLNV wins with a warning.
- VLNV validation: for catalog files we traverse ipxact:ipxactFile entries
  and verify the referenced file's VLNV matches the vlnv attributes; we log
  a warning on mismatch.

This intentionally has no external dependencies beyond lxml and xsdata
already used by the project.
"""

# ruff: noqa: I001
from collections.abc import Callable, Iterable
from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
import json
import os
import math
import re
import stat
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import etree

from amal.utilities import ARROW, logger
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import VLNV, registry
from .xml_document import XmlDocument
from org.accellera.standard import STANDARDS


CACHE_BASENAME = ".ipxact-de-cache.json"
type ProgressCallback = Callable[[str, int, int], None]
type DocumentReporter = Callable[[Path, str, str, str], None]
TOP_LEVEL_ELEMENTS = frozenset(
    {
        "abstractor",
        "abstractionDefinition",
        "busDefinition",
        "catalog",
        "component",
        "design",
        "designConfiguration",
        "generatorChain",
        "typeDefinitions",
    }
)


def _recognized_document(standard: str, version: str, element: str) -> bool:
    meta = STANDARDS.get(standard.lower())
    return meta is not None and version in meta.versions and element in TOP_LEVEL_ELEMENTS


@dataclass(slots=True)
class _DocumentProxy:
    """Lightweight inventory record shared by fresh and cached discovery."""

    vendor: str
    library: str
    name: str
    version: str
    xml_path: str


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
        fingerprint: Nanosecond mtime, nanosecond ctime, and size; absent for legacy records.
    """

    path: str
    mtime: float
    element: str
    standard: str
    version: str
    vlnv: VLNV | None
    fingerprint: tuple[int, int, int] | None = None


def _default_cache_dir() -> Path:
    """Return default cache directory.

    Uses the current working directory.
    """
    return Path.cwd()


def _load_cache(cache_path: Path) -> dict[str, CacheEntry]:
    """Load cache file (array of records) into a dict keyed by absolute path."""
    try:
        if not cache_path.exists():
            return {}
        items = json.loads(cache_path.read_text())
        out: dict[str, CacheEntry] = {}
        if not isinstance(items, list):  # expect array; otherwise ignore
            return {}
        for v in items:
            try:
                if not isinstance(v, dict) or not isinstance(v.get("path"), str) or not Path(v["path"]).is_absolute():
                    raise ValueError("cache path must be absolute")
                mtime = v["mtime"]
                if isinstance(mtime, bool) or not isinstance(mtime, (float, int)) or not math.isfinite(mtime):
                    raise ValueError("invalid modification time")
                vlnv = v.get("vlnv")
                if vlnv is not None and (
                    not isinstance(vlnv, list)
                    or len(vlnv) != 4
                    or not all(isinstance(part, str) and part for part in vlnv)
                ):
                    raise ValueError("invalid VLNV")
                fingerprint = v.get("fingerprint")
                if fingerprint is not None and (
                    not isinstance(fingerprint, list)
                    or len(fingerprint) != 3
                    or not all(type(part) is int and part >= 0 for part in fingerprint)
                ):
                    raise ValueError("invalid file fingerprint")
                if not all(isinstance(v.get(key, ""), str) for key in ("element", "standard", "version")):
                    raise ValueError("invalid document metadata")
                ce = CacheEntry(
                    path=v["path"],
                    mtime=mtime,
                    element=v.get("element", ""),
                    standard=v.get("standard", ""),
                    version=v.get("version", ""),
                    vlnv=tuple(vlnv) if vlnv is not None else None,
                    fingerprint=tuple(fingerprint) if fingerprint is not None else None,
                )
                out[ce.path] = ce
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning(f"Ignoring invalid cache record in {cache_path}: {exc}")
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
            "fingerprint": list(e.fingerprint) if e.fingerprint else None,
        }
        for e in cache.values()
    ]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=cache_path.parent, delete=False, encoding="utf-8") as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, cache_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _fingerprint(path: Path, *, source_stat: os.stat_result | None = None) -> tuple[int, int, int]:
    metadata = source_stat if source_stat is not None else path.stat()
    return metadata.st_mtime_ns, metadata.st_ctime_ns, metadata.st_size


def load_registry_from_cache(
    *, cache_dir: Path | None = None, validate_files: bool = True, progress: ProgressCallback | None = None
) -> bool:
    """Load the in-memory registry solely from the on-disk cache.

    This does not discover files. By default, it checks cached paths and their fingerprints; when
    ``validate_files`` is False, it restores the saved recognized-document inventory without checking source
    files. It reads the cache file (from the current working directory by default) and re-registers cached
    entries into the global VLNV registry. Unrecognized editions and non-document roots are skipped. Returns
    True if any entries were loaded.

    Args:
        cache_dir: Optional explicit directory containing the cache file.
        validate_files: Whether cached source files must still exist and match their saved fingerprints.
        progress: Optional callback receiving a phase name, current count, and total count.

    Returns:
        True if at least one cached entry was re-registered; False otherwise.
    """
    cache_base = cache_dir or _default_cache_dir()
    cache_path = cache_base / CACHE_BASENAME
    if progress is not None:
        progress("reading_cache", 0, 0)
    cache = _load_cache(cache_path)
    registry.clear()
    loaded = 0
    seen_vlnvs: set[VLNV] = set()
    total = len(cache)
    if progress is not None:
        progress("loading", 0, total)
    for index, (f, ce) in enumerate(cache.items(), start=1):
        if progress is not None:
            progress("loading", index, total)
        if not ce.vlnv:
            continue
        if not _recognized_document(ce.standard, ce.version, ce.element):
            continue
        path = Path(f)
        try:
            if validate_files:
                source_stat = path.stat()
                if not stat.S_ISREG(source_stat.st_mode):
                    continue
                fingerprint = _fingerprint(path, source_stat=source_stat)
                if ce.fingerprint != fingerprint:
                    continue
            if ce.vlnv in seen_vlnvs:
                logger.warning(f"Duplicate cached VLNV {ce.vlnv}: skipping {f}")
                continue
            proxy = _DocumentProxy(*ce.vlnv, str(path))
            # Derive element type from cached element local name
            etype = (ce.element[:1].upper() + ce.element[1:]) if ce.element else None
            registry.register(
                proxy,
                ce.vlnv,
                file_name=f,
                replace=True,
                element_type=etype,
                standard=ce.standard,
                schema_version=ce.version,
            )
            seen_vlnvs.add(ce.vlnv)
            loaded += 1
        except Exception:  # pragma: no cover - defensive
            continue
    if progress is not None:
        progress("completed", total, total)
    return loaded > 0


def _iter_xml_files(paths: Iterable[Path]) -> Iterable[Path]:
    """Yield XML files under given paths.

    Directories are traversed recursively; files are yielded if they have
    a .xml extension. Each directory is read and sorted before traversal continues,
    so earlier files are available without waiting for the rest of the tree.
    """

    def visit(directory: Path) -> Iterable[Path]:
        try:
            with os.scandir(directory) as iterator:
                entries = list(iterator)
        except OSError as exc:
            logger.warning(f"Cannot scan directory {directory}: {exc}")
            return

        ordered: list[tuple[str, os.DirEntry[str], bool, bool]] = []
        for entry in entries:
            try:
                is_directory = entry.is_dir(follow_symlinks=False)
                is_symlink = entry.is_symlink()
            except OSError as exc:
                logger.warning(f"Cannot inspect discovered path {entry.path}: {exc}")
                continue
            ordered.append((entry.name, entry, is_directory, is_symlink))

        for _, entry, is_directory, is_symlink in sorted(ordered, key=lambda item: item[0]):
            path = Path(entry.path)
            if is_directory:
                yield from visit(path)
                continue
            if path.suffix.lower() != ".xml":
                continue
            try:
                is_file = entry.is_file()
            except OSError as exc:
                logger.warning(f"Cannot inspect discovered path {path}: {exc}")
                continue
            if is_file:
                yield path.resolve() if is_symlink else path

    for p in paths:
        if p.is_dir():
            yield from visit(p)
        elif p.is_file() and p.suffix.lower() == ".xml":
            yield p.resolve() if p.is_symlink() else p


def _read_document(path: Path, document_reporter: DocumentReporter | None = None) -> XmlDocument:
    """Parse a document and optionally report its path and detected schema metadata."""
    if document_reporter is None:
        return XmlDocument(path)
    document_reporter(path, "", "", "")
    with redirect_stdout(StringIO()):
        document = XmlDocument(path)
    document_reporter(path, document.root_name, document.standard, document.version)
    return document


def _extract_vlnv_from_root(root: etree._Element) -> VLNV | None:
    """Try to extract VLNV from a root element using common child tags.

    This covers typical root elements like catalog/component/busDefinition
    which carry vendor/library/name/version children in the same namespace.
    Returns None if not all parts are present.
    """
    ns = etree.QName(root).namespace
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


def _catalog_references(doc: XmlDocument) -> Iterable[tuple[Path, VLNV, str]]:
    """Resolve local catalog entry URIs without fetching remote resources."""
    if doc.tree is None:
        return
    root = doc.tree.getroot()
    ns = etree.QName(root).namespace
    if not ns:
        return
    categories = {
        "catalogs": "catalog",
        "busDefinitions": "busDefinition",
        "abstractionDefinitions": "abstractionDefinition",
        "components": "component",
        "abstractors": "abstractor",
        "designs": "design",
        "designConfigurations": "designConfiguration",
        "generatorChains": "generatorChain",
        "typeDefinitions": "typeDefinitions",
    }
    for category, expected_type in categories.items():
        for entry in root.findall(f"{{{ns}}}{category}/{{{ns}}}ipxactFile"):
            reference = entry.find(f"{{{ns}}}vlnv")
            name = entry.findtext(f"{{{ns}}}name")
            if reference is None or not name or not name.strip():
                logger.warning(f"Incomplete catalog entry in {doc.path}")
                continue
            expected = tuple(reference.get(key, "") for key in ("vendor", "library", "name", "version"))
            if not all(part.strip() for part in expected):
                logger.warning(f"Incomplete catalog VLNV in {doc.path}")
                continue
            try:
                uri = urlsplit(name.strip())
                if (
                    uri.scheme not in ("", "file")
                    or uri.netloc not in ("", "localhost")
                    or uri.query
                    or uri.fragment
                    or not uri.path
                ):
                    logger.warning(f"Unsupported catalog URI in {doc.path}: {name}")
                    continue
                if re.search(r"%(?![0-9A-Fa-f]{2})", uri.path):
                    raise ValueError("malformed percent escape")
                decoded = unquote(uri.path, errors="strict")
                if "\x00" in decoded:
                    raise ValueError("NUL in decoded path")
                target = (doc.path.parent / decoded).resolve()
            except (ValueError, OSError) as exc:
                logger.warning(f"Invalid catalog URI in {doc.path}: {name}: {exc}")
                continue
            yield target, expected, expected_type


def _discover_catalog_dependencies(
    files: list[str],
    progress: ProgressCallback | None = None,
    document_reporter: DocumentReporter | None = None,
) -> tuple[list[str], dict[str, XmlDocument]]:
    """Expand catalogs with cycle detection; explicit discoveries retain precedence."""
    ordered = dict.fromkeys(files)
    parsed: dict[str, XmlDocument] = {}
    visited: set[str] = set()
    active: set[str] = set()

    def visit(file_name: str) -> None:
        if file_name in active:
            logger.warning(f"Catalog reference cycle at {file_name}")
            return
        if file_name in visited:
            return
        active.add(file_name)
        try:
            doc = parsed.get(file_name)
            if doc is None:
                doc = _read_document(Path(file_name), document_reporter)
                parsed[file_name] = doc
            if doc.tree is None or not _recognized_document(doc.standard, doc.version, doc.root_name):
                return
            root = doc.tree.getroot()
            if etree.QName(root).localname != "catalog":
                return
            for target, expected, expected_type in _catalog_references(doc):
                target_name = str(target)
                try:
                    child = parsed.get(target_name)
                    if child is None:
                        child = _read_document(target, document_reporter)
                        parsed[target_name] = child
                    if child.tree is None:
                        logger.warning(f"Malformed catalog target {target}")
                        continue
                    if not _recognized_document(child.standard, child.version, child.root_name):
                        logger.warning(
                            f"Unsupported catalog target {target}: {child.standard}/{child.version}, "
                            f"root {child.root_name}"
                        )
                        continue
                    actual_type = etree.QName(child.tree.getroot()).localname
                    if actual_type != expected_type:
                        logger.warning(
                            f"Catalog category mismatch for {target}: expected {expected_type}, got {actual_type}"
                        )
                    actual = _extract_vlnv_from_root(child.tree.getroot())
                    if actual is None:
                        logger.warning(f"Incomplete target VLNV for {target}")
                        continue
                    if actual != expected:
                        logger.warning(f"VLNV mismatch for {target}: catalog {expected} vs file {actual}")
                    ordered.setdefault(target_name, None)
                    visit(target_name)
                except Exception as exc:
                    logger.warning(f"Cannot read catalog target {target}: {exc}")
        except Exception as exc:
            logger.warning(f"Cannot discover catalog dependencies in {file_name}: {exc}")
        finally:
            active.remove(file_name)
            visited.add(file_name)

    reported_count = len(ordered)
    for index, file_name in enumerate(files, start=1):
        visit(file_name)
        if progress is not None:
            progress("reading_documents", index, len(files))
        if progress is not None and len(ordered) > reported_count:
            reported_count = len(ordered)
            progress("discovering", reported_count, 0)
    return list(ordered), parsed


def _register_root(doc: XmlDocument) -> VLNV | None:
    """Register root object of `doc` in the global registry.

    Returns the VLNV used for registration when available.
    """
    if doc.tree is None or not _recognized_document(doc.standard, doc.version, doc.root_name):
        return None
    root = doc.tree.getroot()
    vlnv = _extract_vlnv_from_root(root)
    if vlnv is None:
        return None
    # Store vendor/library/name/version and xml_path in a lightweight wrapper
    # without hydrating the XML into a generated xsdata model.
    proxy = _DocumentProxy(*vlnv, str(doc.path))
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
        standard=doc.standard,
        schema_version=doc.version,
    )
    return vlnv


def load_registry_from_paths(
    paths: Iterable[str],
    *,
    cache_dir: Path | None = None,
    progress: ProgressCallback | None = None,
    document_reporter: DocumentReporter | None = None,
) -> None:
    """Scan paths and IPXACT_XML_PATHS, update the global registry.

    Args:
        paths: Iterable of path strings passed on the command line.
        cache_dir: Optional explicit cache directory.
        progress: Optional callback receiving a phase name, current count, and total count.
        document_reporter: Optional callback receiving a path before parsing and detected metadata after parsing.
    """
    search_paths: list[Path] = []
    # CLI provided paths
    for p in paths:
        if p:
            search_paths.append(Path(p).expanduser().resolve())
    # Environment paths (platform path separator)
    env = os.environ.get("IPXACT_XML_PATHS", "")
    for p in (e for e in env.split(os.pathsep) if e):
        search_paths.append(Path(p).expanduser().resolve())
    # De-duplicate while preserving order
    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for p in search_paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)
    if not unique_paths:
        registry.clear()
        _save_cache((cache_dir or _default_cache_dir()) / CACHE_BASENAME, {})
        if progress is not None:
            progress("discovering", 0, 0)
            progress("scanning", 0, 0)
            progress("completed", 0, 0)
        return

    cache_base = cache_dir or _default_cache_dir()
    cache_path = cache_base / CACHE_BASENAME
    cache = _load_cache(cache_path)

    # Compute current file set
    if progress is not None:
        progress("discovering", 0, 0)
    files: list[str] = []
    seen_files: set[str] = set()
    for path in _iter_xml_files(unique_paths):
        file_name = str(path)
        if file_name not in seen_files:
            seen_files.add(file_name)
            files.append(file_name)
            if progress is not None:
                progress("discovering", len(files), 0)
    files, parsed_documents = _discover_catalog_dependencies(files, progress, document_reporter)
    if progress is not None:
        progress("discovering", len(files), len(files))

    # Clear registry; we'll rebuild from current files
    registry.clear()

    new_cache: dict[str, CacheEntry] = {}
    registered: dict[VLNV, str] = {}

    def accept(vlnv: VLNV, file_name: str) -> bool:
        if vlnv in registered:
            logger.warning(f"Duplicate VLNV {vlnv}: keeping {registered[vlnv]}, skipping {file_name}")
            return False
        registered[vlnv] = file_name
        return True

    total = len(files)
    if progress is not None:
        progress("scanning", 0, total)
    for index, f in enumerate(files, start=1):
        if progress is not None:
            progress("scanning", index, total)
        path = Path(f)
        try:
            source_stat = path.stat()
            mtime = source_stat.st_mtime
            fingerprint = _fingerprint(path, source_stat=source_stat)
        except OSError as exc:
            logger.warning(f"Cannot read discovered XML {path}: {exc}")
            continue
        ce = cache.get(f)
        if ce and ce.fingerprint == fingerprint and ce.vlnv:
            # Skip unrecognized editions and non-document roots even if cached
            if not _recognized_document(ce.standard, ce.version, ce.element):
                logger.warning(
                    f"{ARROW} Skipping unsupported XML for scan: '{f}' "
                    f"(detected {ce.standard}/{ce.version}, root {ce.element})"
                )
                continue
            # unchanged; fast register using cached VLNV
            if not accept(ce.vlnv, f):
                continue
            try:
                proxy = _DocumentProxy(*ce.vlnv, str(path))
                # Derive element type from cached element local name
                etype = (ce.element[:1].upper() + ce.element[1:]) if ce.element else None
                registry.register(
                    proxy,
                    ce.vlnv,
                    file_name=f,
                    replace=True,
                    element_type=etype,
                    standard=ce.standard,
                    schema_version=ce.version,
                )
                new_cache[f] = CacheEntry(
                    path=f,
                    mtime=mtime,
                    element=ce.element,
                    standard=ce.standard,
                    version=ce.version,
                    vlnv=ce.vlnv,
                    fingerprint=fingerprint,
                )
                continue
            except Exception:
                # fall through to reparse on any issue
                registered.pop(ce.vlnv, None)

        # Parse fresh
        try:
            doc = parsed_documents.get(f) or _read_document(path, document_reporter)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"{ARROW} Failed parsing '{f}': {exc}")
            continue
        # Filter to recognized standard documents only
        if not _recognized_document(doc.standard, doc.version, doc.root_name):
            logger.warning(
                f"{ARROW} Skipping unsupported XML for scan: '{f}' "
                f"(detected {doc.standard}/{doc.version}, root {doc.root_name})"
            )
            continue
        if doc.tree is not None:
            discovered_vlnv = _extract_vlnv_from_root(doc.tree.getroot())
            if discovered_vlnv is not None and not accept(discovered_vlnv, f):
                continue
        vlnv = _register_root(doc)
        if doc.tree is not None:
            tag_local = etree.QName(doc.tree.getroot()).localname
            standard = doc.standard
            version = doc.version
            new_cache[f] = CacheEntry(
                path=f,
                mtime=mtime,
                element=tag_local,
                standard=standard,
                version=version,
                vlnv=vlnv,
                fingerprint=fingerprint,
            )

    # Persist cache for next run
    _save_cache(cache_path, new_cache)
    if progress is not None:
        progress("completed", total, total)
