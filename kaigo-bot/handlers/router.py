from linebot.v3.messaging import TextMessage
from config import (
    CATEGORY_PROMPTS,
    FUZZY_SUMMARY_PERIODS,
    FUZZY_TOP_MENU,
    SUMMARY_INTENT_KEYWORDS,
)
from handlers.menu import handle_top_menu
from handlers.record import handle_record_prompt, handle_free_record
from handlers.summary import handle_summary, handle_summary_confirm
from handlers.consult import handle_consult
from handlers.vital import handle_vital_start, handle_vital_input
from services.record_store import set_pending_category


def route(user_id: str, user_message: str) -> TextMessage:
    """
    メッセージを適切なハンドラに振り分ける。

    新しいハンドラを追加するときは:
      1. handlers/<name>.py に handle_xxx(user_id, user_message) -> TextMessage | None を実装
      2. このファイルにimportとif-blockを1つ追加
      3. トリガーキーワードがあれば config.py に定数を追加
    """
    # Phase 0: 保留中の確認応答（「はい」「いいえ」）
    reply = handle_summary_confirm(user_id, user_message)
    if reply:
        return reply

    # Phase 0.5: バイタル入力フロー中（ステートがなければ None が返るだけ）
    reply = handle_vital_input(user_id, user_message)
    if reply:
        return reply

    # Phase 1: 完全一致（リッチメニュータップ・Quick Reply）
    reply = _dispatch(user_id, user_message)
    if reply:
        return reply

    # Phase 2: 部分一致・表記ゆれ・自然な日本語対応
    reply = _fuzzy_match(user_id, user_message)
    if reply:
        return reply

    # Phase 3: 自由記述の記録（最終フォールバック）
    return handle_free_record(user_id, user_message)


def _dispatch(user_id: str, message: str) -> TextMessage | None:
    """正規キーワードで完全一致ハンドラを順番に試す。"""
    reply = handle_top_menu(message)
    if reply:
        return reply

    if message == "バイタルを記録":
        return handle_vital_start(user_id)

    reply = handle_record_prompt(message)
    if reply:
        _, category = CATEGORY_PROMPTS[message]
        set_pending_category(user_id, category)
        return reply

    reply = handle_summary(user_id, message)
    if reply:
        return reply

    reply = handle_consult(user_id, message)
    if reply:
        return reply

    return None


def _fuzzy_match(user_id: str, message: str) -> TextMessage | None:
    """
    キーワードの部分一致で意図を推定し、正規キーワードに変換して _dispatch に流す。

    判定順序:
      1. 期間キーワード + サマリー意図キーワード → 期間別サマリー
      2. トップメニューキーワード → 記録/まとめ/使い方メニュー
    """
    # 期間 + サマリー意図 → 特定期間のサマリー
    # 例: 「今週どうだった？」「先週の様子教えて」「今日のまとめ見せて」
    for canonical, period_keywords in FUZZY_SUMMARY_PERIODS.items():
        has_period = any(kw in message for kw in period_keywords)
        has_intent = any(kw in message for kw in SUMMARY_INTENT_KEYWORDS)
        if has_period and has_intent:
            return _dispatch(user_id, canonical)

    # トップメニューキーワード → 正規キーワードに変換
    # 例: 「きろく」→「記録」,「まとめて」→「まとめ」
    for canonical, keywords in FUZZY_TOP_MENU.items():
        if any(kw in message for kw in keywords):
            return _dispatch(user_id, canonical)

    return None
