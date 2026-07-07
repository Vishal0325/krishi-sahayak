import os
import pandas as pd
import glob
import re

DATA_DIR = "data"
CLEANED_DIR = "cleaned_data"
REVIEW_FILE = "review_needed.csv"
REPORT_FILE = "knowledge_quality_report.csv"

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    # Fix whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def run_audit_and_clean():
    if not os.path.exists(CLEANED_DIR):
        os.makedirs(CLEANED_DIR)

    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    review_needed_rows = []
    report_stats = []

    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        try:
            # Using python engine and error_bad_lines=False to handle malformed rows if any
            df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
        except Exception as e:
            print(f"Error reading {file_name}: {e}")
            try:
                # Fallback to other encodings
                df = pd.read_csv(file_path, encoding='cp1252', on_bad_lines='skip')
            except Exception as e:
                print(f"Failed to read {file_name} completely: {e}")
                continue

        original_len = len(df)
        
        # Clean columns if they exist
        if 'Question' not in df.columns or 'Answer' not in df.columns:
            print(f"Skipping {file_name} - Missing Question or Answer column")
            continue
            
        df['Question'] = df['Question'].apply(clean_text)
        df['Answer'] = df['Answer'].apply(clean_text)
        
        # Drop fully empty rows
        df = df[df['Question'] != '']
        df = df[df['Answer'] != '']
        
        # Drop exact duplicates
        df_exact_dedup = df.drop_duplicates()
        exact_dupes_removed = original_len - len(df_exact_dedup)
        
        # Check for conflicting answers for the same question
        # Group by Question
        conflicts_in_file = 0
        df_cleaned = df_exact_dedup.copy()
        
        grouped = df_exact_dedup.groupby('Question')
        questions_to_remove = []
        for question, group in grouped:
            if len(group) > 1:
                # Multiple different answers for the same question
                conflicts_in_file += len(group)
                questions_to_remove.append(question)
                answers = group['Answer'].tolist()
                for i, row in group.iterrows():
                    review_needed_rows.append({
                        "filename": file_name,
                        "Question": question,
                        "Answer": row['Answer'],
                        "Reason": "Conflicting answers for the same question"
                    })
        
        # Remove the conflicting questions from the cleaned dataset (since they need review)
        if questions_to_remove:
            df_cleaned = df_cleaned[~df_cleaned['Question'].isin(questions_to_remove)]
            
        # Write to cleaned_data
        df_cleaned.to_csv(os.path.join(CLEANED_DIR, file_name), index=False, encoding='utf-8')
        
        report_stats.append({
            "File": file_name,
            "Original Rows": original_len,
            "Exact Duplicates Removed": exact_dupes_removed,
            "Conflicts Sent for Review": conflicts_in_file,
            "Cleaned Rows": len(df_cleaned)
        })
        print(f"Processed {file_name}: {len(df_cleaned)} rows saved.")

    # Write review_needed.csv
    if review_needed_rows:
        review_df = pd.DataFrame(review_needed_rows)
        review_df.to_csv(REVIEW_FILE, index=False, encoding='utf-8')
        print(f"Wrote {len(review_needed_rows)} rows to {REVIEW_FILE}")
    else:
        # Create empty file
        pd.DataFrame(columns=["filename", "Question", "Answer", "Reason"]).to_csv(REVIEW_FILE, index=False)
        print(f"No conflicts found. Created empty {REVIEW_FILE}")

    # Write report
    report_df = pd.DataFrame(report_stats)
    report_df.to_csv(REPORT_FILE, index=False, encoding='utf-8')
    print(f"Wrote audit report to {REPORT_FILE}")

if __name__ == "__main__":
    run_audit_and_clean()
