# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------
import os
print(os.getcwd())

import pandas as pd
import unidecode
import re

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

## Changing TIPO MAGNITUD column in df2
# 1. Change 'ML' to 'Ml' in 'TIPO MAGNITUD'
df2['TIPO MAGNITUD'] = df2['TIPO MAGNITUD'].str.replace(r'^ML', 'Ml', regex=True)

# 2. Remove any suffixes after 'Mlr' (e.g., 'Mlr_2' -> 'Mlr')
df2['TIPO MAGNITUD'] = df2['TIPO MAGNITUD'].str.replace(r'^Mlr(_\d+|_PtoGtn.*)$', 'Mlr', regex=True)

# 3. Change 'Mw(mB)' to 'Mw_mb'
df2['TIPO MAGNITUD'] = df2['TIPO MAGNITUD'].str.replace(r'^Mw\(mB\)$', 'Mw_mb', regex=True)

# 4. Change 'M_MLr' to 'Mlr'
df2['TIPO MAGNITUD'] = df2['TIPO MAGNITUD'].str.replace('M_MLr', 'Mlr', regex=False)

# 5. Change 'Mw(Mwp)' to 'Mwp'
df2['TIPO MAGNITUD'] = df2['TIPO MAGNITUD'].str.replace(r'^Mw\(Mwp\)$', 'Mwp', regex=True)

# 6. Change 'M_Pac' to 'M'
df2['TIPO MAGNITUD'] = df2['TIPO MAGNITUD'].str.replace('M_Pac', 'M', regex=False)

## 'DEPARTAMENTO' and 'MUNICIPIO' variables in df2
# 1. Change 'ARCHIPIELAGO DE SAN ANDRES. PROV. Y STA CATALINA' to 'SAI'
df1['DEPARTAMENTO'] = df1['DEPARTAMENTO'].str.replace('ARCHIPIELAGO DE SAN ANDRES. PROV. Y STA CATALINA', 'SAI', regex=False)

# 2. Change 'ZONA GEOGRAFICA ESPECIAL' to 'CAUCA'
df1['DEPARTAMENTO'] = df1['DEPARTAMENTO'].str.replace('ZONA GEOGRAFICA ESPECIAL', 'CAUCA', regex=False)

# 3: Split 'REGION' into 'MUNICIPIO' and 'RESTO' based on the first '-' separator
split_region = df2['REGION'].str.split(' - ', n=1, expand=True)
df2['MUNICIPIO'] = split_region[0]
df2['RESTO'] = split_region[1]

# 4: Split 'RESTO' into 'DEPARTAMENTO' and 'PAIS' based on the first ',' separator
split_resto = df2['RESTO'].str.split(', ', n=1, expand=True)
df2['DEPARTAMENTO'] = split_resto[0]
df2['PAIS'] = split_resto[1]

# 5: Drop the intermediate 'RESTO' column as it is no longer needed
df2 = df2.drop(columns=['RESTO', 'REGION'])

# 6: Convert all the new columns to uppercase
df2['DEPARTAMENTO'] = df2['DEPARTAMENTO'].str.upper()
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.upper()
df2['PAIS'] = df2['PAIS'].str.upper()

# 7. Replace 'SAN ANDRÉS PROVIDENCIA' with 'SAI'
df2['DEPARTAMENTO'] = df2['DEPARTAMENTO'].str.replace('SAN ANDRÉS PROVIDENCIA', 'SAI', regex=False)

# 8. Remove all accents
df2['DEPARTAMENTO'] = df2['DEPARTAMENTO'].apply(lambda x: unidecode.unidecode(x) if pd.notna(x) else x)
df2['MUNICIPIO'] = df2['MUNICIPIO'].apply(lambda x: unidecode.unidecode(x) if pd.notna(x) else x)

# 9. Replace 'Ñ' with 'N'
df2['DEPARTAMENTO'] = df2['DEPARTAMENTO'].str.replace('Ñ', 'N')
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace('Ñ', 'N')

# 10. Replace spaces between words with '_'
df2['DEPARTAMENTO'] = df2['DEPARTAMENTO'].str.strip()
df2['DEPARTAMENTO'] = df2['DEPARTAMENTO'].str.replace(' ', '_')
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.strip()
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace(' ', '_')

# 11. Remove rows where 'DEPARTAMENTO' is 'ESMERALDAS' or 'CARCHI'
df2 = df2[~df2['DEPARTAMENTO'].isin(['ESMERALDAS', 'CARCHI'])]

# 12. Keep only the text inside parentheses
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace(r'.*\((.*?)\).*', r'\1', regex=True)

# 13. Replace multiple underscores with a single underscore
df2['DEPARTAMENTO'] = df2['DEPARTAMENTO'].str.replace(r'_+', '_', regex=True)
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace(r'_+', '_', regex=True)

