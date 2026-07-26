from datetime import datetime, timedelta
import os
import pandas as pd
import requests
import jquantsapi


# ==========================
# 環境変数
# ==========================

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]


# ==========================
# J-Quants API
# ==========================

cli = jquantsapi.ClientV2()


# ==========================
# 取得期間
# BB・RSI計算のため60日取得
# ==========================

today = datetime.now()

start_dt = today - timedelta(days=60)
end_dt = today - timedelta(days=1)


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
        lambda x:
        x.shift(1)
        .rolling(5)
        .mean()
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
# 20日 ±2σ
# ==========================

df["BB_MA20"] = (
    df.groupby("Code")["AdjC"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(20)
        .mean()
    )
)


df["BB_STD20"] = (
    df.groupby("Code")["AdjC"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(20)
        .std()
    )
)


df["BB_Lower"] = (
    df["BB_MA20"]
    - df["BB_STD20"] * 2
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
# RSI 14日
# ==========================

def calc_rsi(series, period=14):

    delta = series.diff()

    gain = delta.where(
        delta > 0,
        0
    )

    loss = -delta.where(
        delta < 0,
        0
    )

    avg_gain = (
        gain.rolling(period)
        .mean()
    )

    avg_loss = (
        loss.rolling(period)
        .mean()
    )

    rs = avg_gain / avg_loss

    rsi = 100 - (
        100 / (1 + rs)
    )

    return rsi


df["RSI14"] = (
    df.groupby("Code")["AdjC"]
    .transform(calc_rsi)
)


# ==========================
# 最新日
# ==========================

latest_date = df["Date"].max()


target = df[
    df["Date"] == latest_date
]


# ==========================
# 銘柄マスター
# ==========================

master = pd.read_csv(
    "eq_master.csv",
    dtype={"Code": str}
)


prime = master[
    master["MktNm"] == "プライム"
][
    [
        "Code",
        "CoName",
        "MktNm"
    ]
]


target = target.merge(
    prime,
    on="Code",
    how="inner"
)

# ==========================
# ノイズ判定
# ==========================

# 決算などの異常出来高
target["VolSpike"] = (
    target["AdjVo"] >= target["AvgVol5"] * 3
)

# 異常な値動き
target["BigMove"] = (
    target["ChangeRate"].abs() >= 10
)

# BBから離れすぎ
target["BB_Anomaly"] = (
    (target["AdjC"] >= target["BB_Lower"] * 1.05) |
    (target["AdjC"] <= target["BB_Lower"] * 0.95)
)

# 配当落ちっぽい日
target["DividendDrop"] = (
    (target["ChangeRate"] <= -3) &
    (target["AdjVo"] <= target["AvgVol5"] * 1.2)
)

# ストップ高・ストップ安
target["LimitUpDown"] = (
    (target["PrevClose"] > 0) &
    (
        (target["AdjC"] >= target["PrevClose"] * 1.2) |
        (target["AdjC"] <= target["PrevClose"] * 0.8)
    )
)

# 大口売買
target["WhaleTrade"] = (
    (target["AdjVo"] >= target["AvgVol5"] * 5) |
    (target["ChangeRate"].abs() >= 8)
)

# 分割・併合
target["SplitMerge"] = (
    (target["AdjC"] <= target["PrevClose"] * 0.5) |
    (target["AdjC"] >= target["PrevClose"] * 1.5)
)

# ==========================
# ノイズ除去
# ==========================

noise_mask = (

    target["VolSpike"] |
    target["BigMove"] |
    target["BB_Anomaly"] |
    target["DividendDrop"] |
    target["LimitUpDown"] |
    target["WhaleTrade"] |
    target["SplitMerge"]

)

target = target[~noise_mask]

# ==========================
# スコア計算
# ==========================

# 出来高倍率
target["VolRatio"] = target["AdjVo"] / target["AvgVol5"]

# BB下限との距離（100%=BB下限）
target["BBRatio"] = target["AdjC"] / target["BB_Lower"] * 100

# RSI（低いほど高得点）
target["Score_RSI"] = (35 - target["RSI14"]).clip(lower=0, upper=35)

# BB下限に近いほど高得点
target["Score_BB"] = (102 - target["BBRatio"]).clip(lower=0, upper=10) * 3

# 出来高倍率
target["Score_Vol"] = (
    (target["VolRatio"] - 1.2)
    .clip(lower=0, upper=2)
    / 2
    * 20
)

# 前日比（-3%が最高）
target["Score_Drop"] = (
    20
    - (target["ChangeRate"] + 3).abs() * 20
).clip(lower=0)

target["Score"] = (
    target["Score_RSI"]
    + target["Score_BB"]
    + target["Score_Vol"]
    + target["Score_Drop"]
)

# ==========================
# スクリーニング
# ==========================

result = target[

    # 前日比 -4～-2%
    (target["ChangeRate"] >= -4) &
    (target["ChangeRate"] <= -2) &

    # 株価700～3000円
    (target["AdjC"] >= 700) &
    (target["AdjC"] <= 3000) &

    # 出来高10万株以上
    (target["AdjVo"] >= 100000) &

    # 売買代金2億円以上
    (target["TradingValue"] >= 200000000) &

    # 出来高は5日平均の1.2倍以上
    (target["AdjVo"] >= target["AvgVol5"] * 1.2) &

    # BB下限付近
    (target["AdjC"] <= target["BB_Lower"] * 1.01) &

    # RSI32以下
    (target["RSI14"] <= 32) &

    # 当日陽線（1%以上）
    (
        (target["AdjC"] - target["AdjO"])
        / target["AdjO"]
        >= 0.01
    ) &

    # 5日線より1%以上下
    (
        target["AdjC"]
        < target["MA5"] * 0.99
    )

]

# ==========================
# スコア順
# ==========================

result = result.sort_values(
    ["Score", "ChangeRate"],
    ascending=[False, True]
)

# ==========================
# Discord文章
# ==========================

if len(result) == 0:

    message = (
        "📉 デイトレ候補なし\n"
        f"対象日：{latest_date:%Y-%m-%d}"
    )

else:

    message = (
        "📈 逆張りデイトレ候補\n"
        f"対象日：{latest_date:%Y-%m-%d}\n"
        f"該当：{len(result)}銘柄\n"
        "（バックテスト条件一致）\n\n"
    )

    for _, row in result.head(10).iterrows():

        stars = "★" * min(5, int(row["Score"] // 20 + 1))

        message += (
            f"{stars} {row['Score']:.1f}点\n"
            f"🔹 {row['Code']} {row['CoName']}\n"
            f"株価：{row['AdjC']:.1f}円\n"
            f"前日比：{row['ChangeRate']:.2f}%\n"
            f"RSI：{row['RSI14']:.1f}\n"
            f"BB下限比：{row['BBRatio']:.1f}%\n"
            f"出来高倍率：{row['VolRatio']:.2f}倍\n"
            f"5日線乖離：{(row['AdjC'] / row['MA5'] - 1) * 100:.2f}%\n"
            f"売買代金：{row['TradingValue'] / 100000000:.2f}億円\n\n"
        )
        
# ==========================
# Discord送信
# ==========================

if len(message) > 1900:
    message = message[:1900] + "\n...省略"


response = requests.post(
    DISCORD_WEBHOOK_URL,
    json={
        "content": message
    }
)


print("文字数:", len(message))
print("Discord応答:", response.status_code)
print(response.text)

print(message)
