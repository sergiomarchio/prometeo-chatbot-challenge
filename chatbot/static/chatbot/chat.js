
function addNewMessage(message) {
    let newMessage = document.createElement("div");
    let text = document.createTextNode(message['content']);

    newMessage.classList.add("message")
    newMessage.classList.add(message['sender'])
    newMessage.appendChild(text);

    chatHistory.insertBefore(newMessage, messageEnd);

    messageEnd.scrollIntoView();
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
    event.preventDefault();

    const userMessage = {
        content: userMessageField.value,
        sender: "user"
    }

    addNewMessage(userMessage);

    userMessageField.value = "";
    userMessageField.focus();

    post("process_message/", userMessage, addNewMessage);
}


const csrftoken = getCookie('csrftoken');

const chatHistory = document.getElementById("chat-history");
const messageEnd = document.getElementById("end-marker");
const chatForm = document.getElementById("chat-form");
const userMessageField = document.getElementById("input-field");
const submitMessageBtn = document.getElementById("submit");


chatForm.addEventListener("submit", messageSubmit);


window.onload = function() {
    messageEnd.scrollIntoView();
    userMessageField.focus();
}