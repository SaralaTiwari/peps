"""Sphinx extensions for performant PEP processing"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes
from docutils.parsers.rst import states
from docutils.writers.html5_polyglot import HTMLTranslator
from sphinx import environment

from pep_sphinx_extensions.pep_processor.html import pep_html_builder
from pep_sphinx_extensions.pep_processor.html import pep_html_translator
from pep_sphinx_extensions.pep_processor.parsing import pep_parser
from pep_sphinx_extensions.pep_processor.parsing import pep_role
from pep_sphinx_extensions.pep_zero_generator.pep_index_generator import create_pep_zero

if TYPE_CHECKING:
    from sphinx.application import Sphinx

# Monkeypatch sphinx.environment.default_settings as Sphinx doesn't allow custom settings or Readers
# This disables reading configuration from docutils.conf so as not to affect pep2html.py
environment.default_settings["_disable_config"] = True


def _depart_maths():
    pass  # No-op callable for the type checker


def _update_config_for_builder(app: Sphinx):
    if app.builder.name == "dirhtml":
        app.env.settings["pep_url"] = "../pep-{:0>4}"


def setup(app: Sphinx) -> dict[str, bool]:
    """Initialize Sphinx extension."""

    environment.default_settings["pep_url"] = "pep-{:0>4}.html"
    environment.default_settings["halt_level"] = 2  # Fail on Docutils warning

    # Register plugin logic
    app.add_builder(pep_html_builder.FileBuilder, override=True)
    app.add_builder(pep_html_builder.DirectoryBuilder, override=True)

    app.add_source_parser(pep_parser.PEPParser)  # Add PEP transforms

    app.set_translator("html", pep_html_translator.PEPTranslator)  # Docutils Node Visitor overrides (html builder)
    app.set_translator("dirhtml", pep_html_translator.PEPTranslator)  # Docutils Node Visitor overrides (dirhtml builder)

    app.add_role("pep", pep_role.PEPRole(), override=True)  # Transform PEP references to links

    # Register event callbacks
    app.connect("builder-inited", _update_config_for_builder)  # Update configuration values for builder used
    app.connect("env-before-read-docs", create_pep_zero)  # PEP 0 hook

    # Mathematics rendering
    inline_maths = HTMLTranslator.visit_math, _depart_maths
    block_maths = HTMLTranslator.visit_math_block, _depart_maths
    app.add_html_math_renderer("maths_to_html", inline_maths, block_maths)  # Render maths to HTML

    # Parallel safety: https://www.sphinx-doc.org/en/master/extdev/index.html#extension-metadata
    return {"parallel_read_safe": True, "parallel_write_safe": True}
