""" The scoreboard from INGInious, extended with all the scored attempts of the student.

Enabled instead of inginious.frontend.plugins.scoreboard, as it registers the
same pages, and uses the same `scoreboard` configuration in course.yaml.

The grader stores the score of submissions with `highscore = "private"` in
the custom value "private_score", which the public scoreboard ignores (it only
considers "score"). Below the public scoreboard, the logged in user is shown
a table with only their own attempts, both public and private.
"""
import os

from flask import g, session
from mongoengine import Q

import inginious.frontend.plugins.scoreboard as upstream
from inginious.frontend.courses import Course
from inginious.frontend.models import Submission

TEMPLATES_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates", "scoreboard")


def get_attempts_table(courseid, scoreboardid):
    """
    Retrieves the attempts of the logged in user, that is, their successful
    submissions with a public or private score, sorted with the best first.
    Only scoreboards with a single task are supported.

    :return: A list of rows (submitted on, score, private), or None if the
             user has no attempts.
    """
    try:
        scoreboard = Course.get(courseid).get_descriptor()["scoreboard"][int(scoreboardid)]
    except Exception:  # pylint: disable=broad-except
        return None  # Invalid scoreboards are handled by the public scoreboard
    taskid = scoreboard["content"]
    if not isinstance(taskid, str):
        return None

    submissions = Submission.objects(
        Q(custom__score__exists=True) | Q(custom__private_score__exists=True),
        courseid=courseid, taskid=taskid, username=session.username, result="success",
    ).only("submitted_on", "custom").as_pymongo()

    rows = []
    for submission in submissions:
        private = "private_score" in submission["custom"]
        try:
            score = float(submission["custom"]["private_score" if private else "score"])
        except (TypeError, ValueError):
            continue  # Badly formatted, skipped as in the public scoreboard
        # Show whole numbers without decimals, as the grader stores integers
        score = int(score) if score.is_integer() else score
        rows.append((submission["submitted_on"].strftime("%Y-%m-%d %H:%M:%S"), score, private))

    rows.sort(key=lambda row: row[1], reverse=not scoreboard.get("reverse", False))
    return rows or None


class ScoreBoard(upstream.ScoreBoard):
    """ The public scoreboard, with all the attempts of the user below it """

    def GET_AUTH(self, courseid, scoreboardid):  # pylint: disable=arguments-differ
        """ GET request """
        g.attempts_table = get_attempts_table(courseid, scoreboardid)
        return super().GET_AUTH(courseid, scoreboardid)


def init(plugin_manager, _2, _3):
    """
    Init the plugin. Enabled in configuration.yaml with the following,
    instead of inginious.frontend.plugins.scoreboard:
    ::

        - plugin_module: ntnu_inginious.scoreboard
    """
    plugin_manager.add_page("/scoreboard/<courseid>", upstream.ScoreBoardCourse.as_view("scoreboardcourse"))
    plugin_manager.add_page("/scoreboard/<courseid>/<scoreboardid>", ScoreBoard.as_view("scoreboard"))
    plugin_manager.add_hook("course_menu", upstream.course_menu)
    plugin_manager.add_hook("task_menu", upstream.task_menu)

    # The templates "scoreboard/..." are served from this plugin if it has them,
    # and otherwise from INGInious. The templates of INGInious are also served
    # as "scoreboard_upstream/...", so that this plugin can extend them.
    plugin_manager.add_template_prefix("scoreboard", [TEMPLATES_PATH, upstream.PATH_TO_PLUGIN])
    plugin_manager.add_template_prefix("scoreboard_upstream", upstream.PATH_TO_PLUGIN)
