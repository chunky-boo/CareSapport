# ケアサポ

在宅介護をする家族向けの介護記録 LINE Bot。  
日々の体調・服薬・食事などをLINEで手軽に記録でき、AIが期間別のサマリーを返します。

## 機能

- 自由記述による介護記録（AIがやさしく返答・要約）
- カテゴリ別記録（🌡 バイタル / 🩺 体調 / 💊 薬 / 🍚 食事）
- 別の日付・時刻を指定して記録（DatetimePicker）
- 期間別サマリー（今日・今週・今月・期間指定〜最大1年）
- 医師への相談文の自動生成（直近2週間/1ヶ月/3ヶ月）
- 記録のCSVエクスポート（期間指定→S3署名付きURL）
- 特定日の記録検索（日付指定→生の記録一覧）
- リッチメニュー・Quick Reply によるナビゲーション（6枠）
- 自然な日本語・表記ゆれへの対応（「まとめて」「今週どうだった？」など）
- メンテナンスモード（Lambda環境変数で即時切り替え）

## 技術スタック

| レイヤー | 技術 |
|---|---|
| フロントエンド | LINE Bot（Messaging API v3） |
| バックエンド | Python 3.12 / AWS Lambda |
| エンドポイント | Lambda 関数URL |
| データベース | Amazon DynamoDB（東京リージョン） |
| AI | Claude Haiku 4.5（Anthropic） |

## セットアップ

### 必要な環境変数

```
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
ANTHROPIC_API_KEY=...
S3_BUCKET_NAME=...          # CSVエクスポート用S3バケット名
MAINTENANCE_MODE=false      # trueにするとメンテナンスメッセージを返す
```

### ローカル開発

```bash
cd kaigo-bot
pip install -r requirements.txt flask python-dotenv
python app.py  # ポート3000で起動
```

### Lambda デプロイ

```bash
cd kaigo-bot

rm -rf package && mkdir package
pip install \
  --platform manylinux2014_x86_64 \
  --target=./package \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --upgrade \
  -r requirements.txt

cp lambda_function.py config.py package/
cp -r handlers services package/

cd package && zip -r ../lambda_deploy.zip .
```

AWSコンソールから `lambda_deploy.zip` をアップロード。

## ファイル構成

```
kaigo-bot/
├── lambda_function.py   # Lambda エントリーポイント
├── app.py               # ローカル開発用 Flask サーバー
├── config.py            # 定数・プロンプト・環境変数
├── setup_richmenu.py    # リッチメニュー登録スクリプト（一度だけ実行）
├── handlers/
│   ├── router.py        # メッセージ振り分け（4フェーズ）
│   ├── menu.py          # トップメニュー（記録/まとめ/使い方/相談文/エクスポート/記録を検索）
│   ├── postback.py      # DatetimePicker postbackイベント処理
│   ├── record.py        # 記録処理
│   ├── summary.py       # 期間別サマリー
│   ├── consult.py       # 医師への相談文生成
│   ├── export.py        # CSVエクスポート
│   └── search.py        # 特定日の記録検索
└── services/
    ├── ai_client.py     # Claude API ラッパー
    ├── record_store.py  # DynamoDB CRUD・ステート管理
    └── s3_store.py      # S3アップロード・署名付きURL生成
```

## プライバシーポリシー

[https://chunky-boo.github.io/CareSapport/privacy_policy](https://chunky-boo.github.io/CareSapport/privacy_policy)
