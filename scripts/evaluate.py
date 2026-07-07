import os
import pickle
import random
import time
import pandas as pd
import numpy as np

# Adjust path to import rag_search correctly
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag_search import search as rag_search

def load_metadata():
    with open("vector_store/metadata.pkl", "rb") as f:
        return pickle.load(f)

def generate_test_cases(metadata, num_cases=1000):
    # Ensure diverse category coverage
    categories = {}
    for i, item in enumerate(metadata):
        cat = item.get('Category', 'General')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((i, item))
    
    test_cases = []
    # Sample uniformly across categories until we hit 1000
    while len(test_cases) < num_cases:
        for cat, items in categories.items():
            if len(test_cases) >= num_cases:
                break
            if items:
                idx = random.randint(0, len(items) - 1)
                test_cases.append(items.pop(idx))
    return test_cases

def evaluate():
    print("Loading metadata...")
    metadata = load_metadata()
    test_cases = generate_test_cases(metadata, 1000)
    
    print(f"Generated {len(test_cases)} test cases.")
    
    metrics = {
        "Top1": 0,
        "Top3": 0,
        "Recall5": 0, # Top 5 recall
        "MRR": 0,
        "Latencies": [],
        "Crop_Acc": {"correct": 0, "total": 0},
        "Govt_Acc": {"correct": 0, "total": 0},
        "Disease_Acc": {"correct": 0, "total": 0},
        "Pest_Acc": {"correct": 0, "total": 0},
        "Hallucination": 0
    }
    
    for i, (orig_idx, ground_truth) in enumerate(test_cases):
        if i % 100 == 0:
            print(f"Evaluating query {i}...")
            
        query = ground_truth["Question"]
        gt_answer = ground_truth["Answer"]
        gt_crop = ground_truth.get("Crop", "General")
        gt_cat = ground_truth.get("Category", "General")
        
        # In this benchmark, we'll ask for top_k = 5 to measure Recall@5
        results, latency = rag_search(query, top_k=5, session_id=f"eval_{i}")
        
        metrics["Latencies"].append(latency)
        
        # Find ranks
        rank = -1
        for r_idx, res in enumerate(results):
            if res["Answer"] == gt_answer:
                rank = r_idx + 1
                break
                
        if rank == 1:
            metrics["Top1"] += 1
            metrics["Top3"] += 1
            metrics["Recall5"] += 1
            metrics["MRR"] += 1.0
        elif rank > 1 and rank <= 3:
            metrics["Top3"] += 1
            metrics["Recall5"] += 1
            metrics["MRR"] += 1.0 / rank
        elif rank > 3 and rank <= 5:
            metrics["Recall5"] += 1
            metrics["MRR"] += 1.0 / rank
            
        # Hallucination check (if top 1 is completely wrong and score is high, it could hallucinate.
        # Since we enforce strict RAG, hallucination rate = rate of Top 1 being wrong, but confidence > 0.8
        if rank != 1 and len(results) > 0 and results[0].get("Score", 0) > 0.8:
            metrics["Hallucination"] += 1

        # Accuracy checks based on entities detected by RAG engine
        from rag_search import rag_engine
        detected = rag_engine.detect_entities(query)
        
        if gt_crop.lower() != "general":
            metrics["Crop_Acc"]["total"] += 1
            if any(c.lower() == gt_crop.lower() for c in detected["crops"]):
                metrics["Crop_Acc"]["correct"] += 1
                
        if "government" in gt_cat.lower():
            metrics["Govt_Acc"]["total"] += 1
            if any("government" in i.lower() for i in detected["intents"]):
                metrics["Govt_Acc"]["correct"] += 1
                
        if "disease" in gt_cat.lower():
            metrics["Disease_Acc"]["total"] += 1
            if any("disease" in i.lower() for i in detected["intents"]):
                metrics["Disease_Acc"]["correct"] += 1
                
        if "pest" in gt_cat.lower():
            metrics["Pest_Acc"]["total"] += 1
            if any("pest" in i.lower() for i in detected["intents"]):
                metrics["Pest_Acc"]["correct"] += 1
                
    total = len(test_cases)
    
    report = {
        "Metric": [
            "Top-1 Accuracy",
            "Top-3 Accuracy",
            "Recall@5",
            "Precision",
            "MRR",
            "Avg Latency (ms)",
            "Crop Detection Accuracy",
            "Government Query Accuracy",
            "Disease Accuracy",
            "Pest Accuracy",
            "Hallucination Rate"
        ],
        "Value": [
            f"{(metrics['Top1'] / total)*100:.2f}%",
            f"{(metrics['Top3'] / total)*100:.2f}%",
            f"{(metrics['Recall5'] / total)*100:.2f}%",
            f"{(metrics['Top1'] / total)*100:.2f}%", # Proxied by Top-1
            f"{metrics['MRR'] / total:.4f}",
            f"{np.mean(metrics['Latencies'])*1000:.2f}",
            f"{(metrics['Crop_Acc']['correct'] / max(1, metrics['Crop_Acc']['total']))*100:.2f}%",
            f"{(metrics['Govt_Acc']['correct'] / max(1, metrics['Govt_Acc']['total']))*100:.2f}%",
            f"{(metrics['Disease_Acc']['correct'] / max(1, metrics['Disease_Acc']['total']))*100:.2f}%",
            f"{(metrics['Pest_Acc']['correct'] / max(1, metrics['Pest_Acc']['total']))*100:.2f}%",
            f"{(metrics['Hallucination'] / total)*100:.2f}%"
        ]
    }
    
    df = pd.DataFrame(report)
    df.to_csv("evaluation_report.csv", index=False)
    print("\n--- Evaluation Report ---")
    print(df.to_string(index=False))
    print("-------------------------")
    print("Saved to evaluation_report.csv")

if __name__ == "__main__":
    evaluate()
