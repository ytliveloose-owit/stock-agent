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

master = cli.get_eq_master()


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
# スクリーニング
# ==========================

result = target[

    # 前日1〜3％下落
    (target["ChangeRate"] >= -3) &
    (target["ChangeRate"] <= -1) &


    # 株価
    (target["AdjC"] >= 500) &
    (target["AdjC"] <= 5000) &


    # 流動性
    (target["AdjVo"] >= 100000) &

    (target["TradingValue"] >= 100000000) &


    # 出来高増加
    (target["AdjVo"] >= target["AvgVol5"]) &


    # BB下限付近
    (target["AdjC"] <= target["BB_Lower"] * 1.02) &


    # RSI売られすぎ
    (target["RSI14"] <= 35)

]


# ==========================
# 下落率順
# ==========================

result = result.sort_values(
    "ChangeRate"
)



# ==========================
# Discord文章
# ==========================

if len(result) == 0:

    message = (
        "📉 デイトレ候補なし\n"
        f"対象日：{latest_date}"
    )

else:

    message = (
        "📈 逆張りデイトレ候補\n"
        f"対象日：{latest_date}\n"
        f"該当：{len(result)}銘柄\n\n"
    )


    for _, row in result.head(10).iterrows():

        message += (

            f"🔹 {row['Code']} {row['CoName']}\n"

            f"株価：{row['AdjC']}円\n"

            f"前日比：{row['ChangeRate']:.2f}%\n"

            f"RSI：{row['RSI14']:.1f}\n"

            f"BB下限比："
            f"{row['AdjC']/row['BB_Lower']*100:.1f}%\n"

            f"出来高：{int(row['AdjVo']):,}\n"

            f"売買代金："
            f"{int(row['TradingValue']/10000):,}万円\n\n"

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
