
function processMessageResponse(data) {
    hideMessageSpinner();

    console.log(data);

    if ('message' in data) {
        exitModal();
        addNewMessage(data['message']);
    } else if ('modal-form' in data) {
        showModalForm(data['modal-form']);
    } else if ('modal-feedback' in data) {
        clearAll();
        setModalFeedback(data['modal-feedback']);
    } else {
        addErrorMessage();
    }

}

function clearAll() {
    for (field of modalContent.querySelectorAll(".input-field")) {
        field.value = "";
    }
    modalContent.querySelector(".input-field").focus();
}

function showBaseModal() {
    mainPage.setAttribute("inert", "");
    baseModal.classList.add("modal-show");

    setTimeout(() => {
         modalContent.querySelector(".input-field").focus();
    }, 50);
}

function hideBaseModal() {
    baseModal.classList.remove("modal-show");
    mainPage.removeAttribute("inert");
}

function setModalFeedback(text) {
    modalFeedbackElement().textContent = text;
}

function clearModalFeedback(text) {
    setModalFeedback("");
}


function showModalForm(html) {

    modalContent.innerHTML = html;
    modalContent.querySelector(".close").addEventListener("click", (e) => exitModal());

    var modalForm = document.getElementById("modal-form");
    modalForm.addEventListener("submit", loginSubmit);

    var image = document.querySelector(".modal img")
    if (image) {
        image.onload = showBaseModal;
        image.onerror = showBaseModal;
    } else {
        showBaseModal();
    }

}

function exitModal(timeout = 500) {
    hideBaseModal();

    var modalContent = document.getElementById("modal-content");
    setTimeout(() => {
        modalContent.innerHTML = "";
        userMessageField.focus();
        }, timeout);
}

function addNewMessage(message) {
    let newMessage = document.createElement("div");
    newMessage.innerHTML = message['content'];

    newMessage.classList.add("message")
    newMessage.classList.add(message['sender'])

    chatHistory.insertBefore(newMessage, messageEnd);

    messageEnd.scrollIntoView();
}

function addErrorMessage() {
    console.log("EEEERRRRORROROROORORORRRRR!!!!!!");
}

function hideMessageSpinner() {
    messageEnd.classList.add("hidden");
}

function showMessageSpinner() {
    messageEnd.classList.remove("hidden");
    messageEnd.scrollIntoView();
}

function clickListener(event) {
    target = event.target;
    if (target.classList.contains("message-link")) {
        userMessageField.value = target.text;
        messageSubmit();
    }
}

function post(url, body, action, errorAction) {
    fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: body
    })
    .then(response => response.json())
    .then(data => action(data))
    .catch((error) => errorAction(error));
}

function messageSubmit(event) {
    // prevent page reload
    if (event) {
        event.preventDefault();
    }

    const userMessage = {
        sender: "user",
        content: userMessageField.value
    }
    addNewMessage(userMessage);

    formData = new FormData(chatForm)

    userMessageField.value = "";
    userMessageField.focus();

    showMessageSpinner();
    post("process_message/", formData, processMessageResponse,
        (error) => {
            hideMessageSpinner();
            addErrorMessage();
        });
}

function loginSubmit(event) {
    // prevent page reload
    if (event) {
        event.preventDefault();
    }

    data = {};
    formData = new FormData(document.getElementById("modal-form"));

    post("provider_login/", formData, processMessageResponse,
        (error) => {
            hideMessageSpinner();
            addErrorMessage();
        });
}

function backgroundClick(event) {
    if(event.target.classList.contains("modal")) {
        exitModal();
    }
}

function modalFormElement() {
    return document.getElementById('modal-form');
}

function modalFeedbackElement() {
    return modalFormElement().querySelector('#feedback');
}


const csrftoken = getCookie('csrftoken');

const chatHistory = document.getElementById("chat-history");
const messageEnd = document.getElementById("end-marker");
const chatForm = document.getElementById("chat-form");
const userMessageField = document.getElementById("input-field");
const submitMessageBtn = document.getElementById("submit");

const baseModal = document.getElementById("modal");
const modalContent = document.getElementById("modal-content");


document.addEventListener('click', clickListener);

chatForm.addEventListener("submit", messageSubmit);


document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        exitModal();
    } else if (modalFormElement()) {
        clearModalFeedback();
    }
});

window.addEventListener("click", backgroundClick);


window.onload = function() {
    messageEnd.scrollIntoView();
    userMessageField.focus();
}
