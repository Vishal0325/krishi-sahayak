import os
import logging
import sqlite3
import aiosqlite
import base64
import random
import datetime
import hashlib
import csv
import io
import json
import traceback
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Response, Depends, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from asyncio import gather
from dotenv import load_dotenv

from rag_search import search as rag_hybrid_search
from knowledge_base import get_system_prompt

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Krishi Sahayak Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API KEYS from .env
KEYS = {
    "mesh": os.getenv("MESH_API_KEY", ""),
    "gemini": os.getenv("GEMINI_API_KEY", "")
}

# Cache for recurring queries
CACHE = {}

def init_db():
    conn = sqlite3.connect('krishi_pro.db')
    c = conn.cursor()
    # Profile with detailed farmer info
    c.execute('''CREATE TABLE IF NOT EXISTS profile
                 (id INTEGER PRIMARY KEY, name TEXT, mobile TEXT UNIQUE, state TEXT, district TEXT, village TEXT, crops TEXT, krishi_score INTEGER, pin TEXT)''')
    # History with metadata for citations
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT, metadata TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shared_knowledge
                 (id INTEGER PRIMARY KEY, question TEXT UNIQUE, answer TEXT, metadata TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS crop_scans
                 (id INTEGER PRIMARY KEY, filename TEXT, farmer_name TEXT, issue TEXT, confidence TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

async def call_ai_provider(prompt: str, system_content: str, history: List[Dict]):
    import asyncio
    print(f"--- AI Provider Call ---")
    
    # Try Mesh AI first with retries
    if KEYS["mesh"]:
        for attempt in range(3):
            try:
                url = "https://api.meshapi.ai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {KEYS['mesh']}", "Content-Type": "application/json"}
                messages = [{"role": "system", "content": system_content}]
                for h in history:
                    messages.append({"role": h["role"], "content": h["content"]})
                messages.append({"role": "user", "content": prompt})
                
                async with httpx.AsyncClient() as client:
                    r = await client.post(url, headers=headers, json={
                        "model": "openai/gpt-4o-mini",
                        "messages": messages,
                        "temperature": 0.1
                    }, timeout=20.0)
                    
                    if r.status_code == 200:
                        return r.json()["choices"][0]["message"]["content"], "Mesh AI"
                    elif r.status_code == 429 or r.status_code >= 500:
                        print(f"Mesh API Error {r.status_code}, retrying...")
                        await asyncio.sleep(1.5 ** attempt)
                    else:
                        print(f"Mesh API Error: {r.status_code} - {r.text}")
                        break # Unrecoverable error
            except Exception as e:
                print(f"!!! Mesh API Exception: {type(e).__name__}: {str(e)}")
                await asyncio.sleep(1.5 ** attempt)

    # Fallback to Gemini with retries
    if KEYS["gemini"]:
        print(f"Falling back to Gemini...")
        for attempt in range(2):
            try:
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={KEYS['gemini']}"
                contents = []
                for h in history:
                    contents.append({"role": "user" if h["role"]=="user" else "model", "parts": [{"text": h["content"]}]})
                contents.append({"role": "user", "parts": [{"text": f"SYSTEM: {system_content}\n\nUSER: {prompt}"}]})
                
                async with httpx.AsyncClient() as client:
                    r = await client.post(url, json={"contents": contents}, timeout=20.0)
                    if r.status_code == 200:
                        return r.json()["candidates"][0]["content"]["parts"][0]["text"], "Gemini"
                    elif r.status_code == 429 or r.status_code >= 500:
                        await asyncio.sleep(1.5 ** attempt)
                    else:
                        print(f"Gemini API Error: {r.status_code} - {r.text}")
                        break
            except Exception as e:
                print(f"!!! Gemini API Exception: {e}")
                await asyncio.sleep(1.5 ** attempt)
            
    return None, None

async def get_context_from_db(session_id: str):
    async with aiosqlite.connect('krishi_pro.db') as db:
        # Get Profile
        profile_str = "Farmer Profile: Not available."
        async with db.execute("SELECT name, state, district, village, crops FROM profile ORDER BY id DESC LIMIT 1") as cursor:
            row = await cursor.fetchone()
            if row:
                profile_str = f"Farmer Profile - Name: {row[0]}, Location: {row[3]}, {row[2]}, {row[1]}, Main Crops: {row[4]}."
        
        # Get Recent History (last 5 turns)
        async with db.execute("SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT 10", (session_id,)) as cursor:
            history = [{"role": r[0], "content": r[1]} for r in reversed(await cursor.fetchall())]
            
        return profile_str, history

@app.post("/api/chat")
async def chat(chat_msg: ChatMessage):
    msg = chat_msg.message.strip()
    session_id = chat_msg.session_id
    print(f"\n=== New Chat Request ===")
    print(f"User question received: {msg}")
    print(f"Session ID: {session_id}")

    if not msg: raise HTTPException(status_code=400, detail="Empty message")

    # 1. Hybrid Semantic Search
    print(f"FAISS search started...")
    cache_key = hashlib.md5(msg.lower().encode()).hexdigest()
    if cache_key in CACHE:
        print(f"Using cached search results.")
        kb_results, search_time = CACHE[cache_key]
    else:
        # Using updated rag search which logs to logs/retrieval_debug
        kb_results, search_time = rag_hybrid_search(msg, top_k=3, session_id=session_id)
        CACHE[cache_key] = (kb_results, search_time)

    print(f"Number of retrieved chunks: {len(kb_results)}")
    
    if not kb_results:
        print(f"No strong KB results found for: {msg}")
        return {"success": True, "response": "This specific information is not in my current knowledge base. Please ask something else.", "citations": []}

    # 2. Build AI Prompt
    profile_str, history = await get_context_from_db(session_id)
    
    context_text = "\n".join([f"Source {i+1} [{res['Crop']}]: {res['Answer']}" for i, res in enumerate(kb_results)])
    citations = [{"id": i+1, "crop": res['Crop'], "cat": res['Category']} for i, res in enumerate(kb_results)]
    
    full_system_prompt = f"""You are a specialized Agricultural Expert.

### STRICT RULES:
1. Answer the user's question ONLY using the provided KNOWLEDGE BASE DATA.
2. If the provided KNOWLEDGE BASE DATA does not contain the specific answer, say: "This specific information is not in my current knowledge base. Please ask something else."
3. NEVER use your general training knowledge or guess.
4. Do NOT combine unrelated chunks. If a chunk is not directly relevant to the specific question, ignore it.
5. Provide specific facts, doses, and methods exactly as found in the sources.

### RESPONSE FORMAT:
- **Problem**: (Brief description)
- **Solution**: (Detailed steps from the provided sources only)
- **Source References**: (List IDs)

### FARMER INFO:
{profile_str}

### KNOWLEDGE BASE DATA:
{context_text}
"""

    # 3. Call AI
    ai_response, model_used = await call_ai_provider(msg, full_system_prompt, history)
    
    if not ai_response:
        print(f"AI Provider failed. Falling back to Local RAG response.")
        ai_response = f"**Problem**: {msg}\n**Solution**: {kb_results[0]['Answer']}\n\n(This information is not available in the current knowledge base for AI processing, but here is a direct match from our handbook.)"
        model_used = "Local RAG"

    print(f"Final response length: {len(ai_response)} characters")
    print(f"Model used: {model_used}")
    print(f"=== Chat Request Completed ===\n")

    # 4. Persistence
    async with aiosqlite.connect('krishi_pro.db') as db:
        await db.execute("INSERT INTO chat_history (session_id, role, content, metadata, timestamp) VALUES (?,?,?,?,?)",
                        (session_id, "user", msg, "", datetime.datetime.now().isoformat()))
        await db.execute("INSERT INTO chat_history (session_id, role, content, metadata, timestamp) VALUES (?,?,?,?,?)",
                        (session_id, "assistant", ai_response, json.dumps(citations), datetime.datetime.now().isoformat()))
        await db.commit()

    return {
        "success": True,
        "response": ai_response,
        "citations": citations,
        "model_used": model_used,
        "search_time_ms": round(search_time * 1000, 2),
        "debug_context": kb_results # Added debug option showing retrieved chunks
    }



# --- OTHER ENDPOINTS ---

@app.get("/api/weather-advisory")
async def weather():
    return {"today": "बिहार में आज मौसम साफ रहेगा, आद्रता 65% है।", "alert": "कोई चेतावनी नहीं।"}

@app.get("/api/crop-calendar")
async def calendar():
    return {"crops": [
        {"crop": "धान (Rice)", "season": "Kharif", "sowing": "जून-जुलाई", "harvest": "अक्टूबर-नवंबर"},
        {"crop": "गेहूं (Wheat)", "season": "Rabi", "sowing": "नवंबर", "harvest": "मार्च-अप्रैल"}
    ]}

@app.get("/api/profile")
async def get_profile():
    async with aiosqlite.connect('krishi_pro.db') as db:
        async with db.execute("SELECT name, mobile, state, district, village, crops FROM profile ORDER BY id DESC LIMIT 1") as cursor:
            row = await cursor.fetchone()
            if row: return {"name": row[0], "mobile": row[1], "state": row[2], "district": row[3], "village": row[4], "crops": row[5].split(",")}
    return {}

@app.post("/api/profile")
async def save_profile(p: dict):
    async with aiosqlite.connect('krishi_pro.db') as db:
        await db.execute("INSERT OR REPLACE INTO profile (name, mobile, state, district, village, crops) VALUES (?,?,?,?,?,?)",
                        (p['name'], p['mobile'], p['state'], p.get('district'), p.get('village'), ",".join(p.get('crops',[]))))
        await db.commit()
    return {"success": True}

@app.get("/api/admin/farmers")
async def get_all_farmers():
    async with aiosqlite.connect('krishi_pro.db') as db:
        async with db.execute("SELECT name, mobile, state, district, village, crops FROM profile") as cursor:
            rows = await cursor.fetchall()
            return [{"name": r[0], "mobile": r[1], "state": r[2], "district": r[3], "village": r[4], "crops": r[5]} for r in rows]

@app.post("/api/upload-scan")
async def upload_scan(file: UploadFile = File(...), farmer_name: str = "Unknown", issue: str = "N/A", confidence: str = "0%"):
    os.makedirs("static/uploads", exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100,999)}{file_extension}"
    file_path = os.path.join("static/uploads", unique_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    async with aiosqlite.connect('krishi_pro.db') as db:
        await db.execute("INSERT INTO crop_scans (filename, farmer_name, issue, confidence, timestamp) VALUES (?,?,?,?,?)",
                        (unique_filename, farmer_name, issue, confidence, datetime.datetime.now().isoformat()))
        await db.commit()
    
    return {"success": True, "filename": unique_filename}

@app.get("/api/admin/scans")
async def get_all_scans():
    async with aiosqlite.connect('krishi_pro.db') as db:
        async with db.execute("SELECT id, filename, farmer_name, issue, confidence, timestamp FROM crop_scans ORDER BY id DESC") as cursor:
            rows = await cursor.fetchall()
            return [{"id": r[0], "url": f"/uploads/{r[1]}", "farmer": r[2], "issue": r[3], "conf": r[4], "date": r[5]} for r in rows]

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
