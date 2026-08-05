/**
 * The function called by INGInious' frontend in the admin panel. This function is responsible for initializing the
 * problem values into the input fields in the admin panel. This function is called whenever a problem of the type
 * "algcode" is encountered.
 *
 * @param well The jQuery (HTML) object representing the part of the admin panel corresponding to the problem.
 * @param pid The unique identifier for the problem (given in the YAML file).
 * @param problem A dictionary containing all the data of the given problem (all properties in the YAML file).
 */
function studio_init_template_algcode(well, pid, problem) {
    // The "algcode" problem type, along with its HTML, inherits from the standard "code" problem type. Thus, we call
    // the initialization function for the fields of the "code" problem type.
    studio_init_template_code(well, pid, problem);

    if ("test_file" in problem) {
        $("#test_file-" + pid, well).val(problem["test_file"]);
    }

    if ("memory_limit" in problem) {
        $("#memory_limit-" + pid, well).val(problem["memory_limit"]);
    }

    if ("time_limit" in problem) {
        $("#time_limit-" + pid, well).val(problem["time_limit"]);
    }

    let default_template = $("#template-default-" + pid, well);
    let template_source = $("#template-source-" + pid, well);

    // Whenever the "template.default" field is checked/unchecked, make the "template.source" field
    // unavailable/available. This, as the "template.source" field is ignored if the "template.default" field is "on".
    default_template.change((event) => {
        let is_checked = default_template.is(":checked");
        template_source.attr("disabled", is_checked);
    });

    if ("template" in problem && "default" in problem["template"]) {
        default_template.attr("checked", problem["template"]["default"]);
        template_source.attr("disabled", problem["template"]["default"]);
    }

    if ("template" in problem && "source" in problem["template"]) {
        template_source.val(problem["template"]["source"]);
    }

    if ("template" in problem && "output" in problem["template"]) {
        $("#template-output-" + pid, well).val(problem["template"]["output"]);
    }

    if ("weight" in problem) {
        $("#weight-" + pid, well).val(problem["weight"]);
    }

    if ("highscore_test_file" in problem) {
        $("#highscore_test_file-" + pid, well).val(problem["highscore_test_file"])
    }

    if ("highscore_runs" in problem) {
        $("#highscore_runs-" + pid, well).val(problem["highscore_runs"])
    }
}

/**
 * The function called by INGInious' frontend in the admin panel. This function is responsible for initializing the
 * problem values into the input fields in the admin panel. This function is called whenever a problem of the type
 * "weighted_multiple_choice" is encountered.
 *
 * @param well The jQuery (HTML) object representing the part of the admin panel corresponding to the problem.
 * @param pid The unique identifier for the problem (given in the YAML file).
 * @param problem A dictionary containing all the data of the given problem (all properties in the YAML file).
 */
function studio_init_template_weighted_multiple_choice(well, pid, problem) {
    studio_init_template_multiple_choice(well, pid, problem);

    if ("weight" in problem) {
        $("#weight-" + pid, well).val(problem["weight"]);
    }
}

function studio_init_template_text(well, pid, problem) {
    if ("header" in problem) {
        $("#header-" + pid, well).val(problem["header"]);
    }
}

studio_init_template_reflection = studio_init_template_text;
studio_init_template_exact = studio_init_template_match;

function studio_init_template_information_box(well, pid, problem) {
    if ("header" in problem) {
        $("#header-" + pid, well).val(problem["header"]);
    }
}

// In the same way that studio_init_template_<problem_type> is called in the admin panel, load_input_<problem_type> is
// called when a task is viewed. This function must initialize the task fields with prior or default data. Since
// "algcode" does not change how a task is viewed in a task, we simply assign the function to be the same as for "code"
// problems. The same goes for "weighted_multiple_choice", "reflection" and "exact" problems.
load_input_algcode = load_input_code;
load_input_weighted_multiple_choice = load_input_multiple_choice;
load_input_exact = load_input_match;
load_input_reflection = load_input_text;

