from datetime import datetime
import os
import pandas as pd
import jquantsapi

# ==========================
# J-Quants
# ==========================

cli = jquantsapi.ClientV2()

# ==========================
# 取得期間（まずは1か月）
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

# ==========================
# CSV保存
# ==========================

csv_file = "daily_data.csv"

if os.path.exists(csv_file):

    old = pd.read_csv(
        csv_file,
        dtype={"Code": str}
    )

    df = pd.concat(
        [old, df],
        ignore_index=True
    )

    df = df.drop_duplicates(
        subset=["Code", "Date"]
    )

df.to_csv(
    csv_file,
    index=False,
    encoding="utf-8-sig"
)

print(df.head())

print()

print("保存件数:", len(df))
