from datetime import datetime, timezone, timedelta
from linebot.v3.messaging import TextMessage, QuickReply, QuickReplyItem, DatetimePickerAction
from services.record_store import get_records_by_date_range

_JST = timezone(timedelta(hours=9))
_ERROR_FETCH = "記録の取得に失敗しました。しばらくしてから再度お試しください。"


def handle_search_menu() -> TextMessage:
    return TextMessage(
        text="確認したい日付を選んでください。",
        quick_reply=QuickReply(items=[
            QuickReplyItem(action=DatetimePickerAction(
                label="日付を選ぶ", data="action=search_date", mode="date"
            )),
        ]),
    )


def handle_search(user_id: str, date_str: str) -> TextMessage:
    try:
        records = get_records_by_date_range(user_id, date_str, date_str)
    except Exception as e:
        print(f"[search] fetch failed: {e}")
        return TextMessage(text=_ERROR_FETCH)

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    display_date = f"{dt.month}月{dt.day}日"

    if not records:
        return TextMessage(text=f"{display_date}の記録はありません。")

    lines = [f"📋 {display_date}の記録（{len(records)}件）\n"]
    for i, r in enumerate(records, 1):
        ts = datetime.fromisoformat(r["timestamp"]).astimezone(_JST)
        category = f"[{r['category']}] " if r.get("category") else ""
        lines.append(f"{i}. {ts.strftime('%H:%M')} {category}{r['rawMessage']}")

    return TextMessage(text="\n".join(lines))
