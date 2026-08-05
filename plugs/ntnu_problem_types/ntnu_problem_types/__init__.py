__version__ = "0.1"

from .problems import (
    DisplayableAlgCodeProblem,
    DisplayableWeightedMultipleChoiceProblem,
    DisplayableTextProblem,
    DisplayableInformationBox,
    DisplayableReflectionProblem,
    DisplayableExactProblem,
)
import os
from docutils import nodes
from docutils.parsers.rst import directives, Directive
from flask import send_from_directory, request
import flask
from inginious.frontend.pages.utils import INGIniousPage


__version__ = "0.2"

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))


class StaticMockPage(INGIniousPage):
    """
    Standard code from INGInious. Used to serve static files from the
    plugin.
    """

    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)

class HintRole(Directive):
    """
    A directive to show hints. The hints are separated by an empty line
    in the content of the directive.
    """

    has_content = True

    def run(self):
        # Split the content on two empty lines to allow for normal reST
        # contexts (one empty line)
        hint_text = "\n".join(self.content).split("\n\n\n")
        hint_nodes = []
        content_offset = self.content_offset
        current_content_offset = 0
        for hint_number, text in enumerate(hint_text):
            # Parse the content of each hint separately and create HTML
            # nodes for it. The nodes are hidden and only copied from
            # when presenting the given hint.
            container = nodes.container("", classes=["alghint-text"])
            # Need to calculate offsets in the content
            current_content_length = len(text.split("\n"))
            content_offset = self.state.nested_parse(
                self.content[
                    current_content_offset : current_content_offset
                    + current_content_length
                ],
                content_offset,
                container,
            )
            # Adds two due to the two empty lines removed between each
            # hint.
            current_content_offset += current_content_length + 2

            hint_nodes += [
                nodes.inline(
                    text,
                    f"Hint {hint_number + 1}",
                    classes=["alghint-button"],
                ),
                container,
            ]

        # Common node for showing content after all the hint buttons
        hint_nodes += [
            nodes.inline(
                "",
                "",
                classes=[
                    "alghint",
                    "admonition",
                    "note",
                    "alert",
                    "alert-light",
                ],
            )
        ]

        return [nodes.container("", *hint_nodes)]


def init(plugin_manager, client, plugin_config):
    plugin_manager.add_page(
        "/plugins/ntnu_problem_types/static/<path:path>",
        StaticMockPage.as_view("ntnuproblemtypesstaticpage"),
    )
    plugin_manager.add_hook(
        "javascript_header",
        lambda: request.url_root + "plugins/ntnu_problem_types/static/ntnu_problem_types.js",
    )
    plugin_manager.add_hook(
        "css",
        lambda: request.url_root + "plugins/ntnu_problem_types/static/ntnu_problem_types.css",
    )

    plugin_manager.add_template_prefix("ntnu_problem_types", PATH_TO_PLUGIN + "/templates")


    # These are autoloaded
    # course_factory.get_task_factory().add_problem_type(
    #     DisplayableAlgCodeProblem
    # )
    # course_factory.get_task_factory().add_problem_type(
    #     DisplayableWeightedMultipleChoiceProblem
    # )
    # course_factory.get_task_factory().add_problem_type(DisplayableTextProblem)
    # course_factory.get_task_factory().add_problem_type(
    #     DisplayableInformationBox
    # )
    # course_factory.get_task_factory().add_problem_type(
    #     DisplayableReflectionProblem
    # )
    # course_factory.get_task_factory().add_problem_type(DisplayableExactProblem)

    directives.register_directive("alghint", HintRole)
