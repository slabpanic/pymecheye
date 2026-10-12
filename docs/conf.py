"""Build documentation from the installed native binding and its public docstrings."""

from importlib.metadata import version as package_version
import os
from pathlib import Path
import sys

DOCS = Path(__file__).resolve().parent
sys.path.insert(0, str(DOCS / "_ext"))

from generate_api import generate_api

project = "pymecheye"
author = "pymecheye contributors"
copyright = "2026, pymecheye contributors"
release = package_version("pymecheye")
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "en"
nitpicky = True
autosummary_generate = True
autodoc_typehints = "none"
autodoc_member_order = "bysource"
autodoc_inherit_docstrings = True
html_theme = "furo"
html_title = f"{project} {release}"
html_baseurl = os.environ.get(
    "READTHEDOCS_CANONICAL_URL", "https://pymecheye.readthedocs.io/en/latest/"
)


# Generate inventories before Sphinx discovers source documents. Do not mock the
# native module: SDK descriptors and dynamic classes must be real for autodoc.
generate_api(DOCS)


def public_signature(app, what, name, obj, options, signature, return_annotation):
    """Hide closure-capture arguments on generated no-argument SDK accessors."""
    if getattr(obj, "__name__", "") in {"<lambda>", "_range"}:
        return "()", return_annotation
    return None


def setup(app):
    app.connect("autodoc-process-signature", public_signature)
