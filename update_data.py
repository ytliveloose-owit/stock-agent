from datetime import datetime
import os
import pandas as pd
import jquantsapi

# ==========================
# J-Quants
# ==========================

cli = jquantsapi.ClientV2()

# ==========================
# 取得期間（1か月）
# ==========================

from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import os

csv_file = "daily_data.csv"

# CSVが存在する場合
if os.path.exists(csv_file):

    old = pd.read_csv(
        csv_file,
        dtype={"Code": str}
    )

    old["Date"] = pd.to_datetime(old["Date"])

    last_date = old["Date"].max()

    # 次の月の1日
    start_dt = (
        last_date.replace(day=1)
        + relativedelta(months=1)
    )

# CSVが無い場合
else:

    old = pd.DataFrame()

    start_dt = datetime(2023, 1, 1)

# ==========================
# 3か月分取得
# ==========================

end_month = start_dt + relativedelta(months=2)

last_day = calendar.monthrange(
    end_month.year,
    end_month.month
)[1]

end_dt = datetime(
    end_month.year,
    end_month.month,
    last_day
)

print(f"取得期間：{start_dt:%Y-%m-%d} ～ {end_dt:%Y-%m-%d}")

print(start_dt)
print(end_dt)

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

df = (
    df.drop_duplicates(
        subset=["Code", "Date"]
    )
    .sort_values(
        ["Code", "Date"]
    )
)

df.to_csv(
    csv_file,
    index=False,
    encoding="utf-8-sig"
)

print(df.head())

print()

print("保存件数:", len(df))
