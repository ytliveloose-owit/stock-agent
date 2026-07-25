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

# ==========================
# バックテスト結果（売られすぎTOP5）
# ==========================

# 条件に合う銘柄（signal）を日付ごとにグループ化
grouped = signal.groupby("Date")

# 各日の条件銘柄から ChangeRate 昇順でトップ5のみ抽出
top5 = grouped.apply(lambda g: g.sort_values("ChangeRate").head(5))

# groupby.apply の階層インデックスを解除
top5 = top5.reset_index(drop=True)

# 翌日データがあるものだけ残す
top5 = top5.dropna(subset=["Return"])

# バックテスト集計
wins = top5[top5["Return"] > 0]
losses = top5[top5["Return"] <= 0]

trade_count = len(top5)
win_count = len(wins)
loss_count = len(losses)

win_rate = win_count / trade_count * 100 if trade_count > 0 else 0
avg_return = top5["Return"].mean()
avg_win = wins["Return"].mean() if win_count > 0 else 0
avg_loss = losses["Return"].mean() if loss_count > 0 else 0
profit_factor = wins["Return"].sum() / abs(losses["Return"].sum()) if loss_count > 0 else float("inf")

print("=" * 40)
print("トップ5銘柄のみバックテスト結果")
print("=" * 40)
print(f"取引回数      ：{trade_count}")
print(f"勝ち          ：{win_count}")
print(f"負け          ：{loss_count}")
print(f"勝率          ：{win_rate:.2f}%")
print(f"平均利益率    ：{avg_return:.2f}%")
print(f"平均勝ち      ：{avg_win:.2f}%")
print(f"平均負け      ：{avg_loss:.2f}%")
print(f"最大利益      ：{top5['Return'].max():.2f}%")
print(f"最大損失      ：{top5['Return'].min():.2f}%")
print(f"プロフィットファクター：{profit_factor:.2f}")

print()
print("=== 上位20件（トップ5銘柄） ===")
print(top5[
    ["Date", "Code", "AdjC", "NextOpen", "NextClose", "Return"]
].head(20))


# ==========================
# バックテスト結果
# ==========================

# 翌日のデータがない行を除外
signal = signal.dropna(subset=["Return"])

wins = signal[signal["Return"] > 0]
losses = signal[signal["Return"] <= 0]

trade_count = len(signal)
win_count = len(wins)
loss_count = len(losses)

win_rate = (
    win_count / trade_count * 100
    if trade_count > 0 else 0
)

avg_return = signal["Return"].mean()

avg_win = (
    wins["Return"].mean()
    if win_count > 0 else 0
)

avg_loss = (
    losses["Return"].mean()
    if loss_count > 0 else 0
)

profit_factor = (
    wins["Return"].sum() /
    abs(losses["Return"].sum())
    if loss_count > 0 else float("inf")
)

print("=" * 40)
print("バックテスト結果")
print("=" * 40)

print(f"取引回数      ：{trade_count}")
print(f"勝ち          ：{win_count}")
print(f"負け          ：{loss_count}")
print(f"勝率          ：{win_rate:.2f}%")
print(f"平均利益率    ：{avg_return:.2f}%")
print(f"平均勝ち      ：{avg_win:.2f}%")
print(f"平均負け      ：{avg_loss:.2f}%")
print(f"最大利益      ：{signal['Return'].max():.2f}%")
print(f"最大損失      ：{signal['Return'].min():.2f}%")
print(f"プロフィットファクター：{profit_factor:.2f}")

print()
print("=== 上位20件 ===")
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
