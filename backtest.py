import pandas as pd

# ==========================
# CSV読込
# ==========================

df = pd.read_csv(
    "daily_data.csv",
    dtype={"Code": str}
)

df["Date"] = pd.to_datetime(df["Date"])

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
# 前日比
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
# ==========================

df["TradingValue"] = (
    df["AdjC"] * df["AdjVo"]
)

# ==========================
# ボリンジャーバンド
# ==========================

df["BB_MA20"] = (
    df.groupby("Code")["AdjC"]
    .transform(
        lambda x: x.shift(1).rolling(20).mean()
    )
)

df["BB_STD20"] = (
    df.groupby("Code")["AdjC"]
    .transform(
        lambda x: x.shift(1).rolling(20).std()
    )
)

df["BB_Lower"] = (
    df["BB_MA20"]
    - 2 * df["BB_STD20"]
)

# ==========================
# RSI
# ==========================

def calc_rsi(series, period=14):

    delta = series.diff()

    gain = delta.where(delta > 0, 0)

    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

df["RSI14"] = (
    df.groupby("Code")["AdjC"]
    .transform(calc_rsi)
)

# ==========================
# 翌日の株価
# ==========================

df["NextOpen"] = (
    df.groupby("Code")["AdjO"]
    .shift(-1)
)

df["NextClose"] = (
    df.groupby("Code")["AdjC"]
    .shift(-1)
)

# ==========================
# 条件抽出
# ==========================

signal = df[
    (df["ChangeRate"] >= -3) &
    (df["ChangeRate"] <= -1) &
    (df["AdjC"] >= 500) &
    (df["AdjC"] <= 5000) &
    (df["AdjVo"] >= 100000) &
    (df["TradingValue"] >= 100000000) &
    (df["AdjVo"] >= df["AvgVol5"]) &
    (df["AdjC"] <= df["BB_Lower"] * 1.02) &
    (df["RSI14"] <= 35)
]

# ==========================
# 利益率
# （翌日始値買い→翌日終値売り）
# ==========================

signal["Return"] = (
    (signal["NextClose"] - signal["NextOpen"])
    / signal["NextOpen"]
    * 100
)

print()

print("シグナル数:", len(signal))

print()

print(signal[
    [
        "Date",
        "Code",
        "AdjC",
        "NextOpen",
        "NextClose",
        "Return"
    ]
].head(20))

print()

print("平均利益率")
print(signal["Return"].mean())

print()

print("最大利益")
print(signal["Return"].max())

print()

print("最大損失")
print(signal["Return"].min())
