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
import requests
from urllib.parse import quote
import re
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def extract_location_name(text):
    address_patterns = [
        r"Address:[\s\n]*([^,\n]+?)(?:,|\n|$)", 
        r"Địa chỉ:[\s\n]*([^,\n]+?)(?:,|\n|$)",  
        r"住所:[\s\n]*([^,\n]+?)(?:,|\n|$)"      
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            location = match.group(1).strip()
            if location.lower() in ["hanoi", "hanoi, vietnam", "hà nội", "hà nội, việt nam"]:
                gps_pattern = r"GPS Coordinates:.*\n.*?([^,\n]+?)(?:,|\n|$)"
                gps_match = re.search(gps_pattern, text, re.IGNORECASE | re.MULTILINE)
                if gps_match:
                    gps_location = gps_match.group(1).strip()
                    if gps_location and not gps_location.lower() in ["hanoi", "hà nội"]:
                        location = gps_location
            return location
            
    return None

def get_location_images(location_name, num_images=3):
    try:
        if not location_name:
            return []
        
        location = location_name.strip()
        
        generic_terms = ["hanoi", "vietnam", "hà nội", "việt nam", "hànội"]
        location_parts = location.lower().split(',')
        location = location_parts[0].strip()
        
        if location.lower() in generic_terms:
            return []
            
        search_query = f"{location}"
        if "hanoi" not in location.lower() and "hà nội" not in location.lower():
            search_query += " Hanoi"
            
        search_query += " landmark tourist attraction"
        
        print(f"Searching for images with query: {search_query}")  
        
        encoded_query = quote(search_query)
        url = f"https://www.googleapis.com/customsearch/v1?q={encoded_query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&searchType=image&num={num_images}"
        response = requests.get(url)
        data = response.json()
        
        if 'items' in data:
            return [item['link'] for item in data['items']]
        return []
    except Exception as e:
        print(f"Error fetching images: {e}")
        return []

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
- What to preparedsdd

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
            
            location_name = extract_location_name(collected_response)
            if location_name:
                print(f"Extracted location: {location_name}")  
                
                if ',' in location_name:
             
                    location_name = location_name.split(',')[0].strip()
                    print(f"Using first location: {location_name}")
                images = get_location_images(location_name)
                print(f"Found {len(images)} images for {location_name}")
            else:
                print("No location found in response")  
                images = []
            yield f"data: {json.dumps({'response': collected_response, 'complete': True, 'images': images})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
   
    uvicorn.run(app, host="0.0.0.0", port=8000 )
