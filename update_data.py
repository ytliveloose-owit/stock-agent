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
# ここだけ変更
# ==========================

YEAR = 2021
MONTH = 9


start_dt = datetime(
    YEAR,
    MONTH,
    1
)

last_day = calendar.monthrange(
    YEAR,
    MONTH
)[1]

end_dt = datetime(
    YEAR,
    MONTH,
    last_day
)


print("取得期間")
print(
    start_dt.date(),
    "～",
    end_dt.date()
)


# ==========================
# 日足取得
# ==========================

df = cli.get_eq_bars_daily_range(
    start_dt=start_dt,
    end_dt=end_dt
)


# ==========================
# 必要列のみ
# ==========================

df = df[
    [
        "Date",
        "Code",
        "AdjO",
        "AdjH",
        "AdjL",
        "AdjC",
        "AdjVo",
    ]
]


df = df.sort_values(
    ["Code", "Date"]
)


# ==========================
# 東証プライム銘柄のみ
# ==========================

master = cli.get_eq_master()


prime = master[
    master["MktNm"] == "プライム"
][
    ["Code"]
]


df = df.merge(
    prime,
    on="Code",
    how="inner"
)


# ==========================
# Date型統一
# ==========================

df["Date"] = pd.to_datetime(
    df["Date"],
    format="mixed"
)


# ==========================
# 年ごとのCSV
# ==========================

csv_file = f"daily_data_{YEAR}.csv"


# ==========================
# 既存CSV読み込み
# ==========================

if os.path.exists(csv_file):

    print()
    print(
        f"既存ファイル読み込み：{csv_file}"
    )

    old = pd.read_csv(
        csv_file,
        dtype={"Code": str}
    )

    old["Date"] = pd.to_datetime(
        old["Date"],
        format="mixed"
    )

else:

    print()
    print(
        f"新規ファイル作成：{csv_file}"
    )

    old = pd.DataFrame()


# ==========================
# 結合
# ==========================

if not old.empty:

    df = pd.concat(
        [
            old,
            df
        ],
        ignore_index=True
    )


# ==========================
# 重複削除
# Code + Date
# ==========================

before = len(df)


df = (
    df
    .drop_duplicates(
        subset=[
            "Code",
            "Date"
        ],
        keep="last"
    )
    .sort_values(
        [
            "Code",
            "Date"
        ]
    )
    .reset_index(drop=True)
)


after = len(df)


print()
print(
    f"重複削除：{before - after:,}件"
)


# ==========================
# 保存
# ==========================

df.to_csv(
    csv_file,
    index=False,
    encoding="utf-8-sig"
)


# ==========================
# 結果表示
# ==========================

print()
print("==========================")
print("保存完了")
print("==========================")

print(
    f"ファイル：{csv_file}"
)

print(
    f"保存件数：{len(df):,}件"
)

print(
    f"ファイルサイズ："
    f"{os.path.getsize(csv_file) / 1024 / 1024:.2f} MB"
)

print()
print(df.head())
