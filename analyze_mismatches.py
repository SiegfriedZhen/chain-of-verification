import pandas as pd
import re
import json

def extract_explanation(assessment_str):
    """提取 final_assessment 中的 explanation 字段"""
    if not isinstance(assessment_str, str):
        return ""
    
    # 嘗試提取 explanation
    explanation_match = re.search(r'"explanation":\s*"([^"]+)"', assessment_str)
    if explanation_match:
        return explanation_match.group(1)
    return ""

# 讀取比較結果
try:
    comparison_df = pd.read_excel("data/comparison_results.xlsx")
    print(f"Successfully loaded comparison file with {len(comparison_df)} rows")
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

# 過濾出不匹配的案例
mismatches = comparison_df[comparison_df['match'] == 'No'].copy()
print(f"\nFound {len(mismatches)} mismatched cases out of {len(comparison_df)} total cases")

# 為每個不匹配的案例提取解釋
mismatches['explanation'] = mismatches['final_assessment'].apply(extract_explanation)

# 顯示不匹配案例的詳細資訊
print("\n--- Detailed Mismatch Analysis ---")
for i, row in mismatches.iterrows():
    print(f"\nIteration {row['iteration']}:")
    print(f"CoVe Result: {row['parsed_assessment']}")
    print(f"Human Eval: {row['human_eval']}")
    print(f"Mismatch Type: {'False Positive' if row['parsed_assessment'] == 'VERIFIED' and row['human_eval'] == 'Fail' else 'False Negative' if row['parsed_assessment'] == 'UNVERIFIED' and row['human_eval'] == 'Success' else 'Other'}")
    print(f"Explanation: {row['explanation'][:200]}..." if len(row['explanation']) > 200 else f"Explanation: {row['explanation']}")

# 分析不匹配案例的模式
print("\n--- Mismatch Pattern Analysis ---")

# 1. False Positives (Verified but should be Fail)
fp = mismatches[(mismatches['parsed_assessment'] == 'VERIFIED') & (mismatches['human_eval'] == 'Fail')]
print(f"False Positives: {len(fp)} cases ({len(fp)/len(mismatches)*100:.1f}% of mismatches)")

# 2. False Negatives (Unverified but should be Success)
fn = mismatches[(mismatches['parsed_assessment'] == 'UNVERIFIED') & (mismatches['human_eval'] == 'Success')]
print(f"False Negatives: {len(fn)} cases ({len(fn)/len(mismatches)*100:.1f}% of mismatches)")

# 3. 其他類型的不匹配
other = mismatches[~(((mismatches['parsed_assessment'] == 'VERIFIED') & (mismatches['human_eval'] == 'Fail')) | 
                     ((mismatches['parsed_assessment'] == 'UNVERIFIED') & (mismatches['human_eval'] == 'Success')))]
print(f"Other Mismatches: {len(other)} cases ({len(other)/len(mismatches)*100:.1f}% of mismatches)")

# 保存分析結果
mismatches.to_excel("data/mismatch_analysis.xlsx", index=False)
print("\nMismatch analysis saved to data/mismatch_analysis.xlsx") 