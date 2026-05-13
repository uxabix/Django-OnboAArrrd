# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from __future__ import annotations

import os
import sys
from pathlib import Path

# Project root (parent of docs/)
_DOCS_DIR = Path(__file__).resolve().parent
_ROOT = _DOCS_DIR.parent
sys.path.insert(0, str(_ROOT))

# Minimal environment so Django settings load during doc builds without a real DB.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OnboAArrrd.settings")
if not os.environ.get("POSTGRES_DB"):
    os.environ.setdefault("SECRET_KEY", "sphinx-doc-build-only")
    os.environ.setdefault("POSTGRES_DB", "sphinx")
    os.environ.setdefault("POSTGRES_USER", "sphinx")
    os.environ.setdefault("POSTGRES_PASSWORD", "sphinx")
    os.environ.setdefault("POSTGRES_HOST", "127.0.0.1")
    os.environ.setdefault("POSTGRES_PORT", "5432")

import django  # noqa: E402

django.setup()

project = "OnboAArrrd"
copyright = "OnboAArrrd contributors"
author = "OnboAArrrd contributors"
release = "0.1.0"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

autosummary_generate = False
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": False,
    "inherited-members": False,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", "https://docs.djangoproject.com/en/stable/_objects/"),
}
