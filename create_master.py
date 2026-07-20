import jquantsapi

cli = jquantsapi.ClientV2()

master = cli.get_eq_master()

master.to_csv(
    "eq_master.csv",
    index=False
)
import os
print(os.getcwd())
print("銘柄マスター作成完了")
