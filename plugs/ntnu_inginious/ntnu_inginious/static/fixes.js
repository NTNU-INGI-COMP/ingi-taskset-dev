document.addEventListener("DOMContentLoaded", removeCurrentGrade);
document.addEventListener("DOMContentLoaded", removeMarketplace);
document.addEventListener("DOMContentLoaded", removeSignIn);
document.addEventListener("DOMContentLoaded", removeSave);

function removeCurrentGrade() {
    // Select the progress element that we do not use
    elements = document.getElementsByClassName("progress mb-3");

    // If there are not exactly one element, then there either is no progress
    // element or something is funcy. So only delete when there is one element.
    if (elements.length == 1) {
        element = elements[0];
        element.previousElementSibling.remove();
        element.remove();
    }
}

function removeMarketplace() {
    // Select the marketplace icon (only used for this specific purpose)
    elements = document.getElementsByClassName("fa fa-shopping-bag fa-fw");

    // If there are not exactly one element, then there either is no marketplace
    // element or something is funcy. So only delete when there is one element.
    if (elements.length == 1) {
        element = elements[0];
        // Want to delete the parent element (the menu item)
        element.parentElement.remove();
    }
}

function removeSignIn() {
    // Select the address book icon on "Sign in with" page
    elements = document.getElementsByClassName("fa fa-address-book");

    if (elements.length == 1) {
        elements[0].click();
    }
}

function removeSave() {
    // Remove save and load buttons to avoid potential confusion in cases where
    // students think they have delivered by pressing the save icon.
    document.getElementById("save_loc").remove();
    document.getElementById("load_loc").remove();
}
