
function processMessageResponse(data) {
    hideMessageSpinner();

    console.log(data);

    if ('message' in data) {
        exitModal();
        addNewMessage(data['message']);
    } else if ('modal-form' in data) {
        showModalForm(data['modal-form']);
    } else {
        addErrorMessage();
    }

}

function showBaseModal() {
    baseModal.classList.add("modal-show");
}

function hideBaseModal() {
    baseModal.classList.remove("modal-show");
}

function showModalForm(html) {
    modalContent.innerHTML = html;
    modalContent.querySelector(".close").addEventListener("click", (e) => exitModal(e));

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

function exitModal(event) {
    hideBaseModal();

    var modalContent = document.getElementById("modal-content");
    setTimeout(() => {
        modalContent.innerHTML = "";
        }, 500);
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
    console.log(getCookie("csrftoken"));
    fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(body)
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

    userMessageField.value = "";
    userMessageField.focus();

    showMessageSpinner();
    post("process_message/", userMessage, processMessageResponse,
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
    fields = document.getElementById("modal-form").querySelectorAll(".input-field");
    for (let field of fields) {
        data[field.getAttribute('name')] = field.value;
    }

    post("provider_login/", data, processMessageResponse, (error) => {
            hideMessageSpinner();
            addErrorMessage();
        });
}

function backgroundClick(event) {
    if(event.target.classList.contains("modal")) {
        exitModal(event);
    }
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
    }
});

window.addEventListener("click", backgroundClick);


window.onload = function() {
    messageEnd.scrollIntoView();
    userMessageField.focus();
}
