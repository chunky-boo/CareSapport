from linebot.v3.messaging import TextMessage, QuickReply, QuickReplyItem, DatetimePickerAction
from services.record_store import get_records_by_date_range
from services.s3_store import upload_csv_and_get_url
from datetime import datetime

_ERROR_FETCH = "記録の取得に失敗しました。しばらくしてから再度お試しください。"
_ERROR_EXPORT = "CSVの作成に失敗しました。しばらくしてから再度お試しください。"


def handle_export_menu() -> TextMessage:
    return TextMessage(
        text="書き出す期間の開始日を選んでください。",
        quick_reply=QuickReply(items=[
            QuickReplyItem(action=DatetimePickerAction(
                label="開始日を選ぶ", data="action=export_start_date", mode="date"
            )),
        ]),
    )


def handle_export(user_id: str, start_date: str, end_date: str) -> TextMessage:
    try:
        records = get_records_by_date_range(user_id, start_date, end_date)
    except Exception as e:
        print(f"[export] fetch failed: {e}")
        return TextMessage(text=_ERROR_FETCH)

    if not records:
        return TextMessage(text="指定期間の記録がありません。")

    try:
        url = upload_csv_and_get_url(user_id, records, start_date, end_date)
    except Exception as e:
        print(f"[export] upload failed: {e}")
        return TextMessage(text=_ERROR_EXPORT)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    display = f"{start_dt.month}月{start_dt.day}日〜{end_dt.month}月{end_dt.day}日（{len(records)}件）"

    return TextMessage(text=f"📥 {display}の記録をCSVにしました。1時間以内にダウンロードしてください。\n\n{url}")
