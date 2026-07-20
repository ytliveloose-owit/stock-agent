from datetime import datetime
import pandas as pd
import jquantsapi

# ==========================
# J-Quants API
# ==========================
cli = jquantsapi.ClientV2()

# ==========================
# 前営業日を含めて取得
# ==========================
start_dt = datetime(2026, 4, 24)
end_dt = datetime(2026, 4, 27)

# ==========================
# 日足データ取得
# ==========================
df = cli.get_eq_bars_daily_range(
    start_dt=start_dt,
    end_dt=end_dt
)

# 日付順に並べる
df = df.sort_values(["Code", "Date"])

# 前営業日の終値
df["PrevClose"] = df.groupby("Code")["AdjC"].shift(1)

# 前日比(%)
df["ChangeRate"] = (
    (df["AdjC"] - df["PrevClose"])
    / df["PrevClose"] * 100
)

# 最新日だけ抽出
target = df[df["Date"] == pd.Timestamp(end_dt)]

# ==========================
# 銘柄マスター取得
# ==========================
master = cli.get_eq_master()

# 東証プライム市場のみ
prime = master[
    master["MktNm"] == "プライム"
][["Code", "CoName", "MktNm"]]

# 日足と結合
target = target.merge(
    prime,
    on="Code",
    how="inner"
)

# ==========================
# スクリーニング条件
# ==========================
result = target[
    (target["ChangeRate"] >= -3) &
    (target["ChangeRate"] <= -1) &
    (target["AdjVo"] >= 100000)
]

# 前日比順
result = result.sort_values("ChangeRate")

# ==========================
# 表示
# ==========================
result = result[
    [
        "Code",
        "CoName",
        "MktNm",
        "AdjC",
        "PrevClose",
        "ChangeRate",
        "AdjVo"
    ]
]

print(result.to_string(index=False))

print()
print(f"該当銘柄数：{len(result)}")
