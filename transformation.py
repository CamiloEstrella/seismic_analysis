# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------
import os
print(os.getcwd())

import pandas as pd

# ---------------------------------------------------------------------------------------
## 0. Import dataset

# Function to ensure unique column names
def make_column_names_unique(columns):
    seen = set()
    for i, col in enumerate(columns):
        if col in seen:
            counter = 1
            new_col = f"{col}.{counter}"
            while new_col in seen:
                counter += 1
                new_col = f"{col}.{counter}"
            columns[i] = new_col
        seen.add(columns[i])
    return columns

# File prefix and extension (in case needed)
file_prefix = ""  # If there's a prefix, set it here
file_extension = ".csv"

# Dictionary to store the DataFrames
dataframes = {}

# Load each file, handling the header correctly for files 9 to 16
for i in range(1, 17):
    file_name = f"{file_prefix}{i}{file_extension}"
    
    if i < 9:
        # Load the first 8 files normally
        dataframes[file_name] = pd.read_csv(file_name)
    else:
        # Load files 9 to 16, with header at the 14th row (index 13)
        temp_df = pd.read_csv(file_name, header=13)
        temp_df.columns = make_column_names_unique(list(temp_df.columns))
        dataframes[file_name] = temp_df

# ---------------------------------------------------------------------------------------
## 1. Transform dataset

# Combine the first 8 DataFrames into one
df1 = pd.concat([dataframes[f"{i}.csv"] for i in range(1, 9)], ignore_index=True)

# Eliminate the first 13 rows from each DataFrame (already done during read) and then combine them
df2 = pd.concat([dataframes[f"{i}.csv"] for i in range(9, 17)], ignore_index=True)

# Split 'FECHA - HORA UTC' into 'FECHA' and 'HORA_UTC'
df2[['FECHA', 'HORA_UTC']] = df2['FECHA - HORA UTC'].str.split(' ', expand=True)

# Drop the original 'FECHA - HORA UTC' column if no longer needed
df2 = df2.drop(columns=['FECHA - HORA UTC'])

# Rename columns in df1
df1 = df1.rename(columns={
    'LATITUD (grados)': 'LATITUD',
    'LONGITUD (grados)': 'LONGITUD',
    'PROFUNDIDAD (Km)': 'PROFUNDIDAD'
})

# Rename columns in df2
df2 = df2.rename(columns={
    'LATITUD (°)': 'LATITUD',
    'LONGITUD (°)': 'LONGITUD',
    'PROF. (Km)': 'PROFUNDIDAD'
})

# Create a new 'MAGNITUDE' column using the provided rules
df1['MAGNITUDE'] = df1.apply(
    lambda row: row['MAGNITUD Ml'] if pd.notna(row['MAGNITUD Ml']) and (
        pd.isna(row['MAGNITUD Mw']) or row['MAGNITUD Ml'] <= 5.5) else row['MAGNITUD Mw'], axis=1)

# Create a new 'TIPO MAGNITUD' column based on which column was used for 'MAGNITUDE'
df1['TIPO MAGNITUD'] = df1.apply(
    lambda row: 'Ml' if pd.notna(row['MAGNITUD Ml']) and (
        pd.isna(row['MAGNITUD Mw']) or row['MAGNITUD Ml'] <= 5.5) else 'Mw', axis=1)

# Drop the old magnitude columns
df1 = df1.drop(columns=['MAGNITUD Ml', 'MAGNITUD Mw'])

