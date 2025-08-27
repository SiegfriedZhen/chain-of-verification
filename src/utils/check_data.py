import pandas as pd

# Read the Excel file
df = pd.read_excel("data/yt_tsai_secret.xlsx")

# Display basic information about the dataset
print("\nDataset Info:")
print(df.info())

# Display the first few rows
print("\nFirst few rows:")
print(df.head())

# Display column names
print("\nColumn names:")
print(df.columns.tolist()) 