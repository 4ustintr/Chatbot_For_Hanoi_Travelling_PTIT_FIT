from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
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
print(os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not found in environment variables")

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = STATIC_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


CONFIG_FILE = Path("bot_config.json")

DEFAULT_CONFIG = {
    "name": "Travel Assistant",
    "prompt": """You are a multilingual Hanoi travel assistant. You can respond in English, Vietnamese, and Japanese. When answering questions, respond in the user's selected language and structure your response in the following format:
Require response type markdown
🏷️ OVERVIEW/概要/TỔNG QUAN:
- Brief summary of the topic/place (2-3 sentences)

📍 LOCATION & ACCESS/場所とアクセス/ĐỊA ĐIỂM & CÁCH ĐI:
- GPS Coordinates: [latitude, longitude] format(This section does not change the language of GPS Coordinates)
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

Always provide accurate, up-to-date information about Hanoi. Keep responses concise but informative. If you're unsure about specific details, mention that information may need verification. Use a friendly, helpful tone. Respond entirely in the language specified by the user's selection (English, Vietnamese, or Japanese). """,
    "files": []
}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

BOT_CONFIG = load_config()
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    return FileResponse("admin.html")

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
        save_config(BOT_CONFIG)
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
    save_config(BOT_CONFIG)
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

from fastapi.responses import StreamingResponse
import asyncio
import json

@app.post("/bot/chat")
async def chat(message: dict):
    try:
        language = message.get("language", "en")
        lang_instruction = ""
        if language == "en":
            lang_instruction = "Respond in English language."
        elif language == "vi":
            lang_instruction = "Respond in Vietnamese language."
        else:
            lang_instruction = "Respond in Japanese language."

        messages = [
            {"role": "system", "content": BOT_CONFIG["prompt"]},
            {"role": "system", "content": lang_instruction},
            {"role": "user", "content": message["message"]}
        ]

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=800,
            stream=True
        )

        async def generate():
            collected_response = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    collected_response += content
                    yield f"data: {json.dumps({'response': content, 'complete': False})}\n\n"
                await asyncio.sleep(0.05)  
            yield f"data: {json.dumps({'response': collected_response, 'complete': True})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
   
    uvicorn.run(app, host="0.0.0.0", port=8000 )
