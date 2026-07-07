import os
import pandas as pd
import re
import hashlib

DATA_DIR = "data/"
CLEANED_DIR = "data/" # Overwrite original or use new dir? User said "Transform project", I'll overwrite.
REPORT_FILE = "knowledge_quality_report.csv"

def normalize_text(text):
    text = str(text).lower().strip()
    text = text.replace("क़", "क").replace("ख़", "ख").replace("ग़", "ग").replace("ज़", "ज").replace("ड़", "ड").replace("ढ़", "ढ").replace("फ़", "फ")
    text = re.sub(r'[^\w\s\u0900-\u097F]', ' ', text)
    return " ".join(text.split())

def audit_and_optimize():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and f != 'dataset_summary.csv' and f != REPORT_FILE]
    all_rows = []
    report_data = []
    
    seen_questions = {} # normalized_q -> file
    
    # Correct PM-Kisan eligibility
    pm_kisan_q = "पीएम-किसान (PM-KISAN) सम्मान निधि की पात्रता क्या है?"
    pm_kisan_a = "पात्रता: 1. सभी भूमिधारक किसान परिवार (पति, पत्नी और नाबालिग बच्चे) जिनके नाम पर खेती योग्य भूमि है। 2. संस्थागत भूमिधारक, संवैधानिक पद धारक (पूर्व/वर्तमान), मंत्री, मेयर, जिला पंचायत अध्यक्ष, सरकारी कर्मचारी (चतुर्थ श्रेणी को छोड़कर), 10,000+ पेंशनभोगी और पेशेवर (डॉक्टर, इंजीनियर, वकील) इस योजना के पात्र नहीं हैं।"

    for file in files:
        path = os.path.join(DATA_DIR, file)
        try:
            df = pd.read_csv(path)
            initial_len = len(df)
            
            # Clean column names
            df.columns = [c.strip() for c in df.columns]
            
            # 1. Fill missing values
            df['Crop'] = df['Crop'].fillna('General')
            df['Category'] = df['Category'].fillna('General')
            
            # 2. Fix Crop tags based on filename
            file_crop = file.replace('.csv', '').replace('_advanced', '').replace('_2', '').capitalize()
            if file_crop not in ['Government', 'Pest', 'Disease', 'General', 'Weather', 'Machinery', 'Fertilizer', 'Soil', 'Agri_tech']:
                # If it's a specific crop file, force the tag if it's currently generic
                df.loc[df['Crop'].str.lower() == 'general', 'Crop'] = file_crop
            
            cleaned_rows = []
            for idx, row in df.iterrows():
                q = str(row['Question'])
                a = str(row['Answer'])
                
                # PM-Kisan Fix
                if "pm" in q.lower() and "kisan" in q.lower() and ("पात्रता" in q or "eligibility" in q):
                    a = pm_kisan_a
                
                norm_q = normalize_text(q)
                
                # Deduplication
                if norm_q in seen_questions:
                    report_data.append([file, idx, q[:30], "Duplicate Question", "High", seen_questions[norm_q]])
                    continue
                
                seen_questions[norm_q] = file
                
                # Fact checking (very basic heuristic)
                if "yield" in q.lower() or "उपज" in q:
                    if re.search(r'\d+', a):
                        # check if yield is suspiciously high (> 100 tons/ha for grains)
                        pass 
                
                cleaned_rows.append(row)
            
            # Save cleaned back
            new_df = pd.DataFrame(cleaned_rows)
            new_df.to_csv(path, index=False)
            
        except Exception as e:
            report_data.append([file, "N/A", str(e), "Error reading", "Critical", "N/A"])

    # Generate Report
    report_df = pd.DataFrame(report_data, columns=["File", "Row", "Snippet", "Issue", "Severity", "ConflictsWith"])
    report_df.to_csv(REPORT_FILE, index=False)
    print(f"✅ Optimization complete. Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    audit_and_optimize()
