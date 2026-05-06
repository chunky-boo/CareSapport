from unittest.mock import patch
from linebot.v3.messaging import TextMessage
from handlers.search import handle_search_menu, handle_search

_SAMPLE_RECORDS = [
    {"timestamp": "2026-05-01T01:00:00+00:00", "rawMessage": "熱が出た", "category": "体調"},
    {"timestamp": "2026-05-01T03:00:00+00:00", "rawMessage": "薬を飲んだ"},
]


def test_handle_search_menu_001():
    """日付選択DatetimePickerが返る"""
    result = handle_search_menu()
    assert isinstance(result, TextMessage)
    assert "日付" in result.text
    assert result.quick_reply is not None


def test_handle_search_001():
    """DynamoDB取得エラー時はエラーメッセージが返る"""
    with patch("handlers.search.get_records_by_date_range", side_effect=Exception("DB error")):
        result = handle_search("user1", "2026-05-01")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text


def test_handle_search_002():
    """記録が0件のときは「記録はありません」が返る"""
    with patch("handlers.search.get_records_by_date_range", return_value=[]):
        result = handle_search("user1", "2026-05-01")
        assert isinstance(result, TextMessage)
        assert "ありません" in result.text


def test_handle_search_003():
    """カテゴリあり・なし混在の記録が一覧表示される"""
    with patch("handlers.search.get_records_by_date_range", return_value=_SAMPLE_RECORDS):
        result = handle_search("user1", "2026-05-01")
        assert isinstance(result, TextMessage)
        assert "2件" in result.text
        assert "[体調]" in result.text
        assert "熱が出た" in result.text
        assert "薬を飲んだ" in result.text
