import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("data.csv")

# Basic info
print(df.shape)
print(df.info())
print(df.describe())

# Missing values
print(df.isnull().sum())

# Correlation
sns.heatmap(df.corr(), annot=True, cmap='coolwarm')
plt.show()

# Visualize relationships
sns.pairplot(df)
plt.show()

sns.boxplot(x=df['price'])
plt.title("Outliers in Price")
plt.show()
