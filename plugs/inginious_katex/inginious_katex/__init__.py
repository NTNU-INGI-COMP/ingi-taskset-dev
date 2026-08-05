import os

from docutils import nodes
from docutils.parsers.rst import roles
from flask import send_from_directory, request
from inginious.frontend.pages.utils import INGIniousPage

import flask


__version__ = "0.2"

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))


class StaticMockPage(INGIniousPage):
    """ Standard INGInious static page handler """

    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)


def katex_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    """Custom docutils role function"""
    # Add custom CSS class
    options.update({"classes": ["katex-pre-render"]})
    # Pick the part of the text that is between ``
    # (format ":katex:`\LaTeX`")
    text = rawtext.split("`")[1]
    node = nodes.inline(rawtext, text, **options)
    return [node], []


def init(plugin_manager, _2, _3):
    """ Init the plugin """
    plugin_manager.add_page(
        "/plugins/inginious_katex/static/<path:path>",
        StaticMockPage.as_view("katexstaticpage"),
    )
    plugin_manager.add_hook(
        "javascript_header",
        lambda: "https://cdn.jsdelivr.net/npm/katex@0.13.11/dist/katex.min.js",
    )
    plugin_manager.add_hook(
        "javascript_header",
        lambda: request.url_root + "/plugins/inginious_katex/static/load_katex.js",
    )
    plugin_manager.add_hook(
        "css",
        lambda: "https://cdn.jsdelivr.net/npm/katex@0.13.11/dist/katex.min.css",
    )

    # Add the custom role function as ":katex:``" in the reST handler
    roles.register_local_role("katex", katex_role)
