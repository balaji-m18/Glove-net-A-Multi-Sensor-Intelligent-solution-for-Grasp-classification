import pandas as pd
import matplotlib.pyplot as plt

# === Configuration ===
file_path = r"C:\Mini Project\Dataset Protocol 2\Filtered Data\Balaji-1.csv"  # Update if path is different

# === Load & preprocess ===
df = pd.read_csv(file_path)

# Convert Timestamp and set it as index
df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
df.set_index('Timestamp', inplace=True)

# Drop unwanted columns
columns_to_exclude = ['Flex1_ADC', 'Flex2_ADC', 'Flex3_ADC']
df.drop(columns=[col for col in columns_to_exclude if col in df.columns], inplace=True)

# === Ensure Only Numeric Columns Are Processed ===
# Convert all columns to numeric, forcing errors to NaN
df = df.apply(pd.to_numeric, errors='coerce')

# === Handle Duplicate Timestamps ===
df = df[~df.index.duplicated(keep='first')]

# Resample data for consistent time intervals (e.g., 1 second)
df_resampled = df.resample('1S').mean()  # Mean of values at each second

# === Plot Each Column Separately ===
for col in df_resampled.select_dtypes(include='number').columns:
    plt.figure(figsize=(10, 6))  # Create a new figure for each plot
    plt.plot(df_resampled.index, df_resampled[col], label=col, marker='o', linestyle='-', linewidth=2)
    
    # Add titles and labels for each plot
    plt.title(f"{col} Over Time", fontsize=14, weight='bold')
    plt.xlabel("Time", fontsize=12)
    plt.ylabel(f"{col} Sensor Reading", fontsize=12)
    
    # Add grid and legend
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='upper left', fontsize=9)
    
    # Adjust layout for better spacing
    plt.tight_layout()
    
    # Show each individual plot
    plt.show()
