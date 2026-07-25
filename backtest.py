import pandas as pd

# CSV読込
df = pd.read_csv(
    "daily_data.csv",
    dtype={"Code": str}
)

print(df.head())

print()

print(df.columns)

print()

print("件数:", len(df))
