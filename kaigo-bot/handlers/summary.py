import anthropic
from linebot.v3.messaging import TextMessage
from config import PERIOD_MAP
from services.record_store import get_records_by_period
from services.ai_client import generate

_ERROR_FETCH = "記録の取得に失敗しました。しばらくしてから再度お試しください。"
_ERROR_AI = "まとめの生成に失敗しました。しばらくしてから再度お試しください。"


def handle_summary(user_id: str, user_message: str) -> TextMessage | None:
    """期間別サマリー。PERIOD_MAP にないメッセージは None を返す。"""
    if user_message not in PERIOD_MAP:
        return None

    period = PERIOD_MAP[user_message]

    try:
        records = get_records_by_period(user_id, period)
    except Exception as e:
        print(f"[summary] fetch failed: {e}")
        return TextMessage(text=_ERROR_FETCH)

    if not records:
        return TextMessage(text=f"{period}の記録はまだありません。")

    records_text = "\n".join(
        f"・{r['timestamp'][:10]}: {r['rawMessage']}" for r in records
    )
    prompt = f"以下は{period}の介護記録です。やさしくまとめてください：\n{records_text}"

    try:
        summary_text = generate(prompt)
    except anthropic.APIError as e:
        print(f"[summary] AI failed: {e}")
        return TextMessage(text=_ERROR_AI)

    return TextMessage(text=summary_text)
