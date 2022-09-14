
// https://docs.djangoproject.com/en/4.1/howto/csrf/
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function addNewMessage(message) {
    let newMessage = document.createElement("div");
    let text = document.createTextNode(message['content']);

    newMessage.classList.add("message")
    newMessage.classList.add(message['sender'])
    newMessage.appendChild(text);

    chatHistory.insertBefore(newMessage, messageEnd);
}

function messageSubmit(e) {
    // prevent page reload
    e.preventDefault();

    const userMessage = {
        content: userMessageField.value,
        sender: "user"
    }

    addNewMessage(userMessage);
    messageEnd.scrollIntoView();

    userMessageField.value = "";
    userMessageField.focus();
}

const csrftoken = getCookie('csrftoken');

window.onload = function() {
    messageEnd.scrollIntoView();
    userMessageField.focus();
}

const chatHistory = document.getElementById("chat-history");
const messageEnd = document.getElementById("end-marker");
const chatForm = document.getElementById("chat-form");
const userMessageField = document.getElementById("input-field");
const submitMessageBtn = document.getElementById("submit");

chatForm.addEventListener("submit", messageSubmit);

