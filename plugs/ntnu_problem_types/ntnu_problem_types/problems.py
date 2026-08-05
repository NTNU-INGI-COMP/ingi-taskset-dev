from inginious.common.tasks_problems import (
    CodeProblem,
    MultipleChoiceProblem,
    Problem,
    MatchProblem,
)
from inginious.frontend.parsable_text import ParsableText
from inginious.frontend.task_problems import (
    DisplayableCodeProblem,
    DisplayableMultipleChoiceProblem,
    DisplayableProblem,
    DisplayableMatchProblem,
)
import os
from random import Random

from flask import render_template

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_FOLDER = os.path.join(PATH_TO_PLUGIN, "templates")

TEMPLATE_PREFIX="ntnu_problem_types/"


class AlgCodeProblem(CodeProblem):
    """
    Problem definition for the backend. Inherits from the standard
    "code" problem type. No changes are really made here, as the
     problems don't actually filter there data when initializing from
    the YAML file.
    """

    @classmethod
    def get_type(cls):
        return "algcode"


class DisplayableAlgCodeProblem(AlgCodeProblem, DisplayableCodeProblem):
    """
    Problem definition for the frontend. Inherits from the standard
     "code" problem type.
    """

    @classmethod
    def get_type_name(cls, language):
        return "algcode"

    @classmethod
    def show_editbox(cls, key, language):
        """
        Returns the HTML render for the edit box in the admin panel.

        :param key: The problem key, e.g., "algcode".
        :param language: The language to render the template in.
        :return: The HTML render for the admin portion of the "algcode"
                 problem type.
        """
        # Render the standard "code" problem type and include that HTML
        # in the rendering of the "algcode" problem type.
        base_code_edit_render = DisplayableCodeProblem.show_editbox(
            "code", language
        )

        return render_template("ntnu_problem_types/algcode_edit.html",
                template_folder=TEMPLATE_PREFIX, key=key,
                base_code_edit_render=base_code_edit_render)


class WeightedMultipleChoiceProblem(MultipleChoiceProblem):
    """
    A weighted variant of the standard multiple choice problem type.
    """

    @classmethod
    def get_type(cls):
        return "weighted_multiple_choice"

    def input_is_consistent(
        self, task_input, default_allowed_extension, default_max_size
    ):
        """
        The task is optional, which means that not being answered is
        also allowed.
        """
        if task_input[self.get_id()] is None or task_input[self.get_id()] == []:
            return True
        return super().input_is_consistent(
            task_input, default_allowed_extension, default_max_size
        )


class DisplayableWeightedMultipleChoiceProblem(
    WeightedMultipleChoiceProblem, DisplayableMultipleChoiceProblem
):
    """
    A weighted variant of the standard multiple choice problem type
    """

    @classmethod
    def get_type_name(cls, language):
        # The type name is the display name. It may vary from the value
        # of "get_type".
        return "weighted multiple choice"

    @classmethod
    def show_editbox(cls, key, language):
        """
        Returns the HTML render for the edit box in the admin panel.

        :param key: The problem key, e.g., "weighted_multiple_choice".
        :param language: The language to render the template in.
        :return: The HTML render for the admin portion of the
                 "weighted_multiple_choice" problem type.
        """
        # Render the standard "multiple_choice" problem type and
        # include that HTML in the rendering of the
        # "weighted_multiple_choice" problem type.
        base_edit_render = DisplayableMultipleChoiceProblem.show_editbox(
            "multiple_choice", language
        )
        return render_template("ntnu_problem_types/weighted_multiple_choice_edit.html",
                template_folder=TEMPLATE_PREFIX, key=key,
                base_multiple_choice_edit_render=base_edit_render)

    def show_input(self, language, seed):
        """
        Returns the HTML render for the problem, as will be displayed
        to the student. The function is an adapted version of the
        function of its parent.

        :param language: The display language (not used)
        :param seed: The seed to be used for randomization
        :return: The HTML render for the `text` problem type, as
                 displayed to the student
        """
        choices = []
        limit = self._limit
        if limit == 0:
            limit = len(self._choices)  # no limit

        rand = Random(
            "{}#{}#{}".format(self.get_id(), language, seed)
        )

        # Ensure that the choices are random
        # we *do* need to copy the choices here
        random_order_choices = list(self._choices)
        rand.shuffle(random_order_choices)

        if self._multiple:
            # take only the valid choices in the first pass
            for entry in random_order_choices:
                if entry["valid"]:
                    choices.append(entry)
                    limit = limit - 1
            # take everything else in a second pass
            for entry in random_order_choices:
                if limit == 0:
                    break
                if not entry["valid"]:
                    choices.append(entry)
                    limit = limit - 1
        else:
            # need to have ONE valid entry
            for entry in random_order_choices:
                if not entry["valid"] and limit > 1:
                    choices.append(entry)
                    limit = limit - 1
            for entry in random_order_choices:
                if entry["valid"] and limit > 0:
                    choices.append(entry)
                    limit = limit - 1

        rand.shuffle(choices)

        header = ParsableText(
            self.gettext(language, self._header),
            "rst"
        )

        return render_template("ntnu_problem_types/weighted_multiple_choice.html",
                template_folder=TEMPLATE_PREFIX, pid=self.get_id(),
                header=header, checkbox=self._multiple, choices=choices,
                func = lambda text: ParsableText(
                    self.gettext(language, text) if text else "", "rst"
            ))


