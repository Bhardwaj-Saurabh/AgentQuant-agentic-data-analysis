import pandas as pd
import matplotlib.pyplot as plt

original_data = [
    {"date": "2025-09-01", "value": 542},
    {"date": "2025-09-02", "value": 489},
    {"date": "2025-09-03", "value": 563},
    {"date": "2025-09-04", "value": 512},
    {"date": "2025-09-05", "value": 0},
    {"date": "2025-09-06", "value": 598},
    {"date": "2025-09-07", "value": 621},
    {"date": "2025-09-08", "value": 505},
    {"date": "2025-09-09", "value": 0},
    {"date": "2025-09-10", "value": 534},
    {"date": "2025-09-11", "value": 511},
    {"date": "2025-09-12", "value": 490},
    {"date": "2025-09-13", "value": 523},
    {"date": "2025-09-14", "value": 514},
    {"date": "2025-09-15", "value": 2500},
    {"date": "2025-09-16", "value": 527},
    {"date": "2025-09-17", "value": 499},
    {"date": "2025-09-18", "value": 5545},
    {"date": "2025-09-19", "value": 488},
    {"date": "2025-09-20", "value": 531}
]

cleaned_data = [
    {"date": "2025-09-01", "value": 542},
    {"date": "2025-09-02", "value": 489},
    {"date": "2025-09-03", "value": 563},
    {"date": "2025-09-04", "value": 512},
    {"date": "2025-09-06", "value": 598},
    {"date": "2025-09-07", "value": 621},
    {"date": "2025-09-08", "value": 505},
    {"date": "2025-09-10", "value": 534},
    {"date": "2025-09-11", "value": 511},
    {"date": "2025-09-12", "value": 490},
    {"date": "2025-09-13", "value": 523},
    {"date": "2025-09-14", "value": 514},
    {"date": "2025-09-16", "value": 527},
    {"date": "2025-09-17", "value": 499},
    {"date": "2025-09-19", "value": 488},
    {"date": "2025-09-20", "value": 531}
]

df_original = pd.DataFrame(original_data)
df_cleaned = pd.DataFrame(cleaned_data)

df_original['date'] = pd.to_datetime(df_original['date'])
df_cleaned['date'] = pd.to_datetime(df_cleaned['date'])

df_original.set_index('date', inplace=True)
df_cleaned.set_index('date', inplace=True)

df_cleaned = df_cleaned.reindex(df_original.index)

plt.figure(figsize=(10,6))
plt.plot(df_original.index, df_original['value'], label='Original Data', color='blue', marker='o')
plt.plot(df_cleaned.index, df_cleaned['value'], label='Clean Data', color='green', marker='o')

plt.title("Original vs Clean Data")
plt.xlabel("Date")
plt.ylabel("Value")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('artifacts/data_visualization.png', dpi=150, bbox_inches='tight')
plt.close()