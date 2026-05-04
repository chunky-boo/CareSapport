import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# ① リッチメニューを作成
richmenu_data = {
    "size": {"width": 2500, "height": 843},
    "selected": True,
    "name": "トップメニュー",
    "chatBarText": "メニュー",
    "areas": [
        {
            "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
            "action": {"type": "message", "text": "記録"}
        },
        {
            "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
            "action": {"type": "message", "text": "まとめ"}
        },
        {
            "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
            "action": {"type": "message", "text": "使い方"}
        }
    ]
}

res = requests.post(
    "https://api.line.me/v2/bot/richmenu",
    headers={**HEADERS, "Content-Type": "application/json"},
    json=richmenu_data
)
print("Create:", res.status_code, res.text)
richmenu_id = res.json()["richMenuId"]

# ② 画像をアップロード
with open("richmenu_top_compressed.jpg", "rb") as f:
    res = requests.post(
        f"https://api-data.line.me/v2/bot/richmenu/{richmenu_id}/content",
        headers={**HEADERS, "Content-Type": "image/jpeg"},
        data=f.read()
    )
print("Upload:", res.status_code, res.text)

# ③ デフォルトに設定（全ユーザーに適用）
res = requests.post(
    f"https://api.line.me/v2/bot/user/all/richmenu/{richmenu_id}",
    headers=HEADERS
)
print("Default:", res.status_code, res.text)

print(f"\n✅ Done! Rich Menu ID: {richmenu_id}")