import time
import pandas as pd
import requests
import json

TEST_QUERIES = [
    {"q": "How to grow wheat?", "expected_crop": "Wheat"},
    {"q": "धान में पत्ती पीली होने का कारण?", "expected_crop": "Rice"},
    {"q": "PM Kisan eligibility?", "expected_intent": "Government"},
    {"q": "Bitcoin price today", "expected_fallback": True},
    {"q": "Makhana business plan cost", "expected_intent": "Business"},
    {"q": "Litchi fruit borer control", "expected_crop": "Litchi"},
    {"q": "Tomato wilt treatment", "expected_crop": "Tomato"},
    {"q": "How to survive on Mars?", "expected_fallback": True}
]

BASE_URL = "http://127.0.0.1:8012"

def run_benchmark():
    print("🚀 Starting Production Benchmark...")
    results = []
    
    for test in TEST_QUERIES:
        start = time.time()
        try:
            r = requests.post(f"{BASE_URL}/api/chat", json={"message": test["q"]}, timeout=30)
            latency = (time.time() - start) * 1000
            
            if r.status_code == 200:
                data = r.json()
                response_text = data.get("response", "")
                citations = data.get("citations", [])
                
                # Check for fallback
                is_fallback = "not available" in response_text.lower() or "मेरे पास इसकी जानकारी उपलब्ध नहीं है" in response_text
                
                # Validation logic
                passed = True
                if test.get("expected_fallback") and not is_fallback: passed = False
                if test.get("expected_crop"):
                    if not any(test["expected_crop"].lower() in str(c).lower() for c in citations):
                        if not is_fallback: passed = False # If it's not fallback, it MUST have the crop citation
                
                results.append({
                    "Query": test["q"],
                    "Latency_ms": round(latency, 2),
                    "Status": "PASS" if passed else "FAIL",
                    "Model": data.get("model_used"),
                    "Citations": len(citations),
                    "Is_Fallback": is_fallback
                })
                print(f"DONE: {test['q'][:30]}... | {latency:.0f}ms | {results[-1]['Status']}")
            else:
                print(f"FAILED: {test['q']} | HTTP {r.status_code}")
        except Exception as e:
            print(f"ERROR: {test['q']} | {str(e)}")

    df = pd.DataFrame(results)
    df.to_csv("evaluation_report.csv", index=False)
    
    print("\n--- FINAL METRICS ---")
    print(f"Average Latency: {df['Latency_ms'].mean():.2f} ms")
    print(f"Pass Rate: {(df['Status']=='PASS').mean()*100:.1f}%")
    print(f"Hallucination Block Rate: {df['Is_Fallback'].sum()} / {len(TEST_QUERIES)}")
    print("Report saved to evaluation_report.csv")

if __name__ == "__main__":
    # Note: Requires server to be running
    run_benchmark()