function load_input_text(submissionid, key, input) {
    let field = $("textarea[name='" + key + "']");
    if (key in input) {
        field.val(input[key]);
    } else {
        field.val("");
    }
}


// There will never be any input in the information
load_input_information_box = () => null;

// In the same way that load_input_<problem_type> is called when a task is viewed, load_feedback_<problem_type> is
// called when feedback should be displayed for a task. Since neither "algcode", "exact" nor "weighted_multiple_choice"
// change how a task is displayed, we simply assign the function to be the same as for "code" and
// "weighted_multiple_choice" problems.
load_feedback_algcode = load_feedback_code;
load_feedback_weighted_multiple_choice = load_feedback_multiple_choice;
load_feedback_exact = load_feedback_match;

// Let load_feedback_text and load_feedback_information_box be empty function. There should be no feedback for a task
// that cannot be corrected directly in the INGInious system.
load_feedback_text = () => null;
// This is a hack used to fix the display of the green/red box with simple feedback.
load_feedback_reflection = load_feedback_multiple_choice;
load_feedback_information_box = () => null;


// Modified version of taskFormValid that INGInious use, with the change that checkboxes and radio buttons are also
// allowed to have 
function taskFormValid()
{
    var answered_to_all = true;
    var errors = [];
    var form = $('#task');

    form.find('textarea,input[type="text"]').each(function()
    {
        if($(this).attr('name') != undefined) //skip codemirror's internal textareas
        {
            if($(this).val() == "" && $(this).attr('data-optional') != "True")
                answered_to_all = false;
        }
    });

    form.find('input[type="checkbox"],input[type="radio"]').each(function()
    {
        if(form.find("input[name='"+ $(this).attr('name')+"']:checked").length == 0 && $(this).attr("data-optional") != "True")
        {
            answered_to_all = false;
        }
    });

    form.find('input[type="file"]').each(function()
    {
        var filename = $(this).val().split(/(\\|\/)/g).pop();

        //file input fields cannot be optional
        if(filename == "")
        {
            answered_to_all = false;
            return;
        }

        //verify ext
        var allowed_extensions = $.parseJSON($(this).attr('data-allowed-exts'));
        var has_one = false;
        $.each(allowed_extensions, function(idx, ext){
            has_one = has_one || (filename.lastIndexOf(ext) === filename.length - ext.length) > 0;
        });
        if(!has_one)
            errors.push($("#invalidext").text().replace("{}", filename));

        //try to get the size of the file
        var size = -1;
        try { size = $(this)[0].files[0].size; } catch (e) {} //modern browsers
        if(size == -1) try { size = $(this)[0].files[0].fileSize; } catch(e) { } //old versions of Firefox

        //Verify the maximum size
        var max_size = parseInt($(this).attr('data-max-size'));
        if(size != -1 && size > max_size)
            errors.push($("#filetooheavy").text().replace("{}", filename));
    });

    if(!answered_to_all)
    {
        errors.push($("#answerall").text());
    }

    if(errors.length != 0)
    {
        var task_alert = $('#task_alert');
        var content = $('<div></div>');
        var first = true;
        $.each(errors, function(idx, elem){
            if(!first)
                content.append($('<br>'));
            first = false;
            content.append($('<span></span>').text(elem));
        });
        task_alert.html(getAlertCode("Error", content.html(), "danger", false));
        $('html, body').animate({
            scrollTop: task_alert.offset().top - 100
        }, 200);
        return false;
    }
    else
    {
        return true;
    }
}


window.onload = function () {
    let hintButtons = document.getElementsByClassName("alghint-button");
    for (let i = 0; i < hintButtons.length; i++) {
        let hintButton = hintButtons[i];
        hintButton.addEventListener("mouseover", function (event) {
            let container = hintButton.parentElement.lastElementChild;
            container.innerHTML = "";
            let contentContainer = hintButton.nextSibling;
            for (let childNum = 0; childNum < contentContainer.childNodes.length; childNum++) {
                container.appendChild(contentContainer.childNodes[childNum].cloneNode(true));
            }
        })
    }
}
