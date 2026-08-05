import os

from flask import send_from_directory, request
from inginious.frontend.pages.utils import INGIniousPage
import flask



PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))

class StaticMockPage(INGIniousPage):
    """ Standard INGInious static page handler """

    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)


def init(plugin_manager, _2, _3):
    """ Init the plugin """
    plugin_manager.add_page(
        "/plugins/ntnu_inginious/static/<path:path>",
        StaticMockPage.as_view("ntnuinginiousstaticpage"),
    )
    plugin_manager.add_hook(
        "javascript_header",
        lambda: request.url_root + "plugins/ntnu_inginious/static/fixes.js",
    )
