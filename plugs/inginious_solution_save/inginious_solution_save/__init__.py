import os
import web

__version__ = "0.1"
PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))


class StaticMockPage(object):
    def GET(self, path):
        if not os.path.abspath(PATH_TO_PLUGIN) in os.path.abspath(
            os.path.join(PATH_TO_PLUGIN, path)
        ):
            raise web.notfound()

        try:
            with open(
                os.path.join(PATH_TO_PLUGIN, "static", path), "rb"
            ) as file:
                web.header("Content-Type", "text/javascript")
                return file.read()
        except:
            raise web.notfound()


def init(plugin_manager, _2, _3):
    """ Init the plugin """
    plugin_manager.add_page(
        "/plugins/solution-save/static/(.+)", StaticMockPage
    )
    plugin_manager.add_hook(
        "javascript_footer",
        lambda: web.ctx.homepath
        + "/plugins/solution-save/static/solution_save.js",
    )
