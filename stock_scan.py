from datetime import datetime, timedelta
import jquantsapi

# GitHub SecretsのJQUANTS_API_KEYを自動で利用
cli = jquantsapi.ClientV2()

# 今日と昨日
end_dt = datetime.now()
start_dt = end_dt - timedelta(days=1)

# 日足データ取得
df = cli.get_eq_bars_daily_range(
    start_dt=start_dt,
    end_dt=end_dt
)

print(df.head())
print()
print(f"取得件数: {len(df)}")
