import pandas as pd
import json

# 讀取結果檔案
try:
    results_df = pd.read_excel("data/evaluation_sheet2_results.xlsx")
    print(f"Successfully loaded file with {len(results_df)} rows")
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

# 顯示前 5 筆資料的 final_assessment 內容
print("\n--- First 5 final_assessment values ---")
for i, assessment in enumerate(results_df['final_assessment'].head(5), 1):
    print(f"\nIteration {i}:")
    print(f"Type: {type(assessment)}")
    print(f"Content: {assessment}")
    
    # 嘗試從字串中提取關鍵字
    if isinstance(assessment, str):
        keywords = ["verified", "unverified", "inconclusive", "disinformation"]
        found_keywords = []
        for keyword in keywords:
            if keyword.lower() in assessment.lower():
                found_keywords.append(keyword)
        print(f"Found keywords: {found_keywords}")

# 顯示所有結果的評估分佈
print("\n--- Assessment Distribution ---")
results = []
for assessment in results_df['final_assessment']:
    result = "Unknown"
    if isinstance(assessment, str):
        assessment_lower = assessment.lower()
        if "verified" in assessment_lower and "unverified" not in assessment_lower:
            result = "Verified"
        elif "unverified" in assessment_lower:
            result = "Unverified"
        elif "inconclusive" in assessment_lower:
            result = "Inconclusive"
        elif "evidence" in assessment_lower and "support" in assessment_lower:
            result = "Evidence supports"
        elif "evidence" in assessment_lower and "does not support" in assessment_lower:
            result = "Evidence does not support"
    results.append(result)

# 計算並顯示分佈
from collections import Counter
distribution = Counter(results)
for result, count in distribution.items():
    print(f"{result}: {count} ({count/len(results)*100:.1f}%)") 