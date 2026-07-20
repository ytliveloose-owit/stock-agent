from datetime import datetime, timedelta
import pandas as pd
import jquantsapi

# ==========================
# J-Quants API
# ==========================
cli = jquantsapi.ClientV2()


# ==========================
# 取得期間
# 5日平均出来高計算のため過去5営業日取得
# ==========================
start_dt = datetime(2026, 4, 20)
end_dt = datetime(2026, 4, 27)


# ==========================
# 日足データ取得
# ==========================
df = cli.get_eq_bars_daily_range(
    start_dt=start_dt,
    end_dt=end_dt
)


# ==========================
# 日付順
# ==========================
df = df.sort_values(
    ["Code", "Date"]
)


# ==========================
# 前日終値
# ==========================
df["PrevClose"] = (
    df.groupby("Code")["AdjC"]
    .shift(1)
)


# ==========================
# 前日比(%)
# ==========================
df["ChangeRate"] = (
    (df["AdjC"] - df["PrevClose"])
    / df["PrevClose"]
    * 100
)


# ==========================
# 5日平均出来高
# ==========================
df["AvgVol5"] = (
    df.groupby("Code")["AdjVo"]
    .transform(
        lambda x: x.shift(1).rolling(5).mean()
    )
)


# ==========================
# 売買代金
# 株価 × 出来高
# ==========================
df["TradingValue"] = (
    df["AdjC"] * df["AdjVo"]
)


# ==========================
# 最新日だけ抽出
# ==========================
target = df[
    df["Date"] == pd.Timestamp(end_dt)
]


# ==========================
# 銘柄マスター取得
# ==========================
master = cli.get_eq_master()


# 東証プライム
prime = master[
    master["MktNm"] == "プライム"
][
    [
        "Code",
        "CoName",
        "MktNm"
    ]
]


# 結合
target = target.merge(
    prime,
    on="Code",
    how="inner"
)


# ==========================
# スクリーニング条件
# ==========================
result = target[
    # 前日比 -1～-3%
    (target["ChangeRate"] >= -3) &
    (target["ChangeRate"] <= -1) &

    # 株価200～5000円
    (target["AdjC"] >= 200) &
    (target["AdjC"] <= 5000) &

    # 出来高10万株以上
    (target["AdjVo"] >= 100000) &

    # 売買代金1億円以上
    (target["TradingValue"] >= 100000000) &

    # 前5日平均より出来高増加
    (target["AdjVo"] >= target["AvgVol5"])
]


# ==========================
# 下落率順
# ==========================
result = result.sort_values(
    "ChangeRate"
)


# ==========================
# 表示
# ==========================
result = result[
    [
        "Code",
        "CoName",
        "AdjC",
        "PrevClose",
        "ChangeRate",
        "AdjVo",
        "AvgVol5",
        "TradingValue"
    ]
]


print(result.to_string(index=False))

print()
print(f"該当銘柄数：{len(result)}")
