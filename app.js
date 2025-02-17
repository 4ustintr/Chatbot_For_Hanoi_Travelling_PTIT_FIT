function animateButton() {
    var openButton = document.getElementById("open-chatbot");
    openButton.style.transform = "translate(-50%, -50%) scale(0.8)";
    openButton.style.opacity = "0";
    setTimeout(() => {
        openButton.style.visibility = "hidden";
        toggleChat(true);
    }, 300);
}

function toggleChat(open) {
    var chatbox = document.getElementById("chatbot");
    if (open) {
        chatbox.classList.add("show");
    } else {
        chatbox.classList.remove("show");
        setTimeout(() => {
            var openButton = document.getElementById("open-chatbot");
            openButton.style.visibility = "visible";
            openButton.style.opacity = "1";
            openButton.style.transform = "translate(-50%, -50%) scale(1)";
        }, 300);
    }
}

function sendMessage(event) {
    if (event && event.key !== "Enter") return;

    var userInput = document.getElementById("user-input").value;
    if (!userInput.trim()) return;

    var chatBody = document.getElementById("chat-body");
    var userMessage = document.createElement("div");
    userMessage.className = "user-message message";
    userMessage.textContent = userInput;
    chatBody.appendChild(userMessage);

    document.getElementById("user-input").value = "";

    setTimeout(() => {
        var botMessage = document.createElement("div");
        botMessage.className = "bot-message message";
        botMessage.textContent = "Here is my answer!";
        chatBody.appendChild(botMessage);
        chatBody.scrollTop = chatBody.scrollHeight;
    }, 1000);
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("expanded");
}

function toggleSearch() {
    alert("Tìm kiếm!");
}