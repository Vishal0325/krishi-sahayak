import asyncio
import os
import sys

# Adjust path to import app correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import chat, ChatMessage, init_db

queries = [
    "धान में जिंक की कमी",
    "धान में नाइट्रोजन की कमी",
    "धान में पत्ती पीली",
    "तना छेदक",
    "झुलसा रोग",
    "ब्लास्ट रोग",
    "PM किसान",
    "KCC",
    "PMFBY",
    "मखाना",
    "लीची",
    "ड्रैगन फ्रूट",
    "थ्रिप्स",
    "यूरिया",
    "DAP",
    "Nano Urea",
    "अज्ञात जानकारी चाहिए", # Unknown query
    "अजगर उड़ रहा है" # Random nonsense
]

async def run_live_tests():
    print("Running Live Tests...")
    init_db() # ensure db exists
    
    for i, q in enumerate(queries):
        print(f"\n======================================")
        print(f"Test {i+1}: {q}")
        msg = ChatMessage(message=q, session_id=f"livetest_{i}")
        try:
            res = await chat(msg)
            print(f"Response (Model: {res.get('model_used')}):")
            print(res.get("response"))
            print(f"Citations: {res.get('citations')}")
        except Exception as e:
            print(f"Error testing '{q}': {e}")
            
    print("\n======================================")
    print("Live tests completed.")

if __name__ == "__main__":
    asyncio.run(run_live_tests())
