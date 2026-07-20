import os

api_key = os.getenv("JQUANTS_API_KEY")

if api_key:
    print("APIキーを正常に読み込みました。")
    print(f"キーの先頭5文字: {api_key[:5]}*****")
else:
    print("APIキーが読み込めません。")
