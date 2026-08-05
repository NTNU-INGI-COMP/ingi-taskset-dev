document.addEventListener("DOMContentLoaded", renderKaTeX);

function renderKaTeX() {
    let katex_elements = Array.from(document.getElementsByClassName("katex-pre-render"));

    function smallCaps(context) {
        // `\textsc` take a single argument
        let arg = context.consumeArgs(1)[0];
        // Reverse the argument, as it consists of tokens given in reverse (tokenizer: {ABC} => ["C", "B", "A"])
        arg.reverse();

        // Combine the tokens to a single string
        let string = arg.map(token => token.text).join("")

        // Replace lowercase letters with smaller uppercase letters
        let lowercase = /([a-z]+)/g
        string = string.replace(lowercase, (_, match) => "{\\scriptsize " + match.toUpperCase() + "}")

        // Return the string without any formatting
        return "\\textrm{" + string + "}"
    }

    let macros = {
        "\\textsc": smallCaps,
        "\\le": "\\leqslant",
        "\\leq": "\\leqslant",
        "\\ge": "\\geqslant",
        "\\geq": "\\geqslant",
        "\\pr": "\\textsc",
        "\\cn": "\\textsc",
        "\\id": "\\textit",
    }


    // Add macros for french style
    let capitals = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    for (let index = 0; index < capitals.length; index++) {
        macros[capitals[index]] = "{\\char " + (65 + index) + "}";
    }


    for (let index = 0; index < katex_elements.length; index++) {
        let element = katex_elements[index];
        katex.render(element.innerText, element, {
            macros: macros,
            throwOnError: false,
        });

        // Remove the class after rendering, so that the rendering function can be called several times
        element.classList.remove("katex-pre-render");
    }
}

// Allow KaTeX rendering in the reST feedback. Overrides the original function, by creating a new function that first
// calls the original function and then calls the KaTeX renderer.
displayTaskStudentAlertWithProblems = (function (original) {
    return function () {
        // Pass along all the arguments. Then we don't need to assume anything about the original function.
        original.apply(null, arguments);
        renderKaTeX();
    }
})(displayTaskStudentAlertWithProblems);
