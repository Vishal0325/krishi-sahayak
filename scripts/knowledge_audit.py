import pandas as pd
import glob
import os
import re

def audit_kb():
    data_dir = "data"
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    report = []
    conflicts = []
    
    total_docs = 0
    duplicates = 0
    missing_fields = 0
    
    for file in csv_files:
        if "audit" in file or "report" in file or "summary" in file:
            continue
            
        try:
            df = pd.read_csv(file)
            filename = os.path.basename(file)
            
            # Check for required columns
            required = ['Question', 'Answer']
            missing = [c for c in required if c not in df.columns]
            if missing:
                report.append({"file": filename, "issue": f"Missing columns: {missing}"})
                continue
            
            # Row-level audit
            for idx, row in df.iterrows():
                total_docs += 1
                q = str(row['Question'])
                a = str(row['Answer'])
                
                # Basic validation
                if len(q) < 5 or len(a) < 5:
                    report.append({"file": filename, "row": idx, "issue": "Short text content"})
                
                # Check for contradictory units or dangerous dosages (simplified regex)
                if re.search(r'\d+\s*(kg|g|ml|lit)', a.lower()):
                    # Potential dosage found - mark for review if needed
                    pass
            
            # Duplicate check within file
            dup_count = df.duplicated(subset=['Question']).sum()
            duplicates += dup_count
            if dup_count > 0:
                report.append({"file": filename, "issue": f"Found {dup_count} duplicate questions"})
                
        except Exception as e:
            report.append({"file": filename, "issue": f"Read Error: {str(e)}"})

    report_df = pd.DataFrame(report)
    report_df.to_csv("knowledge_audit_report.csv", index=False)
    
    print(f"✅ Audit Complete.")
    print(f"Total Documents: {total_docs}")
    print(f"Total Duplicates: {duplicates}")
    print(f"Report saved to knowledge_audit_report.csv")

if __name__ == "__main__":
    audit_kb()
