from datetime import datetime, timedelta
from linebot.v3.messaging import TextMessage, QuickReply, QuickReplyItem, DatetimePickerAction, MessageAction
from services.record_store import (
    set_pending_date,
    get_pending_summary_start,
    set_pending_summary_start,
    clear_pending_summary_start,
    set_pending_summary_confirm,
    get_pending_export_start,
    set_pending_export_start,
    clear_pending_export_start,
)
from handlers.menu import make_category_quick_reply
from handlers.summary import handle_summary_range
from handlers.export import handle_export
from handlers.search import handle_search


def handle_postback(user_id: str, data: str, params) -> TextMessage | None:
    if data == "action=select_date":
        datetime_str = params.datetime if hasattr(params, "datetime") else params.get("datetime")
        if not datetime_str:
            return None
        set_pending_date(user_id, datetime_str)
        dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
        display_date = f"{dt.month}月{dt.day}日 {dt.hour:02d}:{dt.minute:02d}"
        return TextMessage(
            text=f"{display_date}の記録ですね。何を記録しますか？",
            quick_reply=make_category_quick_reply(),
        )

    if data == "action=summary_start_date":
        date_str = params.date if hasattr(params, "date") else params.get("date")
        if not date_str:
            return None
        set_pending_summary_start(user_id, date_str)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = f"{dt.year}年{dt.month}月{dt.day}日"
        return TextMessage(
            text=f"{display_date}から、いつまでのまとめですか？",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=DatetimePickerAction(
                    label="終了日を選ぶ", data="action=summary_end_date", mode="date"
                )),
            ]),
        )

    if data == "action=summary_end_date":
        date_str = params.date if hasattr(params, "date") else params.get("date")
        if not date_str:
            return None
        start_date = get_pending_summary_start(user_id)
        if not start_date:
            return TextMessage(text="期間指定がタイムアウトしました。もう一度「まとめ」からお試しください。")
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(date_str, "%Y-%m-%d")
        if end_dt < start_dt:
            clear_pending_summary_start(user_id)
            return TextMessage(text="終了日は開始日以降を選んでください。もう一度「まとめ」からお試しください。")
        clear_pending_summary_start(user_id)
        if (end_dt - start_dt).days > 365:
            capped_end = start_dt + timedelta(days=365)
            capped_end_str = capped_end.strftime("%Y-%m-%d")
            set_pending_summary_confirm(user_id, start_date, capped_end_str)
            display = f"{start_dt.year}年{start_dt.month}月{start_dt.day}日〜{capped_end.year}年{capped_end.month}月{capped_end.day}日（1年間）"
            return TextMessage(
                text=f"1年を超えているため、{display}でのまとめになります。よろしいですか？",
                quick_reply=QuickReply(items=[
                    QuickReplyItem(action=MessageAction(label="はい", text="はい")),
                    QuickReplyItem(action=MessageAction(label="いいえ", text="いいえ")),
                ]),
            )
        set_pending_summary_confirm(user_id, start_date, date_str)
        display = f"{start_dt.year}年{start_dt.month}月{start_dt.day}日〜{end_dt.year}年{end_dt.month}月{end_dt.day}日"
        return TextMessage(
            text=f"{display}のまとめを作成します。よろしいですか？",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label="はい", text="はい")),
                QuickReplyItem(action=MessageAction(label="いいえ", text="いいえ")),
            ]),
        )

    if data == "action=export_start_date":
        date_str = params.date if hasattr(params, "date") else params.get("date")
        if not date_str:
            return None
        set_pending_export_start(user_id, date_str)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = f"{dt.year}年{dt.month}月{dt.day}日"
        return TextMessage(
            text=f"{display_date}から、いつまでのCSVを書き出しますか？",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=DatetimePickerAction(
                    label="終了日を選ぶ", data="action=export_end_date", mode="date"
                )),
            ]),
        )

    if data == "action=export_end_date":
        date_str = params.date if hasattr(params, "date") else params.get("date")
        if not date_str:
            return None
        start_date = get_pending_export_start(user_id)
        if not start_date:
            return TextMessage(text="期間指定がタイムアウトしました。もう一度「エクスポート」からお試しください。")
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(date_str, "%Y-%m-%d")
        if end_dt < start_dt:
            clear_pending_export_start(user_id)
            return TextMessage(text="終了日は開始日以降を選んでください。もう一度「エクスポート」からお試しください。")
        clear_pending_export_start(user_id)
        return handle_export(user_id, start_date, date_str)

    if data == "action=search_date":
        date_str = params.date if hasattr(params, "date") else params.get("date")
        if not date_str:
            return None
        return handle_search(user_id, date_str)

    return None
