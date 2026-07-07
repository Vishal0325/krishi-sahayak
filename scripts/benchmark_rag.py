import os
import pandas as pd
import numpy as np
import time
from tqdm import tqdm
from rag_search import search

DATA_DIR = "data/"
EVAL_FILE = "evaluation_report.csv"

def run_evaluation():
    # 1. Sample questions from CSVs
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and f not in ['dataset_summary.csv', 'knowledge_quality_report.csv']]
    test_data = []
    
    for file in files:
        df = pd.read_csv(os.path.join(DATA_DIR, file))
        # Take up to 5 samples per file to cover diversity
        samples = df.sample(min(len(df), 5), random_state=42)
        for _, row in samples.iterrows():
            test_data.append({
                "Question": row['Question'],
                "Expected_Answer": row['Answer'],
                "Expected_Crop": row['Crop'],
                "Expected_Category": row['Category']
            })

    print(f"📊 Evaluating RAG on {len(test_data)} questions...")
    
    results = []
    top1_hits = 0
    top3_hits = 0
    mrr_sum = 0
    latencies = []
    crop_acc = 0
    
    for item in tqdm(test_data):
        q = item["Question"]
        start = time.time()
        retrieved, latency = search(q, top_k=5)
        latencies.append(latency * 1000)
        
        hit_rank = -1
        for rank, res in enumerate(retrieved):
            # Check if retrieved answer is same as expected (exact match on text)
            if res['Answer'] == item['Expected_Answer']:
                hit_rank = rank + 1
                break
        
        if hit_rank == 1: top1_hits += 1
        if hit_rank > 0 and hit_rank <= 3: top3_hits += 1
        if hit_rank > 0: mrr_sum += 1.0 / hit_rank
        
        # Crop detection accuracy
        if retrieved and retrieved[0]['Crop'] == item['Expected_Crop']:
            crop_acc += 1
            
        results.append({
            "Question": q,
            "Hit_Rank": hit_rank,
            "Latency_ms": latency * 1000
        })

    total = len(test_data)
    summary = {
        "Total_Questions": total,
        "Top1_Accuracy": f"{(top1_hits/total)*100:.2f}%",
        "Top3_Accuracy": f"{(top3_hits/total)*100:.2f}%",
        "MRR": f"{mrr_sum/total:.4f}",
        "Crop_Classification_Accuracy": f"{(crop_acc/total)*100:.2f}%",
        "Avg_Latency_ms": f"{np.mean(latencies):.2f}ms"
    }
    
    pd.DataFrame([summary]).to_csv(EVAL_FILE, index=False)
    print(f"✅ Evaluation complete. Summary: {summary}")

if __name__ == "__main__":
    run_evaluation()
