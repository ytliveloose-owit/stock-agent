from datetime import datetime, timedelta
import jquantsapi

# GitHub SecretsのJQUANTS_API_KEYを自動で利用
cli = jquantsapi.ClientV2()

from datetime import datetime
start_dt = datetime(2026,4,25)
end_dt = datetime(2026,4,27)

# 日足データ取得
df = cli.get_eq_bars_daily_range(
    start_dt=start_dt,
    end_dt=end_dt
)

print(df.head())
print()
print(f"取得件数: {len(df)}")
