import jquantsapi

# GitHub Secrets の JQUANTS_API_KEY を自動利用
cli = jquantsapi.ClientV2()

# ClientV2で利用できるメソッド一覧を表示
print(dir(cli))
