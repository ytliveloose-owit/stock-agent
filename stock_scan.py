import jquantsapi

# GitHub Secrets の JQUANTS_API_KEY を利用
cli = jquantsapi.ClientV2()

# 銘柄マスター取得
master = cli.get_eq_master()

print(master.columns.tolist())
print()
print(master.head())
