import jquantsapi

cli = jquantsapi.ClientV2()

master = cli.get_eq_master()

master.to_csv(
    "eq_master.csv",
    index=False,
    encoding="utf-8-sig"
)

print("eq_master.csv 作成完了")
