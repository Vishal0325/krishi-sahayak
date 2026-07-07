import faiss
import pickle
import numpy as np
import time
import os
import re
import json
import httpx
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class KrishiRAG:
    def __init__(self):
        print("🚀 Initializing Ultra-Light KrishiRAG Engine via Gemini API...")
        self.index = None
        self.metadata = None
        self.bm25 = None
        self.load_db()
        
        self.synonyms = {
            "यूरिया": ["urea", "nitrogen", "नाइट्रोजन"],
            "dap": ["phosphorus", "फॉस्फोरस", "डीएपी"],
            "पत्ती पीली": ["yellow leaves", "nitrogen deficiency", "zinc deficiency", "पीलापन"],
            "कीड़ा": ["pest", "कीट", "insect", "बग"],
            "रोग": ["disease", "बीमारी", "झुलसा", "फंगस", "fungus"],
            "खाद": ["fertilizer", "उर्वरक", "poshak", "पोषण"]
        }

    def load_db(self):
        index_path = "vector_store/index.faiss"
        meta_path = "vector_store/metadata.pkl"
        
        if os.path.exists(index_path) and os.path.exists(meta_path):
            self.index = faiss.read_index(index_path)
            with open(meta_path, "rb") as f:
                self.metadata = pickle.load(f)
            print(f"✅ Loaded {len(self.metadata)} chunks into FAISS Vector Store.")
            
            # Initialize BM25 for Keyword Search
            corpus = [f"{c.get('Question','')} {c.get('Answer','')}" for c in self.metadata]
            tokenized_corpus = [doc.lower().split(" ") for doc in corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            print("❌ Vector store files not found! Creating an empty fallback.")
            self.metadata = []

    def get_gemini_embedding(self, text: str) -> List[float]:
        """Gemini API का उपयोग करके एम्बेडिंग प्राप्त करें (0MB RAM खर्च होगी)"""
        if not GEMINI_API_KEY:
            print("⚠️ GEMINI_API_KEY not found in environment!")
            return [0.0] * 768 # Fallback empty embedding
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
        
        # text-embedding-004 model 768 dimensions देता है, अगर आपका पुराना इंडेक्स 384 का है 
        # तो आप मॉडल को 'models/embedding-001' भी रख सकते हैं।
        try:
            response = httpx.post(url, json={
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text}]}
            }, timeout=10.0)
            if response.status_code == 200:
                return response.json()["embedding"]["values"]
        except Exception as e:
            print(f"Embedding API Error: {e}")
        return [0.0] * 768

    def search(self, query: str, top_k: int = 3, session_id: str = "default") -> Tuple[List[Dict], float]:
        start_time = time.time()
        if not self.metadata:
            return [], time.time() - start_time

        # 1. Keyword Search (BM25)
        tokenized_query = query.lower().split(" ")
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # 2. Semantic Search via Gemini API
        query_vector = self.get_gemini_embedding(query)
        
        # Ensure embedding size matches your FAISS index
        # अगर FAISS index का डायमेंशन और जेमिनी का डायमेंशन अलग है, तो आप केवल BM25 + Meta-data मैचिंग का उपयोग भी कर सकते हैं।
        try:
            query_np = np.array([query_vector], dtype=np.float32)
            # Normalize for cosine similarity if required
            faiss.normalize_L2(query_np)
            D, I = self.index.search(query_np, max(top_k * 3, 15))
            semantic_candidates = [self.metadata[idx] for idx in I[0] if idx != -1]
        except Exception as faiss_err:
            print(f"FAISS Match fallback: {faiss_err}")
            # Fallback to top BM25 if dimensions mismatch
            top_bm25_idx = np.argsort(bm25_scores)[::-1][:15]
            semantic_candidates = [self.metadata[idx] for idx in top_bm25_idx]

        # Combine and Scored Candidates
        scored_candidates = []
        for i, res in enumerate(semantic_candidates):
            # Simple boost calculation to replace heavy cross-encoder
            score = 1.0
            if query.lower() in res.get('Question', '').lower():
                score += 2.0
            scored_candidates.append({**res, "Score": score})

        scored_candidates.sort(key=lambda x: x["Score"], reverse=True)
        return scored_candidates[:top_k], time.time() - start_time

# Lazy loading to save memory
rag_engine = None

def search(query, top_k=3, session_id="default"):
    global rag_engine
    if rag_engine is None:
        rag_engine = KrishiRAG()
    return rag_engine.search(query, top_k=top_k, session_id=session_id)