function toggleModal(event, modal) {
    modal.classList.toggle("modal-show");

    if(modal.id == "login-modal") {
        clearInput();
    }
}

function focusInput() {
    input_field.focus();
}

function backgroundClick(event) {
    if(event.target.classList.contains("modal")) {
        toggleModal(event, event.target);
    }
}

function clearInput() {
    input_field.value = "";
}

function hideModals() {
    if (guest_modal.classList.contains("modal-show")) {
        toggleModal(null, guest_modal);
    }
    if (login_modal.classList.contains("modal-show")) {
        toggleModal(null, login_modal);
    }
}

const guest_button = document.getElementById("guest-button");
const login_button = document.getElementById("login-button");

const guest_modal = document.getElementById("guest-modal");
const login_modal = document.getElementById("login-modal");

const input_field = document.getElementById("input-field");


guest_button.addEventListener("click", (e) => toggleModal(e, guest_modal));
login_button.addEventListener("click", (e) => {
    toggleModal(e, login_modal);
    setTimeout(focusInput, 100);
});

guest_modal.querySelector(".close").addEventListener("click", (e) => toggleModal(e, guest_modal));
login_modal.querySelector(".close").addEventListener("click", (e) => toggleModal(e, login_modal));

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        hideModals();
    }
});

window.addEventListener("click", backgroundClick);

window.addEventListener("unload", clearInput);