class TextProblem(Problem):
    """
    A problem type that has a single text field for an answer. This is
    mainly meant for open-ended problems, that will not necessarily be
    corrected.
    """

    def __init__(self, problemid, content, translations, taskfs):
        super().__init__(problemid, content, translations, taskfs)
        self._header = content.get("header", "")

    @classmethod
    def get_type(cls):
        return "text"

    def input_is_consistent(
        self, task_input, default_allowed_extension, default_max_size
    ):
        # Text problems are not corrected and thus the input is always
        # consistent
        return True

    def input_type(self):
        return str

    def check_answer(self, task_input, language):
        # All answers are assumed to be valid
        return True, None, None, 0

    @classmethod
    def get_text_fields(cls):
        fields = Problem.get_text_fields()
        # The header must be marked as reST.
        fields.update({"header": True})
        return fields


class DisplayableTextProblem(TextProblem, DisplayableProblem):
    """
    A problem type that has a single text field for an answer. This is
    mainly meant for open-ended problems, that will not necessarily be
    corrected.
    """

    @classmethod
    def get_type_name(cls, language):
        return "Text"

    def show_input(self, language, seed):
        """
        Returns the HTML render for the problem, as will be displayed
        to the student

        :param language: The display language (not used)
        :param seed: The seed to be used for randomization
        :return: The HTML render for the `text` problem type, as
                 displayed to the student
        """
        # The header is reST and must be parsed as such
        header = ParsableText(
            self.gettext(language, self._header),
            "rst"
        )
        return render_template("ntnu_problem_types/text.html", header=header,
                template_folder=TEMPLATE_PREFIX, inputID=self.get_id())

    @classmethod
    def show_editbox(cls, key, language):
        """
        Returns the HTML render for the edit box in the admin panel

        :param key: The problem key
        :param language: The display language (not used)
        :return: The HTML render for the `text` problem type, as
                 displayed in the admin panel
        """
        return render_template("ntnu_problem_types/text_edit.html",
                template_folder=TEMPLATE_PREFIX, key=key)

    @classmethod
    def show_editbox_templates(cls, key, language):
        return ""


class ReflectionProblem(TextProblem):
    """
    A special problem type, derived from the text problem type, meant
    for reflection tasks.
    """

    @classmethod
    def get_type(cls):
        return "reflection"


