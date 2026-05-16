import anthropic
from datetime import datetime, timezone, timedelta
from linebot.v3.messaging import TextMessage
from config import PERIOD_MAP, SUMMARY_SYSTEM_PROMPT, SUMMARY_MAX_RECORDS
from services.record_store import (
    get_records_by_period,
    get_records_by_date_range,
    get_pending_summary_confirm,
    clear_pending_summary_confirm,
)
from services.ai_client import generate

_ERROR_FETCH = "記録の取得に失敗しました。しばらくしてから再度お試しください。"
_ERROR_AI = "まとめの生成に失敗しました。しばらくしてから再度お試しください。"
_JST = timezone(timedelta(hours=9))


def _build_summary(records: list[dict], period_label: str) -> TextMessage:
    records_text = "\n".join(
        f"・{datetime.fromisoformat(r['timestamp']).astimezone(_JST).strftime('%Y-%m-%d')}: {r['rawMessage']}"
        for r in records
    )
    prompt = f"以下は{period_label}の介護記録です。やさしくまとめてください：\n{records_text}"
    try:
        summary_text = generate(prompt, system=SUMMARY_SYSTEM_PROMPT)
    except anthropic.APIError as e:
        print(f"[summary] AI failed: {e}")
        return TextMessage(text=_ERROR_AI)
    return TextMessage(text=summary_text)


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

    return _build_summary(records, period)


def handle_summary_confirm(user_id: str, user_message: str) -> TextMessage | None:
    """「はい」「いいえ」で期間上限確認に応答する。確認待ち状態がなければ None を返す。"""
    confirm = get_pending_summary_confirm(user_id)
    if not confirm:
        return None
    if user_message == "いいえ":
        clear_pending_summary_confirm(user_id)
        return TextMessage(text="キャンセルしました。")
    if user_message == "はい":
        start_date, end_date = confirm
        clear_pending_summary_confirm(user_id)
        return handle_summary_range(user_id, start_date, end_date)
    # はい/いいえ以外 → ステートをクリアして通常処理へ戻す
    clear_pending_summary_confirm(user_id)
    return None


def handle_summary_range(user_id: str, start_date: str, end_date: str) -> TextMessage:
    """日付範囲指定サマリー。"""
    try:
        records = get_records_by_date_range(user_id, start_date, end_date)
    except Exception as e:
        print(f"[summary] fetch failed: {e}")
        return TextMessage(text=_ERROR_FETCH)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    period_label = f"{start_dt.year}年{start_dt.month}月{start_dt.day}日〜{end_dt.year}年{end_dt.month}月{end_dt.day}日"

    if not records:
        return TextMessage(text=f"{period_label}の記録はありません。")

    return _build_summary(records[-SUMMARY_MAX_RECORDS:], period_label)
