import anthropic
from datetime import datetime, timezone, timedelta
from linebot.v3.messaging import TextMessage, QuickReply, QuickReplyItem, MessageAction
from config import CONSULT_PERIOD_MAP, CONSULT_SYSTEM_PROMPT, CONSULT_MAX_TOKENS
from services.record_store import get_records_since
from services.ai_client import generate

_ERROR_FETCH = "記録の取得に失敗しました。しばらくしてから再度お試しください。"
_ERROR_AI = "相談文の生成に失敗しました。しばらくしてから再度お試しください。"
_JST = timezone(timedelta(hours=9))


def handle_consult_menu() -> TextMessage:
    return TextMessage(
        text="何日分の記録をもとに相談文を作りますか？",
        quick_reply=QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="直近2週間", text="相談文（2週間）")),
            QuickReplyItem(action=MessageAction(label="直近1ヶ月", text="相談文（1ヶ月）")),
            QuickReplyItem(action=MessageAction(label="直近3ヶ月", text="相談文（3ヶ月）")),
        ]),
    )


def handle_consult(user_id: str, user_message: str) -> TextMessage | None:
    if user_message not in CONSULT_PERIOD_MAP:
        return None

    days = CONSULT_PERIOD_MAP[user_message]

    try:
        records = get_records_since(user_id, days)
    except Exception as e:
        print(f"[consult] fetch failed: {e}")
        return TextMessage(text=_ERROR_FETCH)

    if not records:
        return TextMessage(text=f"直近{days}日間の記録がありません。")

    records_text = "\n".join(
        f"・{datetime.fromisoformat(r['timestamp']).astimezone(_JST).strftime('%Y-%m-%d')}: [{r.get('category', '未分類')}] {r['rawMessage']}"
        for r in records
    )
    prompt = f"以下は直近{days}日間の介護記録です。医師への相談文を作成してください：\n{records_text}"

    try:
        consult_text = generate(prompt, system=CONSULT_SYSTEM_PROMPT, max_tokens=CONSULT_MAX_TOKENS)
    except anthropic.APIError as e:
        print(f"[consult] AI failed: {e}")
        return TextMessage(text=_ERROR_AI)

    return TextMessage(text=consult_text)
