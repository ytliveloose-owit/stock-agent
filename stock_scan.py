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
# ==========================

today = datetime.now()

start_dt = today - timedelta(days=10)
end_dt = today - timedelta(days=1)


# ==========================
# 日足取得
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
    (target["ChangeRate"] >= -3) &
    (target["ChangeRate"] <= -1) &

    (target["AdjC"] >= 500) &
    (target["AdjC"] <= 5000) &

    (target["AdjVo"] >= 100000) &

    (target["TradingValue"] >= 100000000) &

    (target["AdjVo"] >= target["AvgVol5"])
]


# ==========================
# 下落率順
# ==========================

result = result.sort_values(
    "ChangeRate"
)


# ==========================
# Discord通知文章作成
# ==========================

if len(result) == 0:

    message = (
        "📉 デイトレ候補なし\n"
        f"対象日：{latest_date}"
    )

else:

    message = (
        "📈 デイトレ候補\n"
        f"対象日：{latest_date}\n"
        f"該当：{len(result)}銘柄\n\n"
    )


    for _, row in result.iterrows():

        message += (
            f"🔹 {row['Code']} {row['CoName']}\n"
            f"株価：{row['AdjC']}円\n"
            f"前日比：{row['ChangeRate']:.2f}%\n"
            f"出来高：{int(row['AdjVo']):,}\n"
            f"売買代金：{int(row['TradingValue']/10000):,}万円\n"
            f"\n"
        )


# ==========================
# Discord送信
# ==========================

requests.post(
    DISCORD_WEBHOOK_URL,
    json={
        "content": message
    }
)
print("文字数:", len(message))
print("Discord応答:", response.status_code)
print(response.text)

# ==========================
# ログ表示
# ==========================

print(message)
