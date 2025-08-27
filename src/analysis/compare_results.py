import pandas as pd
import ast
import numpy as np
import re
import json

def parse_final_assessment(assessment_str):
    """Parses the final_assessment string to extract the core evaluation."""
    if not isinstance(assessment_str, str):
        return str(assessment_str) # Return as is if not a string
    
    # 嘗試用正則表達式提取 final_result
    final_result_match = re.search(r'"final_result":\s*"([^"]+)"', assessment_str)
    if final_result_match:
        return final_result_match.group(1)
    
    # 備用方法: 嘗試提取 JSON 對象並讀取 final_result
    json_match = re.search(r'{\s*"final_result"[^}]+}', assessment_str)
    if json_match:
        try:
            json_str = json_match.group(0)
            json_obj = json.loads(json_str)
            if "final_result" in json_obj:
                return json_obj["final_result"]
        except:
            pass

    # 最後的備用方法: 關鍵字搜索
    assessment_lower = assessment_str.lower()
    if "unverified" in assessment_lower:
        return "UNVERIFIED"
    elif "verified" in assessment_lower and "unverified" not in assessment_lower:
        return "VERIFIED"
    elif "inconclusive" in assessment_lower:
        return "INCONCLUSIVE"
    elif "debunked" in assessment_lower:
        return "DEBUNKED"
    
    # 如果都找不到, 返回預設值
    return "UNKNOWN"

def map_cove_to_human_eval(cove_result):
    """將 CoVe 結果映射到 human_eval 格式 (Success/Fail)"""
    cove_result = cove_result.upper()
    if cove_result == "VERIFIED":
        return "Success"  # 假設 Verified 對應 Success
    else:
        return "Fail"  # 其他狀態都對應 Fail

# Load the generated results
try:
    results_df = pd.read_excel("data/evaluation_sheet2_results.xlsx")
except FileNotFoundError:
    print("Error: 'data/evaluation_sheet2_results.xlsx' not found. Please run evaluate_sheet2.py first.")
    exit()

# Load the original evaluation sheet
original_df = pd.read_excel("data/LLM evaluation.xlsx", sheet_name="工作表2")

# Select relevant columns from original sheet
original_subset = original_df[['Iterations', 'human_eval']].copy()

# Merge the dataframes
comparison_df = pd.merge(results_df, original_subset, left_on='iteration', right_on='Iterations', how='left')

# Parse the 'final_assessment' column
comparison_df['parsed_assessment'] = comparison_df['final_assessment'].apply(parse_final_assessment)

# Map CoVe results to human_eval format
comparison_df['cove_mapped_to_human'] = comparison_df['parsed_assessment'].apply(map_cove_to_human_eval)

# --- Comparison --- 
# Calculate agreement (using mapped values)
comparison_df['match'] = np.where(comparison_df['cove_mapped_to_human'] == comparison_df['human_eval'], 'Yes', 'No')
agreement_count = (comparison_df['match'] == 'Yes').sum()
total_count = len(comparison_df)
agreement_percentage = (agreement_count / total_count) * 100 if total_count > 0 else 0

# Display comparison
print("--- Comparison of CoVe Assessment vs Human Evaluation ---")
print(comparison_df[['iteration', 'parsed_assessment', 'cove_mapped_to_human', 'human_eval', 'match']].to_string(index=False))

print("\n--- Summary ---")
print(f"Total Iterations: {total_count}")
print(f"Agreements: {agreement_count}")
print(f"Agreement Percentage: {agreement_percentage:.2f}%")

# Count distribution of CoVe results
cove_counts = comparison_df['parsed_assessment'].value_counts()
print("\n--- CoVe Result Distribution ---")
for result, count in cove_counts.items():
    print(f"{result}: {count} ({count/total_count*100:.1f}%)")

# Count distribution of human eval results
human_counts = comparison_df['human_eval'].value_counts()
print("\n--- Human Eval Distribution ---")
for result, count in human_counts.items():
    print(f"{result}: {count} ({count/total_count*100:.1f}%)")

# Save the comparison results
comparison_df.to_excel("data/comparison_results.xlsx", index=False)
print("\nComparison results saved to data/comparison_results.xlsx") 