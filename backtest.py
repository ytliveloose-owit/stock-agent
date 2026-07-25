from datetime import datetime
import pandas as pd
import jquantsapi

# ==========================
# J-Quants
# ==========================
cli = jquantsapi.ClientV2()

# ==========================
# 取得期間
# ==========================
start_dt = datetime(2025, 1, 1)
end_dt = datetime(2025, 1, 31)

# ==========================
# 日足取得
# ==========================
df = cli.get_eq_bars_daily_range(
    start_dt=start_dt,
    end_dt=end_dt
)

# ==========================
# 並び替え
# ==========================
df = df.sort_values(
    ["Code", "Date"]
)

print(df.head())
print(df.tail())

print()

print("取得件数")
print(len(df))

print()

print("銘柄数")
print(df["Code"].nunique())

print()

print("営業日数")
print(df["Date"].nunique())
