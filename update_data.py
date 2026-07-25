from datetime import datetime
import calendar
import os

import pandas as pd
import jquantsapi

# ==========================
# J-Quants
# ==========================

cli = jquantsapi.ClientV2()

# ==========================
# 取得したい年月を指定
# （ここだけ変更）
# ==========================

YEAR = 2026
MONTH = 6

start_dt = datetime(YEAR, MONTH, 1)

last_day = calendar.monthrange(YEAR, MONTH)[1]

end_dt = datetime(
    YEAR,
    MONTH,
    last_day
)

print("取得期間")
print(start_dt.date(), "～", end_dt.date())

# ==========================
# 日足取得
# ==========================

df = cli.get_eq_bars_daily_range(
    start_dt=start_dt,
    end_dt=end_dt
)

df = df.sort_values(
    ["Code", "Date"]
)

# ==========================
# 東証プライム銘柄のみ
# ==========================

master = cli.get_eq_master()

prime = master[
    master["MktNm"] == "プライム"
][["Code"]]

df = df.merge(
    prime,
    on="Code",
    how="inner"
)

# ==========================
# CSV読み込み
# ==========================

csv_file = "daily_data.csv"

if os.path.exists(csv_file):

    old = pd.read_csv(
        csv_file,
        dtype={"Code": str}
    )

    old["Date"] = pd.to_datetime(
        old["Date"],
        format="mixed"
    )

else:

    old = pd.DataFrame()

# ==========================
# Date型統一
# ==========================

df["Date"] = pd.to_datetime(
    df["Date"],
    format="mixed"
)

# ==========================
# 結合
# ==========================

if not old.empty:

    df = pd.concat(
        [old, df],
        ignore_index=True
    )

# ==========================
# 重複削除
# ==========================

df = (
    df.drop_duplicates(
        subset=["Code", "Date"],
        keep="last"
    )
    .sort_values(
        ["Code", "Date"]
    )
)

# ==========================
# 保存
# ==========================

df.to_csv(
    csv_file,
    index=False,
    encoding="utf-8-sig"
)

print()

print("保存件数:", len(df))

print(df.head())
