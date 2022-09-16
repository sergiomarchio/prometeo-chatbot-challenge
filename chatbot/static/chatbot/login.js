function toggleModal(event, modal) {
    modal.classList.toggle("modal-show");
}

function focusInput() {
    input_field.focus();
}

function backgroundClick(event) {
    if(event.target.classList.contains("modal")) {
        toggleModal(event, event.target);
    }

    if(event.target.id == "login-modal") {
        clearInput();
    }
}

function clearInput() {
    input_field.value = "";
}


const guest_button = document.getElementById("guest-button");
const login_button = document.getElementById("login-button");

const guest_modal = document.getElementById("guest-modal");
const login_modal = document.getElementById("login-modal");

const input_field = document.getElementById("input-field");


guest_button.addEventListener("click", (e) => toggleModal(e, guest_modal));
login_button.addEventListener("click", (e) => {
    toggleModal(e, login_modal);
    focusInput();
});

guest_modal.querySelector(".close").addEventListener("click", (e) => toggleModal(e, guest_modal));
login_modal.querySelector(".close").addEventListener("click", (e) => {
    toggleModal(e, login_modal);
    clearInput();
    });

window.addEventListener("click", backgroundClick);

window.addEventListener("unload", clearInput);

