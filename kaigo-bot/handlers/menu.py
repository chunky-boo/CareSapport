from linebot.v3.messaging import (
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    DatetimePickerAction,
)
from config import HELP_MESSAGE


def _make_quick_reply(items: list[tuple[str, str]]) -> QuickReply:
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(label=label, text=text))
            for label, text in items
        ]
    )


def make_category_quick_reply() -> QuickReply:
    return _make_quick_reply([
        ("🌡 バイタル", "バイタルを記録"),
        ("🩺 体調", "体調を記録"),
        ("💊 薬", "薬を記録"),
        ("🍚 食事", "食事を記録"),
    ])


def handle_top_menu(user_message: str) -> TextMessage | None:
    """「記録」「まとめ」「使い方」キーワードに反応する。それ以外は None を返す。"""
    if user_message == "記録":
        return TextMessage(
            text="何を記録しますか？",
            quick_reply=QuickReply(items=[
                *make_category_quick_reply().items,
                QuickReplyItem(action=DatetimePickerAction(
                    label="📅 別の日", data="action=select_date", mode="datetime"
                )),
            ]),
        )
    if user_message == "まとめ":
        return TextMessage(
            text="どの期間のまとめを見ますか?",
            quick_reply=QuickReply(items=[
                *_make_quick_reply([
                    ("📅 今日", "今日のまとめ"),
                    ("📊 今週", "今週のまとめ"),
                    ("📆 今月", "今月のまとめ"),
                ]).items,
                QuickReplyItem(action=DatetimePickerAction(
                    label="🗓 開始日を選ぶ", data="action=summary_start_date", mode="date"
                )),
            ]),
        )
    if user_message == "使い方":
        return TextMessage(text=HELP_MESSAGE)
    if user_message == "相談文":
        from handlers.consult import handle_consult_menu
        return handle_consult_menu()
    if user_message == "エクスポート":
        from handlers.export import handle_export_menu
        return handle_export_menu()
    if user_message == "記録を検索":
        from handlers.search import handle_search_menu
        return handle_search_menu()
    return None
