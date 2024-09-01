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
    'MUNICIPIO': 'CITY',
    'MAGNITUD': 'MAGNITUDE',
    'TIPO MAGNITUD': 'MAGNITUDE TYPE',
    'PROFUNDIDAD': 'DEPTH',
    'FASES': 'PHASES',
    'RMS': 'RMS',
    'GAP': 'GAP'
}, inplace=True)

# ---------------------------------------------------------------------------------------
## 1. EDA for numerical variables
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

# ---------------------------------------------------------------------------------------
## 2. Frequency of non-numerical variables (DEPARTMENT, CITY, MAGNITUDE TYPE).
categorical_vars = ['DEPARTMENT', 'CITY', 'MAGNITUDE TYPE']

for var in categorical_vars:
    if var != 'CITY':
        # Plot frequency for DEPARTMENT and MAGNITUDE TYPE as before
        plt.figure(figsize=(12, 6))
        sns.countplot(data=earthquakes_df, x=var, order=earthquakes_df[var].value_counts().index)
        plt.xticks(rotation=90)
        plt.title(f'Frequency of {var}')
        plt.ylabel('Frequency')
        plt.show()
    else:
        # For CITY, show only the top 20 most frequent values
        top_20_cities = earthquakes_df['CITY'].value_counts().nlargest(20).index
        plt.figure(figsize=(12, 6))
        sns.countplot(data=earthquakes_df[earthquakes_df['CITY'].isin(top_20_cities)],
                      x='CITY', order=top_20_cities)
        plt.xticks(rotation=90)
        plt.title('Frequency of Top 20 Cities')
        plt.ylabel('Frequency')
        plt.show()

# ---------------------------------------------------------------------------------------
## 3. Additional elements important for exploratory data analysis

# Correlation between numerical variables
correlation_matrix = earthquakes_df[numerical_vars].corr()
print("Correlation matrix:\n", correlation_matrix)

# Correlation heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
plt.title('Correlation Matrix Heatmap')
plt.show()

# ---------------------------------------------------------------------------------------
# 5. MANOVA between DEPARTMENT variable and numerical variables
# Filter rows with NaN and encode the categorical variable DEPARTMENT
earthquakes_df.dropna(subset=['DEPARTMENT'] + numerical_vars, inplace=True)
earthquakes_df['DEPARTMENT'] = earthquakes_df['DEPARTMENT'].astype('category')

# Define dependent variables and the independent variable for MANOVA
manova_data = earthquakes_df[numerical_vars]
independent_var = 'DEPARTMENT'
formula = f'{"+".join(numerical_vars)} ~ {independent_var}'

# Run MANOVA
manova = MANOVA.from_formula(formula, data=earthquakes_df)
manova_results = manova.mv_test()
print("MANOVA Results:\n", manova_results)