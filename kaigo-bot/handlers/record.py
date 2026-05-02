import anthropic
from linebot.v3.messaging import TextMessage
from config import CATEGORY_PROMPTS
from services.ai_client import generate
from services.record_store import save_record, get_pending_category, set_pending_category

_ERROR_AI = "AIとの通信に失敗しました。しばらくしてから再度お試しください。"
_ERROR_SAVE = "記録の保存に失敗しましたが、返答は生成できました。"


def handle_record_prompt(user_message: str) -> TextMessage | None:
    """カテゴリ選択ボタンへの反応。促しメッセージを返す。それ以外は None。"""
    if user_message not in CATEGORY_PROMPTS:
        return None
    prompt_text, _ = CATEGORY_PROMPTS[user_message]
    return TextMessage(text=prompt_text)


def handle_free_record(user_id: str, user_message: str) -> TextMessage:
    """自由記述の記録処理。常に TextMessage を返す（最終フォールバック）。"""
    try:
        reply_text = generate(user_message)
    except anthropic.APIError:
        return TextMessage(text=_ERROR_AI)

    category = get_pending_category(user_id)
    try:
        save_record(user_id, user_message, reply_text, category=category)
        if category:
            set_pending_category(user_id, None)
    except Exception as e:
        print(f"[record] save failed: {e}")

    return TextMessage(text=reply_text)
