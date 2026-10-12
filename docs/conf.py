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
language = os.environ.get("READTHEDOCS_LANGUAGE", "en").replace("-", "_")
if language.lower() == "zh_cn":
    language = "zh_CN"
locale_dirs = ["locale"]
gettext_compact = True
gettext_uuid = False
nitpicky = True
autosummary_generate = True
autodoc_typehints = "none"
autodoc_member_order = "bysource"
autodoc_inherit_docstrings = True
html_theme = "furo"
html_title = f"{project} {release}"
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "language-switcher.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
        "sidebar/variant-selector.html",
    ]
}


def configure_language(app, config):
    """Use the selected Sphinx language in local and hosted canonical URLs."""
    locale = "zh-cn" if config.language == "zh_CN" else "en"
    config.html_baseurl = os.environ.get(
        "READTHEDOCS_CANONICAL_URL",
        f"https://pymecheye.readthedocs.io/{locale}/latest/",
    )


def language_links(app, pagename, templatename, context, doctree):
    """Link the same page in each language for CI previews and Read the Docs."""
    page = app.builder.get_target_uri(pagename)
    links = []
    for code, locale, label in (
        ("en", "en", "English"),
        ("zh_CN", "zh-cn", "简体中文"),
    ):
        if os.environ.get("READTHEDOCS") == "True":
            root = app.config.html_baseurl.rstrip("/").rsplit("/", 2)[0]
            version = os.environ.get("READTHEDOCS_VERSION", "latest")
            url = f"{root}/{locale}/{version}/{page}"
        else:
            url = context["pathto"](f"../{code}/{page}", True)
        links.append((locale, label, url, app.config.language == code))
    context["documentation_languages"] = links
    context["language_title"] = (
        "语言" if app.config.language == "zh_CN" else "Languages"
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
    app.connect("config-inited", configure_language)
    app.connect("html-page-context", language_links)
    app.connect("autodoc-process-signature", public_signature)
