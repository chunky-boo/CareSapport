from linebot.v3.messaging import TextMessage, QuickReply
from handlers.menu import handle_top_menu, make_category_quick_reply, _make_quick_reply, handle_select_year, handle_year_selected


def test_handle_top_menu_001():
    """「記録」でカテゴリ選択Quick Replyが返る"""
    result = handle_top_menu("記録")
    assert isinstance(result, TextMessage)
    assert result.text == "何を記録しますか？"
    assert result.quick_reply is not None


def test_handle_top_menu_002():
    """「まとめ」で期間選択Quick Replyが返る"""
    result = handle_top_menu("まとめ")
    assert isinstance(result, TextMessage)
    assert "期間" in result.text
    assert result.quick_reply is not None


def test_handle_top_menu_003():
    """「使い方」でHELP_MESSAGEが返る"""
    result = handle_top_menu("使い方")
    assert isinstance(result, TextMessage)
    assert "ケアサポ" in result.text


def test_handle_top_menu_004():
    """「相談文」で相談文メニューが返る"""
    result = handle_top_menu("相談文")
    assert isinstance(result, TextMessage)
    assert result.quick_reply is not None


def test_handle_top_menu_005():
    """「エクスポート」でエクスポートメニューが返る"""
    result = handle_top_menu("エクスポート")
    assert isinstance(result, TextMessage)
    assert "開始日" in result.text


def test_handle_top_menu_006():
    """「記録を検索」で検索メニューが返る"""
    result = handle_top_menu("記録を検索")
    assert isinstance(result, TextMessage)
    assert "日付" in result.text


def test_handle_top_menu_007():
    """未知のキーワードでNoneが返る"""
    result = handle_top_menu("unknown")
    assert result is None


def test_make_category_quick_reply_001():
    """カテゴリQuick Replyが4件返る"""
    result = make_category_quick_reply()
    assert isinstance(result, QuickReply)
    assert len(result.items) == 4


def test_make_quick_reply_001():
    """ラベルとテキストのペアからQuick Replyが生成される"""
    result = _make_quick_reply([("ラベルA", "テキストA"), ("ラベルB", "テキストB")])
    assert isinstance(result, QuickReply)
    assert len(result.items) == 2


def test_handle_select_year_001():
    """年選択Quick Replyが4件返る"""
    result = handle_select_year()
    assert isinstance(result, TextMessage)
    assert result.quick_reply is not None
    assert len(result.quick_reply.items) == 4


def test_handle_year_selected_001():
    """年を指定するとその年のDatetimePickerが返る"""
    result = handle_year_selected(2025)
    assert isinstance(result, TextMessage)
    assert "2025年" in result.text
    assert result.quick_reply is not None
