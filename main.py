from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in environment variables")

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = STATIC_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

BOT_CONFIG = {
    "name": "Travel Assistant",
    "prompt": """You are a multilingual Hanoi travel assistant. You can respond in English, Vietnamese, and Japanese. When answering questions, respond in the user's selected language and structure your response in the following format:

🏷️ OVERVIEW/概要/TỔNG QUAN:
- Brief summary of the topic/place (2-3 sentences)

📍 LOCATION & ACCESS/場所とアクセス/ĐỊA ĐIỂM & CÁCH ĐI:
- Address (if applicable)
- How to get there
- Best time to visit

💰 COST & TIPS/費用とヒント/CHI PHÍ & LƯU Ý:
- Entrance fees or estimated costs
- Essential tips for visitors
- What to prepare

⭐ HIGHLIGHTS/ハイライト/ĐIỂM NỔI BẬT:
- Main attractions/features
- What makes it special
- Must-try experiences

⏰ SUGGESTED DURATION/推奨滞在時間/THỜI GIAN ĐỀ XUẤT:
- How long to spend here
- Best time allocation

🔍 ADDITIONAL INFORMATION/追加情報/THÔNG TIN THÊM:
- Historical/cultural context
- Local customs to note
- Nearby attractions

Always provide accurate, up-to-date information about Hanoi. Keep responses concise but informative. If you're unsure about specific details, mention that information may need verification. Use a friendly, helpful tone. Respond entirely in the language specified by the user's selection (English, Vietnamese, or Japanese).""",
    "files": []
}

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    return FileResponse("static/admin.html")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Travel Bot Manager</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
            }
            .section { 
                margin-bottom: 30px; 
                padding: 20px; 
                border: 1px solid #ddd; 
                border-radius: 5px;
            }
            .chat-box {
                height: 400px;
                border: 1px solid #ccc;
                padding: 10px;
                overflow-y: auto;
                margin-bottom: 10px;
                white-space: pre-line;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 5px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .user-message {
                background-color: #e3f2fd;
                margin-left: 20px;
            }
            .bot-message {
                background-color: #f5f5f5;
                margin-right: 20px;
                line-height: 1.5;
            }
            .bot-message ul {
                margin: 5px 0;
                padding-left: 20px;
            }
            .bot-message li {
                margin: 3px 0;
            }
            input[type="text"], textarea {
                width: 100%;
                padding: 8px;
                margin-bottom: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            #fileList {
                margin-top: 10px;
                padding: 10px;
                border: 1px solid #eee;
                border-radius: 4px;
            }
            .error {
                color: #ff0000;
                margin: 10px 0;
            }
            .emoji {
                font-size: 1.2em;
            }
        </style>
    </head>
    <body>
        <h1>Travel Bot Manager</h1>
        
        <div class="section">
            <h2>Bot Configuration</h2>
            <textarea id="botPrompt" rows="4" placeholder="Enter bot prompt">You are a knowledgeable Hanoi travel assistant...</textarea>
            <button onclick="updatePrompt()">Update Prompt</button>
        </div>

        <div class="section">
            <h2>File Upload</h2>
            <form id="uploadForm">
                <input type="file" id="fileInput" accept=".txt,.pdf,.doc,.docx" />
                <button type="submit">Upload</button>
            </form>
            <div id="fileList"></div>
        </div>

        <div class="section">
            <h2>Chat</h2>
            <div class="chat-box" id="chatBox"></div>
            <div style="margin-bottom: 10px;">
                <select id="languageSelect" style="padding: 8px; border-radius: 4px; border: 1px solid #ddd;">
                    <option value="en">English</option>
                    <option value="vi">Vietnamese</option>
                    <option value="ja">Japanese</option>
                </select>
            </div>
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="if(event.key === 'Enter') sendMessage()" />
            <button onclick="sendMessage()">Send</button>
        </div>

        <script>
            function formatMessage(text) {
                // Convert bullet points
                text = text.replace(/^- (.+)$/gm, '• $1');
                
                // Preserve emojis and formatting
                text = text.replace(/([🏷️📍💰⭐⏰🔍])/g, '<span class="emoji">$1</span>');
                
                // Convert markdown headers
                text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                
                return text;
            }

            async function updatePrompt() {
                const prompt = document.getElementById('botPrompt').value;
                try {
                    const response = await fetch('/bot/prompt', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({prompt})
                    });
                    const result = await response.json();
                    alert('Prompt updated successfully!');
                } catch (error) {
                    alert('Error updating prompt: ' + error);
                }
            }

            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData();
                const fileInput = document.getElementById('fileInput');
                formData.append('file', fileInput.files[0]);

                try {
                    const response = await fetch('/bot/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    alert('File uploaded successfully!');
                    loadFiles();
                    fileInput.value = '';
                } catch (error) {
                    alert('Error uploading file: ' + error);
                }
            };

            async function loadFiles() {
                try {
                    const response = await fetch('/bot/files');
                    const files = await response.json();
                    const fileList = document.getElementById('fileList');
                    fileList.innerHTML = '<h3>Uploaded Files:</h3>' + 
                        files.map(f => `<div>${f}</div>`).join('');
                } catch (error) {
                    console.error('Error loading files:', error);
                }
            }

            async function sendMessage() {
                const messageInput = document.getElementById('messageInput');
                const languageSelect = document.getElementById('languageSelect');
                const message = messageInput.value.trim();
                if (!message) return;

                addMessageToChat('user', message);
                messageInput.value = '';

                try {
                    const response = await fetch('/bot/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            message: message,
                            language: languageSelect.value
                        })
                    });
                    const result = await response.json();
                    addMessageToChat('bot', result.response);
                } catch (error) {
                    addMessageToChat('bot', 'Error: ' + error);
                }
            }

            function addMessageToChat(sender, message) {
                const chatBox = document.getElementById('chatBox');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                
                if (sender === 'bot') {
                    messageDiv.innerHTML = formatMessage(message);
                } else {
                    messageDiv.textContent = message;
                }
                
                chatBox.appendChild(messageDiv);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            loadFiles();
        </script>
    </body>
    </html>
    """

@app.post("/bot/upload")
async def upload_file(file: UploadFile):
    try:
        allowed_extensions = {'.txt', '.pdf', '.doc', '.docx'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )

        file_path = UPLOADS_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        BOT_CONFIG["files"].append(file.filename)
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bot/files")
async def list_files():
    return BOT_CONFIG["files"]

@app.get("/bot/prompt")
async def get_prompt():
    return {"prompt": BOT_CONFIG["prompt"]}

@app.post("/bot/prompt")
async def update_prompt(prompt: dict):
    BOT_CONFIG["prompt"] = prompt["prompt"]
    return {"status": "success"}

@app.post("/bot/api-key")
async def update_api_key(api_key: dict):
    try:
        os.environ["OPENAI_API_KEY"] = api_key["api_key"]
        global client
        client = OpenAI(api_key=api_key["api_key"])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bot/chat")
async def chat(message: dict):
    try:
        language = message.get("language", "en")
        lang_instruction = ""
        if language == "ja":
            lang_instruction = "Respond in Japanese language."
        elif language == "vi":
            lang_instruction = "Respond in Vietnamese language."
        else:
            lang_instruction = "Respond in English language."

        messages = [
            {"role": "system", "content": BOT_CONFIG["prompt"]},
            {"role": "system", "content": lang_instruction},
            {"role": "user", "content": message["message"]}
        ]

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.3,
            max_tokens=800
        )
        
        response = completion.choices[0].message.content
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
