from linebot.v3.messaging import (
    TextMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)
from config import HELP_MESSAGE, CATEGORY_PROMPTS, PERIOD_MAP


def _make_quick_reply(items: list[tuple[str, str]]) -> QuickReply:
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(label=label, text=text))
            for label, text in items
        ]
    )


def handle_top_menu(user_message: str) -> TextMessage | None:
    """「記録」「まとめ」「使い方」キーワードに反応する。それ以外は None を返す。"""
    if user_message == "記録":
        return TextMessage(
            text="何を記録しますか？",
            quick_reply=_make_quick_reply(
                [(f"🩺 体調", "体調を記録"), ("💊 薬", "薬を記録"), ("🍚 食事", "食事を記録")]
            ),
        )
    if user_message == "まとめ":
        return TextMessage(
            text="どの期間のまとめを見ますか?",
            quick_reply=_make_quick_reply(
                [("📅 今日", "今日のまとめ"), ("📊 今週", "今週のまとめ"), ("📆 今月", "今月のまとめ")]
            ),
        )
    if user_message == "使い方":
        return TextMessage(text=HELP_MESSAGE)
    return None
