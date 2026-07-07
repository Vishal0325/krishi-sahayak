from knowledge_base import get_soil_health_recommendation, retrieve_knowledge, get_system_prompt

def test():
    print("Testing Soil Health Logic...")
    soil_res = get_soil_health_recommendation("clay", "yellow leaves")
    print(f"Soil Result: {soil_res['status']}, Score: {soil_res['health_score']}")

    print("\nTesting Knowledge Retrieval...")
    k_res = retrieve_knowledge("wheat disease")
    print(f"Knowledge found: {'Yes' if len(k_res) > 50 else 'No'}")

    print("\nTesting System Prompt...")
    prompt = get_system_prompt()
    print(f"Prompt length: {len(prompt)}")
    if "Krishi Sahayak Pro" in prompt:
        print("System Prompt Correct.")

if __name__ == "__main__":
    test()
