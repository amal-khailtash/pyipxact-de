# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path


# def _add_src_to_sys_path() -> None:
#     """Add the repository src/ directory to sys.path for autodoc imports.

#     This makes packages under src/ (e.g., amal.utilities, amal.eda.ipxact_de, accellera.*)
#     importable when Sphinx imports modules for autodoc.
#     """
#     src = (Path(__file__).resolve().parents[1] / "src")
#     src_str = str(src)
#     if src_str not in sys.path:
#         sys.path.insert(0, src_str)

# _add_src_to_sys_path()

src = (Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, str(src))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Accellera IP-XACT DE (Design Environment)'
copyright = '©2025, Amal Khailtash'
author = 'Amal Khailtash'
# The full version, including alpha/beta/rc tags
version = "__version__"
release = "get_pypi_version(project)"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.mathjax',
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    'sphinx.ext.autosectionlabel',
    'sphinx_rtd_theme',
    'sphinx.ext.napoleon',
    'sphinx_contributors',
    'sphinx_github_changelog',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']


# -- Extension configuration -------------------------------------------------
html_show_sourcelink = False
html_logo = "_static/logo-navbar.png"

html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',  #  Provided by Google in your dashboard
    'logo_only': True,
    # 'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 2,
    'includehidden': True,
    'titles_only': False,
}

html_context = {
    'display_github': True,           # Integrate GitHub
    'github_user': 'amal-khailtash',  # Username
    'github_repo': "pyipxact-de",     # Repo name
    'github_version': 'main',         # Version
    'conf_py_path': '/docs/',         # Path in the checkout to the docs root
}
html_favicon = '_static/logo.svg'


# -- autodoc configuration -------------------------------------------------

# Make autodoc more helpful and resilient.
autodoc_default_options: dict[str, bool] = {
    "members": True,
    "undoc-members": True,
    "inherited-members": True,
    "show-inheritance": True,
}
autodoc_typehints: str = "description"  # keep signatures clean
napoleon_google_docstring: bool = True
napoleon_numpy_docstring: bool = False

# # Mock optional/heavy imports that may not be present at doc build time.
# def _compute_autodoc_mock_imports(modules: list[str]) -> list[str]:
#     """Return the subset of modules that are not importable and should be mocked."""
#     missing: list[str] = []
#     for mod in modules:
#         try:
#             __import__(mod)
#         except Exception:
#             missing.append(mod)
#     return missing

# # Extend this list as needed if autodoc import warnings appear.
# _optional_modules: list[str] = [
#     "PyQt5",
#     "qtpy",
#     "qtawesome",
#     "fastapi",
#     "pydantic",
#     "uvicorn",
#     "starlette",
#     "anyio",
#     "sniffio",
#     "orjson",
#     "ujson",
#     "lxml",  # if not installed locally
# ]
# autodoc_mock_imports: list[str] = _compute_autodoc_mock_imports(_optional_modules)
