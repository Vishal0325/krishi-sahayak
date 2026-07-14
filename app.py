import re  # Is line ko file ke sabse upar likhein
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
import time
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Response, Depends, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from asyncio import gather
from dotenv import load_dotenv

from rag_search import search as rag_hybrid_search

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Krishi Sahayak Pro - PRODUCTION")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API KEYS
KEYS = {
    "mesh": os.getenv("MESH_API_KEY", ""),
    "gemini": os.getenv("GEMINI_API_KEY", "")
}

# Phase 12: Latency - Response Cache
RESPONSE_CACHE = {}

def init_db():
    conn = sqlite3.connect('krishi_pro.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS profile
                 (id INTEGER PRIMARY KEY, name TEXT, mobile TEXT UNIQUE, state TEXT, district TEXT, village TEXT, crops TEXT, krishi_score INTEGER, pin TEXT)''')
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
    session_id: Optional[str] = "default"

async def call_ai_provider(prompt: str, system_content: str, history: List[Dict]):
    import asyncio
    
    # Try Mesh AI (Primary for Hackathon)
    if KEYS["mesh"]:
        for attempt in range(2):
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
                        "temperature": 0.0 # Phase 8: Near-zero hallucination
                    }, timeout=15.0)
                    
                    if r.status_code == 200:
                        return r.json()["choices"][0]["message"]["content"], "Mesh AI (GPT-4o-Mini)"
                    elif r.status_code == 429:
                        await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Mesh API Exception: {str(e)}")
                await asyncio.sleep(1.0)

    # Fallback to Gemini
    if KEYS["gemini"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={KEYS['gemini']}"
            contents = []
            for h in history:
                contents.append({"role": "user" if h["role"]=="user" else "model", "parts": [{"text": h["content"]}]})
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM: {system_content}\n\nUSER: {prompt}"}]})
            
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json={"contents": contents}, timeout=15.0)
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"], "Gemini 1.5 Flash"
        except Exception as e:
            logger.error(f"Gemini API Exception: {e}")
            
    return None, None

async def get_context_from_db(session_id: str):
    async with aiosqlite.connect('krishi_pro.db') as db:
        profile_str = "Farmer Profile: Location Bihar."
        async with db.execute("SELECT name, state, district, village, crops FROM profile ORDER BY id DESC LIMIT 1") as cursor:
            row = await cursor.fetchone()
            if row:
                profile_str = f"Farmer: {row[0]}, Location: {row[3]}, {row[2]}, {row[1]}, Crops: {row[4]}."
        
        async with db.execute("SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT 6", (session_id,)) as cursor:
            history = [{"role": r[0], "content": r[1]} for r in reversed(await cursor.fetchall())]
            
        return profile_str, history

@app.post("/api/chat")
async def chat(chat_msg: ChatMessage):
    try:
        msg = chat_msg.message.strip()
        session_id = chat_msg.session_id or "default"
        
        # --- PHASE 17+: PRE-PROCESSING GUARD (Kisan Galt Question Rokna) ---
        
        # 1. Length Check
        if not msg or len(msg) < 3:
            return {"success": True, "response": "कृपया अपना सवाल थोड़ा विस्तार से लिखें ताकि मैं आपकी बेहतर मदद कर सकूँ।", "citations": [], "model_used": "Guardrail"}
        
        if len(msg) > 1000:
            return {"success": True, "response": "आपका सवाल बहुत बड़ा है, कृपया इसे छोटा करके पूछें।", "citations": [], "model_used": "Guardrail"}

        # 2. Gibberish/Pattern Check (e.g., "aaaaaaaaa")
        if re.search(r'(.)\1{5,}', msg):
            return {"success": True, "response": "क्षमा करें, ऐसा लग रहा है कि आपने कुछ गलत टाइप किया है। कृपया सही शब्दों का प्रयोग करें।", "citations": [], "model_used": "Guardrail"}

        # 3. Off-Topic Keywords
        blocked = ["bitcoin", "crypto", "stock market", "politics", "movie", "film", "sports", "cricket", "game", "bollywood", "song"]
        if any(k in msg.lower() for k in blocked):
            return {"success": True, "response": "क्षमा करें, मैं केवल खेती-किसानी, फसल और सरकारी योजनाओं से जुड़े सवालों के जवाब दे सकता हूँ।", "citations": [], "model_used": "Guardrail"}

        # 4. Non-Agricultural English Check
        agri_words = ["crop", "seed", "fertilizer", "soil", "water", "pest", "disease", "farm", "kheti", "kisan", "yield", "mandi", "price", "subsidy", "yojana", "plant"]
        has_agri = any(k in msg.lower() for k in agri_words)
        has_hindi = any(ord(c) > 2300 for c in msg)
        if not has_agri and not has_hindi and len(msg.split()) > 3:
            return {"success": True, "response": "मैं आपकी बात पूरी तरह समझ नहीं पाया। कृपया खेती या फसलों से संबंधित सवाल पूछें।", "citations": [], "model_used": "Guardrail"}

        # --- END GUARD ---

        # Phase 12: Response Cache Lookup
        cache_key = hashlib.md5(f"{msg}_{session_id}".lower().encode()).hexdigest()
        if cache_key in RESPONSE_CACHE:
            return RESPONSE_CACHE[cache_key]

        # 1. Audited Hybrid Search
        kb_results, search_time = rag_hybrid_search(msg, top_k=3, session_id=session_id)

        if not kb_results:
            return {
                "success": True, 
                "response": "This information is not available in the current knowledge base. Please ask something else.", 
                "citations": [],
                "model_used": "RAG Filter (OOD/Low Confidence)",
                "search_time_ms": round(search_time * 1000, 2)
            }

        # 2. Build Strict AI Prompt (Phase 9)
        profile_str, history = await get_context_from_db(session_id)
        
        # Phase 11: Professional Citations
        context_blocks = []
        citations = []
        for i, res in enumerate(kb_results):
            cid = i + 1
            context_blocks.append(f"SOURCE {cid} (File: {res['Source']}, Crop: {res['Crop']}, Category: {res['Category']}):\n{res['Answer']}")
            citations.append({
                "id": cid,
                "file": res['Source'],
                "crop": res['Crop'],
                "category": res['Category'],
                "confidence": f"{int(res['Score']*100)}%",
                "snippet": res['Answer'][:150] + "..."
            })
        
        context_text = "\n\n".join(context_blocks)
        
        full_system_prompt = f"""You are the Krishi Sahayak Production AI.
### PRODUCTION AUDIT PROTOCOLS:
1. **SOURCE ONLY**: Use ONLY the provided context. If the answer isn't there, say: "This information is not available in the current knowledge base. Please ask something else."
2. **NO ESTIMATES**: Never guess costs, profits, yields, or doses. If numbers are missing, say: "मेरे पास इसकी विस्तृत जानकारी उपलब्ध नहीं है। कृपया स्थानीय कृषि विभाग से संपर्क करें।"
3. **STRUCTURED RESPONSE**: 
   - **Problem**: Brief summary.
   - **Cause**: Based on source.
   - **Solution**: Step-by-step from source.
   - **Prevention**: From source.
   - **Important Notes**: Safety/Dosage warning.
4. **CITATION**: Mark every fact with [Source X].

### FARMER PROFILE:
{profile_str}

### RETRIEVED CONTEXT:
{context_text}
"""

        # 3. Call AI
        ai_response, model_used = await call_ai_provider(msg, full_system_prompt, history)
        
        if not ai_response:
            ai_response = f"**Solution**: {kb_results[0]['Answer']}\n\n(Note: Direct handbook match used as AI providers are busy.)"
            model_used = "Local Context Fallback"

        # 4. Result
        result = {
            "success": True,
            "response": ai_response,
            "citations": citations,
            "model_used": model_used,
            "search_time_ms": round(search_time * 1000, 2)
        }
        
        # Update cache
        RESPONSE_CACHE[cache_key] = result

        # Persistence
        async with aiosqlite.connect('krishi_pro.db') as db:
            await db.execute("INSERT INTO chat_history (session_id, role, content, metadata, timestamp) VALUES (?,?,?,?,?)",
                            (session_id, "user", msg, "", datetime.datetime.now().isoformat()))
            await db.execute("INSERT INTO chat_history (session_id, role, content, metadata, timestamp) VALUES (?,?,?,?,?)",
                            (session_id, "assistant", ai_response, json.dumps(citations), datetime.datetime.now().isoformat()))
            await db.commit()

        return result
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "response": f"सर्वर में एक त्रुटि हुई: {str(e)}",
            "citations": [],
            "model_used": "Error"
        }

@app.get("/api/weather-advisory")
async def weather():
    return {"today": "Bihar weather is clear. 65% humidity.", "alert": "No alerts."}

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

@app.post("/api/upload-scan")
async def upload_scan(file: UploadFile = File(...), farmer_name: str = "Unknown", issue: str = "N/A", confidence: str = "0%"):
    os.makedirs("static/uploads", exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
    file_path = os.path.join("static/uploads", unique_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    async with aiosqlite.connect('krishi_pro.db') as db:
        await db.execute("INSERT INTO crop_scans (filename, farmer_name, issue, confidence, timestamp) VALUES (?,?,?,?,?)",
                        (unique_filename, farmer_name, issue, confidence, datetime.datetime.now().isoformat()))
        await db.commit()
    return {"success": True, "filename": unique_filename}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