# 14. Replace '_ANIMAS' with 'LAS_ANIMAS'
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace('_ANIMAS', 'LAS_ANIMAS', regex=False)

# 15. Remove rows if 'MUNICIPIO' contains any of the specified countries or regions
keywords = [
    "VENEZUELA", "PANAMA", "ECUADOR", "NICARAGUA", "BRASIL", 
    "CENTRAL_AMERICA", "CENTRO_AMERICA", "COSTA_RICA", 
    "PERU", "EL_SALVADOR", "GUATEMALA"
]

df2 = df2[~df2['MUNICIPIO'].str.contains('|'.join(keywords), case=False, na=False)]

# 16. Replace 'CARIBBEAN_SEA' with 'MAR_CARIBE'
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace('CARIBBEAN_SEA', 'MAR_CARIBE', regex=False)

# 17. Replace 'VOLCAN_LASLAS_ANIMAS' with 'VOLCAN_LAS_ANIMAS' and set 'DEPARTAMENTO' to 'CAUCA'
df2.loc[df2['MUNICIPIO'] == 'VOLCAN_LASLAS_ANIMAS', 'MUNICIPIO'] = 'VOLCAN_LAS_ANIMAS'
df2.loc[df2['MUNICIPIO'] == 'VOLCAN_LAS_ANIMAS', 'DEPARTAMENTO'] = 'CAUCA'

# 18. Replace text matching 'AREA_DE_INFLUENCIA_VOLCAN_' with just the volcano name
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace(r'AREA_DE_INFLUENCIA_VOLCAN_(.*)', r'VOLCAN_\1', regex=True)

# 19. Replace 'MANAURE_BALCON_DEL_CESAR' with 'MANAURE'
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace('MANAURE_BALCON_DEL_CESAR', 'MANAURE', regex=False)

# 20. Replace 'AREA_EN_LITIGIO_LIMITES_(PURACE' with 'PURACE'
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace(r'AREA_EN_LITIGIO_LIMITES_\((.*?)\)', r'\1', regex=True)

# Replace 'AREA_EN_LITIGIO_LIMITES_(PURACE' or similar with 'PURACE'
df2['MUNICIPIO'] = df2['MUNICIPIO'].str.replace(r'AREA_EN_LITIGIO_LIMITES_\(([^)]*)', r'\1', regex=True)

# 21. Assign 'MUNICIPIO' and 'DEPARTAMENTO' based on given LATITUDE and LONGITUDE values
coordinates_mapping = {
    (12.192, -71.93): ('URIBIA', 'LA_GUAJIRA'),
    (12.183, -71.934): ('URIBIA', 'LA_GUAJIRA'),
    (12.164, -71.929): ('URIBIA', 'LA_GUAJIRA'),
    (12.192, -71.973): ('URIBIA', 'LA_GUAJIRA'),
    (9.977, -77.737): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.827, -77.126): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (4.059, -77.214): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (9.576, -77.437): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.175, -77.641): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.179, -77.415): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.175, -77.77): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.264, -77.927): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.826, -77.118): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (9.235, -77.936): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.836, -77.142): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (9.714, -73.028): ('BECERRIL', 'CESAR'),
    (9.115, -77.424): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.793, -77.726): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.823, -77.171): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (9.561, -77.314): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.763, -77.173): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.231, -76.437): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.819, -77.124): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.614, -77.198): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (7.962, -76.914): ('TURBO', 'ANTIOQUIA'),
    (9.097, -77.393): ('MAR_CARIBE', 'MAR_CARIBE'),
    (4.266, -77.49): ('GENOVEVA_DE_DOCORDO', 'CHOCO'),
    (5.298, -77.396): ('BAJO_BAUDO', 'CHOCO'),
    (4.025, -77.206): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (4.051, -77.01): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.821, -77.172): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (12.188, -71.945): ('URIBIA', 'LA_GUAJIRA'),
    (3.88, -77.302): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (8.048, -76.824): ('UNGUIA', 'CHOCO'),
    (3.866, -77.122): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (9.051, -77.805): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.005, -77.386): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.887, -77.106): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (5.008, -77.377): ('PIZARRO', 'CHOCO'),
    (9.038, -77.425): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.842, -77.123): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (9.064, -77.453): ('MAR_CARIBE', 'MAR_CARIBE'),
    (8.239, -76.893): ('UNGUIA', 'CHOCO'),
    (8.214, -76.889): ('UNGUIA', 'CHOCO'),
    (12.008, -71.009): ('URIBIA', 'LA_GUAJIRA'),
    (4.039, -77.229): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.829, -77.121): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.658, -77.168): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.871, -77.105): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (8.049, -76.812): ('UNGUIA', 'CHOCO'),
    (3.892, -77.085): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.806, -77.151): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (8.197, -76.941): ('UNGUIA', 'CHOCO'),
    (8.211, -76.748): ('UNGUIA', 'CHOCO'),
    (3.882, -77.079): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (8.004, -76.76): ('APARTADO', 'ANTIOQUIA'),
    (3.829, -77.166): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (6.622, -77.402): ('BAHIA_SOLANO', 'CHOCO'),
    (12.01, -71.009): ('URIBIA', 'LA_GUAJIRA'),
    (8.155, -76.888): ('UNGUIA', 'CHOCO'),
    (3.826, -77.12): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.847, -77.133): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (8.012, -76.843): ('UNGUIA', 'CHOCO'),
    (9.057, -77.552): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.146, -77.684): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.681, -77.171): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (8.037, -76.731): ('TURBO', 'ANTIOQUIA'),
    (3.677, -77.17): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.841, -77.132): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.754, -77.18): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (9.033, -77.562): ('MAR_CARIBE', 'MAR_CARIBE'),
    (4.043, -77.297): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (12.104, -71.018): ('URIBIA', 'LA_GUAJIRA'),
    (6.846, -77.625): ('JURADO', 'CHOCO'),
    (9.042, -77.679): ('MAR_CARIBE', 'MAR_CARIBE'),
    (12.294, -71.177): ('URIBIA', 'LA_GUAJIRA'),
    (9.072, -77.382): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.056, -77.756): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.114, -77.832): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.539, -77.685): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.444, -77.294): ('MAR_CARIBE', 'MAR_CARIBE'),
    (5.321, -77.401): ('BAJO_BAUDO', 'CHOCO'),
    (9.798, -77.967): ('MAR_CARIBE', 'MAR_CARIBE'),
    (9.357, -77.885): ('MAR_CARIBE', 'MAR_CARIBE'),
    (3.793, -76.977): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (4.787, -76.192): ('EL_CAIRO', 'VALLE_DEL_CAUCA'),
    (4.805, -76.187): ('EL_CAIRO', 'VALLE_DEL_CAUCA'),
    (4.926, -76.03): ('EL_AGUILA', 'VALLE_DEL_CAUCA'),
    (4.771, -76.189): ('EL_CAIRO', 'VALLE_DEL_CAUCA'),
    (4.797, -76.174): ('EL_CAIRO', 'VALLE_DEL_CAUCA'),
    (4.718, -76.238): ('EL_CAIRO', 'VALLE_DEL_CAUCA'),
    (4.008, -76.971): ('BUENAVENTURA', 'VALLE_DEL_CAUCA'),
    (3.56, -76.973): ('DAGUA', 'VALLE_DEL_CAUCA')
}

