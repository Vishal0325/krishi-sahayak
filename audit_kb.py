import os
import pandas as pd
import re
import csv
import json

DATA_DIR = "data/"
REPORT_FILE = "knowledge_quality_report.csv"

def is_hindi(text):
    return bool(re.search(r'[\u0900-\u097F]', str(text)))

def audit_kb():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and f != 'dataset_summary.csv']
    issues = []
    
    # Track statistics
    stats = {
        "total_rows": 0,
        "duplicates": 0,
        "wrong_crop_tags": 0,
        "suspicious_doses": 0,
        "encoding_issues": 0
    }
    
    all_questions = {}
    
    for file in files:
        path = os.path.join(DATA_DIR, file)
        try:
            df = pd.read_csv(path)
            stats["total_rows"] += len(df)
            
            # Check for missing columns
            required_cols = ['Question', 'Answer', 'Category', 'Crop']
            for col in required_cols:
                if col not in df.columns:
                    issues.append([file, "N/A", f"Missing column: {col}", "Critical"])
            
            for idx, row in df.iterrows():
                q = str(row.get('Question', ''))
                a = str(row.get('Answer', ''))
                crop = str(row.get('Crop', ''))
                cat = str(row.get('Category', ''))
                
                # 1. Duplicates
                if q in all_questions:
                    issues.append([file, idx, f"Duplicate Question: {q[:50]}...", "High"])
                    stats["duplicates"] += 1
                else:
                    all_questions[q] = file
                
                # 2. Wrong Crop Tag (heuristic)
                file_name_crop = file.replace('.csv', '').lower()
                if file_name_crop not in ['government', 'pests', 'disease', 'general', 'weather', 'machinery', 'fertilizer']:
                    if file_name_crop != crop.lower() and crop.lower() not in ['general', 'all']:
                        issues.append([file, idx, f"Mismatched Crop Tag: file suggests {file_name_crop}, row has {crop}", "Medium"])
                        stats["wrong_crop_tags"] += 1
                
                # 3. suspicious doses (Numbers + 'kg' or 'ml' without proper context)
                if any(x in a.lower() for x in ['kg', 'ml', 'gram', 'litre']):
                    # Check if doses are extremely high
                    nums = re.findall(r'\d+\.?\d*', a)
                    for n in nums:
                        if float(n) > 5000 and "ha" not in a.lower():
                            issues.append([file, idx, f"Suspiciously high value in answer: {n}", "Low"])
                            stats["suspicious_doses"] += 1
                
                # 4. Encoding/Spelling
                if "" in q or "" in a:
                    issues.append([file, idx, "Encoding issues (replacement character found)", "High"])
                    stats["encoding_issues"] += 1
                    
        except Exception as e:
            issues.append([file, "N/A", f"Error reading file: {str(e)}", "Critical"])

    # Write report
    report_df = pd.DataFrame(issues, columns=["File", "Row", "Issue", "Severity"])
    report_df.to_csv(REPORT_FILE, index=False)
    
    print(f"Audit completed. Total rows scanned: {stats['total_rows']}")
    print(f"Total issues found: {len(issues)}")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    audit_kb()
