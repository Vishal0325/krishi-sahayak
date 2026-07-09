import faiss
import pickle
import numpy as np
import time
import os
import re
import json
import datetime
import hashlib
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple
from functools import lru_cache

class KrishiRAG:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        print("🚀 [AUDITOR] Initializing Production RAG Engine...")
        self.model = SentenceTransformer(model_name)
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.index = None
        self.metadata = None
        self.bm25 = None
        self.embedding_cache = {}
        self.load_db()
        
        # Phase 3: Synonym Expansion
        self.synonyms = {
            "यूरिया": ["urea", "nitrogen", "n", "नाइट्रोजन"],
            "डीएपी": ["dap", "phosphorus", "फॉस्फोरस", "p"],
            "पोटैश": ["potash", "potassium", "k", "पोटाश"],
            "धान": ["rice", "paddy", "chawal", "चावल"],
            "गेहूं": ["wheat", "gehu", "gehun"],
            "मक्का": ["maize", "corn", "makka"],
            "कीड़ा": ["pest", "insect", "kiit", "कीट", "bug"],
            "बीमारी": ["disease", "rog", "रोग", "fungus", "blight", "झुलसा"],
            "खाद": ["fertilizer", "fertiliser", "manure", "khad", "उर्वरक"],
            "सिंचाई": ["irrigation", "water", "sinchai", "पानी"],
            "भाव": ["price", "mandi", "rate", "daam", "दाम"],
            "योजना": ["scheme", "yojana", "gov", "sarkari"]
        }

    def load_db(self):
        index_path = "vector_store/index.faiss"
        meta_path = "vector_store/metadata.pkl"
        if not (os.path.exists(index_path) and os.path.exists(meta_path)):
            print("⚠️ Vector Database not found. Building it now...")
            try:
                from scripts.build_vector_store import build_index
                build_index()
            except ImportError:
                print("❌ Could not find build_vector_store script.")
                return

        if os.path.exists(index_path) and os.path.exists(meta_path):
            print("📂 Loading Persistent Index...")
            self.index = faiss.read_index(index_path)
            with open(meta_path, "rb") as f:
                self.metadata = pickle.load(f)
            
            # Prepare BM25
            print("📝 Building BM25 Index...")
            corpus = [self.normalize_text(f"{m.get('Question','')} {m.get('Crop','')} {m.get('Category','')}") for m in self.metadata]
            tokenized_corpus = [doc.split() for doc in corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)
            print(f"✅ RAG Engine Audited & Ready: {len(self.metadata)} docs.")

    def normalize_text(self, text: str) -> str:
        # Phase 3: Unicode & Hindi Normalization
        text = str(text).lower().strip()
        # Hindi char normalization (Nuqta removal for matching)
        text = text.replace("क़", "क").replace("ख़", "ख").replace("ग़", "ग").replace("ज़", "ज").replace("ड़", "ड").replace("ढ़", "ढ").replace("फ़", "फ")
        # Standardize units
        text = re.sub(r'(\d+)\s*(किलोग्राम|किग्रा|kg)', r'\1kg', text)
        text = re.sub(r'(\d+)\s*(ग्राम|g)', r'\1g', text)
        text = re.sub(r'(\d+)\s*(लीटर|lit|l)', r'\1L', text)
        # Remove special chars but keep space and alphanumeric
        text = re.sub(r'[^\w\s\u0900-\u097F]', ' ', text)
        return " ".join(text.split())

    def detect_entities(self, query: str) -> Dict[str, List[str]]:
        # Phase 4 & 5: Enhanced Entity Detection
        entities = {"crops": [], "intents": []}
        query_norm = self.normalize_text(query)
        
        crop_map = {
            "rice": "Rice", "paddy": "Rice", "धान": "Rice", "चावल": "Rice",
            "wheat": "Wheat", "गेहूं": "Wheat", "gehu": "Wheat",
            "maize": "Maize", "corn": "Maize", "मक्का": "Maize",
            "potato": "Potato", "आलू": "Potato",
            "tomato": "Tomato", "टमाटर": "Tomato",
            "makhana": "Makhana", "मखाना": "Makhana",
            "onion": "Onion", "प्याज": "Onion",
            "mustard": "Mustard", "सरसों": "Mustard",
            "sugarcane": "Sugarcane", "गन्ना": "Sugarcane",
            "litchi": "Litchi", "लीची": "Litchi",
            "mango": "Mango", "आम": "Mango",
            "chilli": "Chilli", "मिर्च": "Chilli",
            "banana": "Banana", "केला": "Banana"
        }
        for k, v in crop_map.items():
            if k in query_norm:
                if v not in entities["crops"]: entities["crops"].append(v)
        
        intent_map = {
            "yojana": "Government", "योजना": "Government", "paisa": "Government", "scheme": "Government",
            "disease": "Disease", "rog": "Disease", "रोग": "Disease", "बीमारी": "Disease", "झुलसा": "Disease",
            "pest": "Pest", "kiit": "Pest", "कीट": "Pest", "insect": "Pest", "कीड़ा": "Pest",
            "fertilizer": "Fertilizer", "khad": "Fertilizer", "खाद": "Fertilizer", "urea": "Fertilizer",
            "price": "Price", "bhav": "Price", "भाव": "Price", "mandi": "Price",
            "cultivation": "Cultivation", "kheti": "Cultivation", "खेती": "Cultivation",
            "soil": "Soil", "mitti": "Soil", "मिट्टी": "Soil"
        }
        for k, v in intent_map.items():
            if k in query_norm:
                if v not in entities["intents"]: entities["intents"].append(v)
            
        return entities

    def is_out_of_domain(self, query: str) -> bool:
        # Phase 13: OOD Rejection
        blocked_keywords = ["bitcoin", "crypto", "stock market", "politics", "movie", "film", "sports", "cricket", "modi", "rahul gandhi", "election"]
        q_lower = query.lower()
        if any(k in q_lower for k in blocked_keywords):
            return True
        # If no agricultural keywords at all in a long query
        agri_keywords = ["crop", "seed", "fertilizer", "soil", "water", "pest", "disease", "farm", "kheti", "kisan", "yield", "mandi", "price"]
        if len(q_lower.split()) > 4 and not any(k in q_lower for k in agri_keywords) and not any(ord(c) > 2300 for c in q_lower):
            # English query with no agri words
            return True
        return False

    def get_embedding(self, text: str):
        # Phase 12: Latency - Embedding Cache
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        emb = self.model.encode([text]).astype('float32')
        self.embedding_cache[text_hash] = emb
        return emb

    def search(self, query: str, top_k=3, session_id="default") -> Tuple[List[Dict], float]:
        if self.is_out_of_domain(query):
            print(f"🚫 [OOD] Query rejected: {query}")
            return [], 0.0

        if not self.index or not self.bm25: return [], 0.0
        
        start_time = time.time()
        clean_query = self.normalize_text(query)
        query_tokens = clean_query.split()
        
        entities = self.detect_entities(query)
        
        # 1. Hybrid Retrieval
        # FAISS
        query_vector = self.get_embedding(query)
        faiss_dists, faiss_indices = self.index.search(query_vector, 50)
        
        # BM25
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_indices = np.argsort(bm25_scores)[::-1][:50]
        
        candidate_indices = list(set(faiss_indices[0]) | set(bm25_indices))
        candidate_indices = [int(i) for i in candidate_indices if 0 <= i < len(self.metadata)]
        
        if not candidate_indices: return [], 0.0
        candidates = [self.metadata[i] for i in candidate_indices]
        
        # 2. Strict Metadata Filtering (Phase 5: Crop Lock)
        scored_candidates = []
        for res in candidates:
            boost = 1.0
            res_crop = str(res.get('Crop', 'General'))
            
            if entities["crops"]:
                # If specific crop in query, ONLY allow that crop or 'General'
                if any(c.lower() == res_crop.lower() for c in entities["crops"]):
                    boost *= 10.0
                elif res_crop.lower() != "general":
                    boost *= 0.0 # Phase 5: Hard Crop Lock
            
            if boost > 0:
                scored_candidates.append({"res": res, "boost": boost})

        if not scored_candidates: return [], time.time() - start_time
        
        # Pre-sort for Cross-Encoder
        top_candidates = [x["res"] for x in scored_candidates[:20]]
        
        # 3. Cross-Encoder Re-ranking (Phase 6)
        pairs = [[query, f"{c.get('Question','')} {c.get('Answer','')}".strip()] for c in top_candidates]
        cross_scores = self.cross_encoder.predict(pairs)
        
        final_list = []
        for i, res in enumerate(top_candidates):
            # Sigmoid for 0-1 score
            score = 1 / (1 + np.exp(-float(cross_scores[i])))
            final_list.append({**res, "Score": score})

        final_list.sort(key=lambda x: x["Score"], reverse=True)
        
        # Phase 7: Strict Confidence Threshold (Auditor Level: 0.85)
        THRESHOLD = 0.85
        if not final_list or final_list[0]['Score'] < THRESHOLD:
            print(f"🔍 [REJECTED] Top score {final_list[0]['Score']:.2f} < {THRESHOLD}")
            return [], time.time() - start_time

        print(f"✅ [RAG] Found {len(final_list[:top_k])} matches. Top Score: {final_list[0]['Score']:.2f}")
        return final_list[:top_k], time.time() - start_time

rag_engine = None

def search(query, top_k=3, session_id="default"):
    global rag_engine
    if rag_engine is None:
        rag_engine = KrishiRAG()
    return rag_engine.search(query, top_k=top_k, session_id=session_id)
