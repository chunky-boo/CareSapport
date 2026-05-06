import os
import sys

# Lambda環境変数をテスト用にセット（config.pyがimport時に読むため最初に実行）
os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "test_token"
os.environ["LINE_CHANNEL_SECRET"] = "test_secret"
os.environ["ANTHROPIC_API_KEY"] = "test_key"
os.environ["S3_BUCKET_NAME"] = "test-bucket"
os.environ.setdefault("MAINTENANCE_MODE", "false")

# kaigo-bot ルートをモジュール検索パスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
