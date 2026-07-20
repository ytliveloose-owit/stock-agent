from datetime import datetime
import pandas as pd
import jquantsapi

# ==========================
# J-Quants API
# ==========================
# GitHub Secrets の JQUANTS_API_KEY を自動利用
cli = jquantsapi.ClientV2()

# ==========================
# 取得期間
# ==========================
start_dt = datetime(2026, 4, 27)
end_dt = datetime(2026, 4, 27)

# ==========================
# 日足データ取得
# ==========================
df = cli.get_eq_bars_daily_range(
    start_dt=start_dt,
    end_dt=end_dt
)

# ==========================
# 前日比（％）計算
# ==========================
df["change_rate"] = (
    (df["Close"] - df["PreviousClose"])
    / df["PreviousClose"]
) * 100

# ==========================
# 上場銘柄一覧取得
# ==========================
listing = cli.get_listed_info()

# 東証プライム市場のみ抽出
prime = listing[
    listing["MarketCodeName"] == "プライム"
][["Code", "CompanyName"]]

# ==========================
# 日足データと結合
# ==========================
df = df.merge(
    prime,
    on="Code",
    how="inner"
)

# ==========================
# 条件抽出
# ・東証プライム
# ・前日比 -1～-3%
# ・出来高10万株以上
# ・株価500～5,000円
# ==========================
result = df[
    (df["change_rate"] >= -3) &
    (df["change_rate"] <= -1) &
    (df["Volume"] >= 100000) &
    (df["Close"] >= 500) &
    (df["Close"] <= 5000)
]

# 前日比が大きく下落した順
result = result.sort_values("change_rate")

# 表示する列
result = result[
    [
        "Code",
        "CompanyName",
        "Close",
        "PreviousClose",
        "change_rate",
        "Volume"
    ]
]

# ==========================
# 結果表示
# ==========================
print(result.to_string(index=False))
print()
print(f"取得件数：{len(df)}")
print(f"条件一致：{len(result)}")
