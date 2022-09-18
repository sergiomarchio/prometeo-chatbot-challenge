
function addNewMessage(message) {
    let newMessage = document.createElement("div");
    newMessage.innerHTML = message['content'];

    newMessage.classList.add("message")
    newMessage.classList.add(message['sender'])

    chatHistory.insertBefore(newMessage, messageEnd);

    messageEnd.scrollIntoView();
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

function post(url, body, action) {
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
    .then(data => action(data));
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
    post("process_message/", userMessage, (data) => {
        hideMessageSpinner();
        addNewMessage(data);
    });
}


const csrftoken = getCookie('csrftoken');

const chatHistory = document.getElementById("chat-history");
const messageEnd = document.getElementById("end-marker");
const chatForm = document.getElementById("chat-form");
const userMessageField = document.getElementById("input-field");
const submitMessageBtn = document.getElementById("submit");


document.addEventListener('click', clickListener);

chatForm.addEventListener("submit", messageSubmit);


window.onload = function() {
    messageEnd.scrollIntoView();
    userMessageField.focus();
}
