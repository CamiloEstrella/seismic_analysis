# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------
import os
print(os.getcwd())

import pandas as pd
import numpy as np
import matplotlib
print(matplotlib.get_backend())
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.multivariate.manova import MANOVA

# ---------------------------------------------------------------------------------------
## 0. Import dataset

earthquakes_df = pd.read_csv('earthquakes.csv')

# Rename columns to English
earthquakes_df.rename(columns={
    'FECHA': 'DATE',
    'HORA_UTC': 'TIME_UTC',
    'LATITUD': 'LATITUDE',
    'LONGITUD': 'LONGITUDE',
    'DEPARTAMENTO': 'DEPARTMENT',
    'MUNICIPIO': 'MUNICIPALITY',
    'MAGNITUD': 'MAGNITUDE',
    'TIPO MAGNITUD': 'MAGNITUDE TYPE',
    'PROFUNDIDAD': 'DEPTH',
    'FASES': 'PHASES',
    'RMS': 'RMS',
    'GAP': 'GAP'
}, inplace=True)

# ---------------------------------------------------------------------------------------
## 0. EDA for numerical variables
numerical_vars = ['MAGNITUDE', 'DEPTH', 'PHASES', 'RMS', 'GAP']
eda_numerical = earthquakes_df[numerical_vars].describe()
print("Description of numerical variables:\n", eda_numerical)

# Histogram for each numerical variable
for var in numerical_vars:
    plt.figure(figsize=(8, 5))
    sns.histplot(earthquakes_df[var], kde=True)
    plt.title(f'Histogram of {var}')
    plt.xlabel(var)
    plt.ylabel('Frequency')
    plt.show()

# Boxplot for each numerical variable
plt.figure(figsize=(10, 6))
earthquakes_df[numerical_vars].plot(kind='box', subplots=True, layout=(2, 3), figsize=(15, 10))
plt.suptitle('Boxplots of Numerical Variables')
plt.show()