import jquantsapi

cli = jquantsapi.ClientV2()

master = cli.get_eq_master()

master.to_csv(
    "eq_master.csv",
    index=False
)

print("銘柄マスター作成完了")
