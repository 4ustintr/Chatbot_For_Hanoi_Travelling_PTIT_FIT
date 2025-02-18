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

function formatMessage(text) {
    text = text.replace(/^- (.+)$/gm, '• $1');
    
    text = text.replace(/([🏷️📍💰⭐⏰🔍])/g, '<span class="emoji">$1</span>');
    
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    return text;
}

let currentLanguage = 'en';

function updateLanguage() {
    const select = document.getElementById('languageSelect');
    currentLanguage = select.value;
    
    const input = document.getElementById('user-input');
    switch(currentLanguage) {
        case 'vi':
            input.placeholder = 'Nhập tin nhắn...';
            break;
        case 'ja':
            input.placeholder = 'メッセージを入力...';
            break;
        default:
            input.placeholder = 'Type your message...';
    }
}

async function sendMessage(event) {
    if (event && event.key !== "Enter") return;

    var userInput = document.getElementById("user-input").value;
    if (!userInput.trim()) return;

    var chatBody = document.getElementById("chat-body");
    var userMessage = document.createElement("div");
    userMessage.className = "user-message message";
    userMessage.textContent = userInput;
    chatBody.appendChild(userMessage);

    document.getElementById("user-input").value = "";
    chatBody.scrollTop = chatBody.scrollHeight;

    var loadingMessage = document.createElement("div");
    loadingMessage.className = "bot-message message loading";
    loadingMessage.textContent = "...";
    chatBody.appendChild(loadingMessage);
    chatBody.scrollTop = chatBody.scrollHeight;

    try {
        const response = await fetch('http://localhost:8000/bot/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userInput,
                language: currentLanguage
            })
        });

        loadingMessage.remove();

        const data = await response.json();
        
        var botMessage = document.createElement("div");
        botMessage.className = "bot-message message";
        botMessage.innerHTML = formatMessage(data.response);
        chatBody.appendChild(botMessage);
        chatBody.scrollTop = chatBody.scrollHeight;

    } catch (error) {
        loadingMessage.remove();
        
        console.error('Error:', error);
        var botMessage = document.createElement("div");
        botMessage.className = "bot-message message error";
        botMessage.textContent = "Sorry, I encountered an error while processing your message.";
        chatBody.appendChild(botMessage);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
}

function initializeFileUpload() {
    const uploadForm = document.createElement('form');
    uploadForm.id = 'uploadForm';
    uploadForm.style.display = 'none';
    uploadForm.innerHTML = `
        <input type="file" id="fileInput" accept=".txt,.pdf,.doc,.docx" />
    `;
    document.body.appendChild(uploadForm);

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData();
        const fileInput = document.getElementById('fileInput');
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('http://localhost:8000/bot/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            console.log('File uploaded successfully:', result);
            loadFiles();
            fileInput.value = '';
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    });
}

async function loadFiles() {
    try {
        const response = await fetch('http://localhost:8000/bot/files');
        const files = await response.json();
        const history = document.querySelector('.history');
        history.innerHTML = files.length ? 
            files.map(file => `<div class="history-item">${file}</div>`).join('') :
            '<div class="history-item">No files uploaded</div>';
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("expanded");
}

function toggleSearch() {
    alert("Search functionality coming soon!");
}

document.addEventListener('DOMContentLoaded', () => {
    initializeFileUpload();
    loadFiles();
    updateLanguage(); 
});