import pandas as pd

# Read the Excel file
excel_file = pd.ExcelFile("data/LLM evaluation.xlsx")
print("Available sheets:", excel_file.sheet_names) 