import os
import glob
import pandas as pd
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def build_index():
    print("🚀 Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # Use 'data/' directory as it was cleaned by the optimizer
    data_dir = "data"
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    # Exclude non-data csv files
    csv_files = [f for f in csv_files if "summary" not in f and "report" not in f]
    
    metadata = []
    texts_to_embed = []
    
    print("📖 Reading and preparing data...")
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            if 'Question' not in df.columns or 'Answer' not in df.columns:
                continue
                
            for _, row in df.iterrows():
                q = str(row['Question'])
                a = str(row['Answer'])
                c = str(row.get('Category', 'General'))
                crop = str(row.get('Crop', 'General'))
                
                # FOCUS embedding on Query intent: Question + Crop context
                text = f"{q} [Crop: {crop}] [Category: {c}]"
                texts_to_embed.append(text)
                
                metadata.append({
                    "Question": q,
                    "Answer": a,
                    "Category": c,
                    "Crop": crop,
                    "Source": os.path.basename(file)
                })
        except Exception as e:
            print(f"Error reading {file}: {e}")
            
    print(f"Total documents to embed: {len(texts_to_embed)}")
    
    if not texts_to_embed:
        print("❌ No data found to embed!")
        return

    # Embed in batches
    batch_size = 128
    embeddings = []
    
    print("🧠 Generating embeddings...")
    for i in tqdm(range(0, len(texts_to_embed), batch_size)):
        batch = texts_to_embed[i:i+batch_size]
        emb = model.encode(batch, convert_to_numpy=True)
        embeddings.append(emb)
        
    embeddings = np.vstack(embeddings)
    
    print("🏗️ Building FAISS index...")
    dim = embeddings.shape[1]
    # L2 distance is fine for normalized embeddings, or use Inner Product for Cosine Similarity
    index = faiss.IndexFlatIP(dim) 
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    
    if not os.path.exists("vector_store"):
        os.makedirs("vector_store")
        
    print("💾 Saving FAISS index and metadata...")
    faiss.write_index(index, "vector_store/index.faiss")
    
    with open("vector_store/metadata.pkl", "wb") as f:
        pickle.dump(metadata, f)
        
    print("✨ Vector store built successfully!")

if __name__ == "__main__":
    build_index()
