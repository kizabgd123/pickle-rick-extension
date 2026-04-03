import pandas as pd
import sys
import json
from pathlib import Path

def analyze_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        stats = {
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "nulls": df.isnull().sum().to_dict(),
            "target_dist": None
        }
        # Try to guess target (usually the last column or named 'target/label')
        target_candidates = ['target', 'label', 'churn', df.columns[-1]]
        for tc in target_candidates:
            if tc in df.columns:
                stats["target_dist"] = df[tc].value_counts(normalize=True).to_dict()
                break
        
        return stats
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check-data.py [path_to_csv]")
        sys.exit(1)
    
    result = analyze_csv(sys.argv[1])
    print(json.dumps(result, indent=2))
