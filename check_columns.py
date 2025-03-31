import pandas as pd

# Read the Excel file
df = pd.read_excel("data/LLM evaluation.xlsx", sheet_name="工作表2")
print("Available columns:", df.columns.tolist()) 