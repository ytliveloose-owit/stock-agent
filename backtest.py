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
# バックテスト対象期間
# ==========================
START_DATE = "2023-12-01"

END_DATE   = "2026-6-30"

df = df[

    (df["Date"] >= START_DATE) &

    (df["Date"] <= END_DATE)

].copy()

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
# 前日始値
# ==========================

df["PrevOpen"] = (
    df.groupby("Code")["AdjO"]
    .shift(1)
)

# ==========================
# 5日移動平均
# ==========================

df["MA5"] = (
    df.groupby("Code")["AdjC"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(5)
        .mean()
    )
)

# ==========================
# 前日RSI
# ==========================

df["PrevRSI"] = (
    df.groupby("Code")["RSI14"]
    .shift(1)
)

# ==========================
# 翌日の株価
# ==========================

df["NextOpen"] = df.groupby("Code")["AdjO"].shift(-1)
df["NextClose"] = df.groupby("Code")["AdjC"].shift(-1)
df["NextHigh"] = df.groupby("Code")["AdjH"].shift(-1)
df["NextLow"]  = df.groupby("Code")["AdjL"].shift(-1)

# ==========================
# ノイズ除外（完全版）
# ==========================

# --- 1. 決算日っぽい異常値動き ---
df["VolSpike"] = df["AdjVo"] >= df["AvgVol5"] * 3        # 出来高3倍以上
df["BigMove"] = (df["ChangeRate"].abs() >= 10)           # 前日比 ±10%以上
df["BB_Anomaly"] = (
    (df["AdjC"] >= df["BB_Lower"] * 1.05) |              # BB下限から5%以上上
    (df["AdjC"] <= df["BB_Lower"] * 0.95)                # BB下限から5%以上下
)

# --- 2. 配当落ち日（権利落ち日） ---
# 配当落ちは「必ず下がる」ため逆張りのノイズ
df["DividendDrop"] = (
    (df["ChangeRate"] <= -3) &
    (df["AdjVo"] <= df["AvgVol5"] * 1.2)                 # 出来高は増えないことが多い
)

# --- 3. ストップ高・ストップ安の翌日 ---
df["LimitUpDown"] = (
    (df["PrevClose"] > 0) &
    ((df["AdjC"] >= df["PrevClose"] * 1.2) |             # ストップ高翌日
     (df["AdjC"] <= df["PrevClose"] * 0.8))              # ストップ安翌日
)

# --- 4. 大口売買による異常値動き ---
df["WhaleTrade"] = (
    (df["AdjVo"] >= df["AvgVol5"] * 5) |                 # 出来高5倍以上
    (df["ChangeRate"].abs() >= 8)                        # ±8%以上の急変
)

# --- 5. 株式分割・併合などのイベント日（値動きから判定） ---
df["SplitMerge"] = (
    (df["AdjC"] <= df["PrevClose"] * 0.5) |              # 併合で急落
    (df["AdjC"] >= df["PrevClose"] * 1.5)                # 分割で急騰
)

# --- すべてのノイズをまとめて除外 ---
noise_mask = (
    df["VolSpike"] |
    df["BigMove"] |
    df["BB_Anomaly"] |
    df["DividendDrop"] |
    df["LimitUpDown"] |
    df["WhaleTrade"] |
    df["SplitMerge"]
)

df = df[~noise_mask]

# ==========================
# 買いシグナル抽出条件
# ==========================
signal = df[

    # 前日比 -4～-2%
    (df["ChangeRate"] >= -4) &
    (df["ChangeRate"] <= -2) &

    # 株価700～4000円
    (df["AdjC"] >= 700) &
    (df["AdjC"] <= 4000) &

    # 出来高10万株以上
    (df["AdjVo"] >= 100000) &

    # 売買代金2億円以上
    (df["TradingValue"] >= 200000000) &

    # 出来高は5日平均の1.2倍以上
    (df["AdjVo"] >= df["AvgVol5"] * 1.2) &

    # BB下限付近
    (df["AdjC"] <= df["BB_Lower"] * 1.01) &

    # RSI30以下
    (df["RSI14"] <= 33.5) &

    # 当日陽線
    ((df["AdjC"] - df["AdjO"]) / df["AdjO"] >= 0.01) &

    # 5日線より下
    (df["AdjC"] < df["MA5"]*0.99) 

].copy()

# ==========================
# 利確・損切り判定（デイトレ）
# ==========================

# エントリー価格
entry = signal["NextOpen"]

# 利確・損切りライン
tp = entry * 1.025   # +2.5%
sl = entry * 0.98   # -2%

# 判定
def intraday_return(row):
    if pd.isna(row["NextHigh"]) or pd.isna(row["NextLow"]):
        return None

    entry = row["NextOpen"]
    tp = entry * 1.025
    sl = entry * 0.98

    # 利確
    if row["NextHigh"] >= tp:
        return 2.5

    # 損切り
    if row["NextLow"] <= sl:
        return -2.0

    # どちらも到達しない → 終値で決済
    return (row["NextClose"] - entry) / entry * 100

signal["Return"] = signal.apply(intraday_return, axis=1)

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
print(f"対象期間      ：{START_DATE} ～ {END_DATE}")

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
