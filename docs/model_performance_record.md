# 模型效能記錄

## 目前確認的結果

### CoVe 系統整體表現
- **準確率**: 65%
- **測試案例**: 20 個案例
- **一致性**: 與人類評估的匹配案例數 13 個 (65%)
- **不匹配**: 7 個案例 (35%)
- **數據來源**: analysis_report.md
- **測試日期**: 基於 cove_results_20250419_234623.xlsx

### 錯誤分析
- **假陽性 (False Positives)**: 3 案例 (42.9% 的不匹配)
  - CoVe 判斷為 VERIFIED，人類評估為 Fail
- **假陰性 (False Negatives)**: 4 案例 (57.1% 的不匹配)  
  - CoVe 判斷為 UNVERIFIED，人類評估為 Success

### 當前模型配置 (基於 src/config.py)
- **Question Generation**: gpt-4.1
- **React Agent**: claude-3-5-haiku-20241022
- **Final Assessment**: o4-mini (reasoning_effort: high)
- **Aggregation**: o4-mini (reasoning_effort: high)

## 待驗證的結果
- **o3-mini with middle reasoning effort**: 85% (用戶提到但未在代碼庫中找到)

## 實驗歷史
- experiment_report.md: 2025-04-19 實驗，使用 50 輪測試
- 成本: $2.84 USD, 輸入 token: 2,726,766, 輸出 token: 164,133

## 改進建議
1. 引入證據權重系統
2. 設定最小驗證證據比例  
3. 引入信心度評分系統
4. 針對特定類型調整驗證標準