const test_pattern = /^.*\/course\/([^\/]*)\/([^/?]*)/;
let match = window.location.pathname.match(test_pattern);

if (match && match.length == 3) {
    let task_number = match[1];
    let course = match[2];

    if (localStorage.getItem(course) == null) {
        localStorage.setItem(course, "{}");
    }
    let data = JSON.parse(localStorage.getItem(course))[task_number];
    if (data === undefined) {
        data = [];
    }

    $(document).ready(function () {
        if (isMultipleChoice()) {
            setupSaveButton();
            if (isTestUnanswered()) {
                loadAnswers();
            }
        }
    });

    function isTestUnanswered() {
        let empty = true;
        $(".panel-default").find("input[type=checkbox], input[type=radio]").each(function() {
            if($(this).prop('checked')) {
                empty = false;
            }
        });
        return empty;
    }

    function isMultipleChoice() {
        return $(".panel-default").find("input[type=checkbox], input[type=radio]").length > 0;
    }


    function loadAnswers() {
        data.forEach(function(value) {
            $(`input[name=${value.name}][value=${value.value}]`).prop('checked', value.checked);
        });
    }

    function saveAnswers() {
        data = [];
        $(".panel-default").find("input[type=checkbox], input[type=radio]").each(function () {
            data.push({
                name: $(this).prop("name"),
                value: $(this).val(),
                checked: $(this).prop('checked'),
            });
        });

        let courseData = JSON.parse(localStorage.getItem(course));
        courseData[task_number] = data;
        localStorage.setItem(course, JSON.stringify(courseData));

        let alert = $("#save-success-alert");
        if (alert.length === 0) {
            alert = $("<div id='save-success-alert' class='alert alert-success'></div>");
            alert.text("You answers have been saved successfully. They will be loaded each time you access this task on this computer.");
            alert.insertAfter($("#messages"));
        }
        $("html, body").animate({
            scrollTop: alert.offset().top - 100
        }, 200);
    }

    function setupSaveButton() {
        let saveButton = $("<button type='button' class='btn btn-block btn-info center-block btn-lg'>Save without submitting</button>");
        let submitButton = $("#task-submit");

        saveButton.click(saveAnswers);

        let saveRow = $("<div>").toggleClass("row").append($("<div>").toggleClass("col-xs-12").append(saveButton));

        saveRow.insertBefore(submitButton.closest(".row"));
    }
}