for coords, location in coordinates_mapping.items():
    lat, lon = coords
    municipio, departamento = location
    df2.loc[(df2['LATITUD'] == lat) & (df2['LONGITUD'] == lon), 'MUNICIPIO'] = municipio
    df2.loc[(df2['LATITUD'] == lat) & (df2['LONGITUD'] == lon), 'DEPARTAMENTO'] = departamento

# 22. Replicate 'OCEANO_PACIFICO' and 'MAR_CARIBE' from 'MUNICIPIO' to 'DEPARTAMENTO'
df2.loc[df2['MUNICIPIO'] == 'OCEANO_PACIFICO', 'DEPARTAMENTO'] = 'OCEANO_PACIFICO'
df2.loc[df2['MUNICIPIO'] == 'MAR_CARIBE', 'DEPARTAMENTO'] = 'MAR_CARIBE'

# 23. List of MUNICIPIO values to be removed
municipios_to_remove = [
    'NORTE_COLOMBIA',
    'NEAR_NORTH_COAST_OF_COLOMBIA',
    'CERCA_DE_LA_COSTA_DE_COLOMBIA',
    'CERCA_DE_LA_COSTA_OESTE_DE_COLOMBIA',
    'NORTHERN_COLOMBIA',
    'VOLCAN_CHILES',
    'VOLCAN_CERRO_NEGRO'
]

# Remove rows where MUNICIPIO is in the list
df2 = df2[~df2['MUNICIPIO'].isin(municipios_to_remove)]

# 24. Assign 'NARINO' to 'DEPARTAMENTO' for the specified 'MUNICIPIO' values
df2.loc[df2['MUNICIPIO'] == 'VOLCAN_GALERAS', 'DEPARTAMENTO'] = 'NARINO'
df2.loc[df2['MUNICIPIO'] == 'VOLCAN_AZUFRAL', 'DEPARTAMENTO'] = 'NARINO'
df2.loc[df2['MUNICIPIO'] == 'VOLCAN_NEVADO_DEL_RUIZ', 'DEPARTAMENTO'] = 'CALDAS'
df2.loc[df2['MUNICIPIO'] == 'VOLCAN_NEVADO_DEL_HUILA', 'DEPARTAMENTO'] = 'TOLIMA'




# Save df to a CSV file
df1.to_csv('df1_modified.csv', index=False)
df2.to_csv('df2_modified.csv', index=False)