class DisplayableReflectionProblem(ReflectionProblem, DisplayableTextProblem):
    def show_input(self, language, seed):
        """
        Returns the HTML render for the problem, as will be displayed
        to the student. Differs from the `text` problem type, by adding
        an alert box containing standardized information about the
        reflection tasks.

        :param language: The display language (not used)
        :param seed: The seed to be used for randomization
        :return: The HTML render for the `reflection` problem type, as
                 displayed to the student
        """
        header = ParsableText(
            self.gettext(language, self._header), "rst"
        )
        return render_template("ntnu_problem_types/reflection.html",
                template_folder=TEMPLATE_PREFIX, inputID=self.get_id(),
                header=header)


class ExactProblem(MatchProblem):
    """
    A wrapper of `MatchProblem`, making the problem optional.
    """

    @classmethod
    def get_type(cls):
        return "exact"

    def input_is_consistent(
        self, task_input, default_allowed_extension, default_max_size
    ):
        """
        The task is optional, which means that not being answered is
        also allowed.
        """
        if task_input[self.get_id()] is None or task_input[self.get_id()] == []:
            return True
        return super().input_is_consistent(
            task_input, default_allowed_extension, default_max_size
        )

    def check_answer(self, task_input, language):
        if task_input.get(self.get_id(), "").strip() == self._answer:
            return True, None, ["_correct_answer"], 0, ""
        else:
            return False, None, ["_wrong_answer"], 0, ""


class DisplayableExactProblem(ExactProblem, DisplayableMatchProblem):
    """
    A wrapper of MatchProblem, making it optional to answer
    """

    @classmethod
    def get_type_name(cls, language):
        return "Exact"

    def show_input(self, language, seed):
        """
        This method specifies that we use the `exact.html`-template,
        and not the `match`-template, so that we can add the attribute
        `data-optional="True"` to the `<input>`, making the  assignment
        voluntary to answer.
        """
        header = ParsableText(
            self.gettext(language, self._header),
            "rst"
        )
        return render_template("ntnu_problem_types/exact.html",
                template_folder=TEMPLATE_PREFIX, inputID=self.get_id(),
                header=header)


class InformationBox(Problem):
    """
    A problem type that is not actually a problem. This problem type is
    simply meant to give the option of adding tasks without input. That
    is boxes filled with information.
    """

    def __init__(self, problemid, content, translations, taskfs):
        super().__init__(problemid, content, translations, taskfs)
        self._header = content.get("header", "")

    @classmethod
    def get_type(cls):
        return "information_box"

    def input_is_consistent(
        self, task_input, default_allowed_extension, default_max_size
    ):
        # The input must be consistent, as there is never any input
        return True

    def input_type(self):
        return str

    def check_answer(self, task_input, language):
        # No need to check an answer when there is no answer
        return True, None, None, 0

    @classmethod
    def get_text_fields(cls):
        fields = Problem.get_text_fields()
        fields.update({"header": True})
        return fields


class DisplayableInformationBox(InformationBox, DisplayableProblem):
    """
    A problem type that is not actually a problem. This problem type is
    simply meant to give the option of adding tasks without input. That
    is boxes filled with information.
    """

    @classmethod
    def get_type_name(cls, language):
        return "Information Box"

    def show_input(self, language, seed):
        """
        Returns the HTML render for the problem, as will be displayed
        to the student

        :param language: The display language (not used)
        :param seed: The seed to be used for randomization
        :return: The HTML render for the `information` problem type, as
                 displayed to the student
        """
        # The header is reST and must be parsed accordingly
        header = ParsableText(
            self.gettext(language, self._header),
            "rst"
        )
        return render_template("ntnu_problem_types/information_box.html",
                template_folder=TEMPLATE_PREFIX, inputID=self.get_id(),
                header=header)

    @classmethod
    def show_editbox(cls, key, language):
        """
        Returns the HTML render for the edit box in the admin panel

        :param key: The problem key
        :param language: The display language (not used)
        :return: The HTML render for the `reflection` problem type, as
                 displayed in the admin panel
        """
        return render_template("ntnu_problem_types/information_box_edit.html",
                template_folder=TEMPLATE_PREFIX, key=key)

    @classmethod
    def show_editbox_templates(cls, key, language):
        return ""
