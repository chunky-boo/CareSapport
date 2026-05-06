from unittest.mock import patch, MagicMock
import anthropic
from linebot.v3.messaging import TextMessage
from handlers.consult import handle_consult_menu, handle_consult

_SAMPLE_RECORDS = [
    {"timestamp": "2026-05-01T00:00:00+00:00", "rawMessage": "熱が出た", "category": "体調"},
]


def test_handle_consult_menu_001():
    """期間選択Quick Reply（3件）が返る"""
    result = handle_consult_menu()
    assert isinstance(result, TextMessage)
    assert result.quick_reply is not None
    assert len(result.quick_reply.items) == 3


def test_handle_consult_001():
    """CONSULT_PERIOD_MAPにないキーワードでNoneが返る"""
    result = handle_consult("user1", "unknown")
    assert result is None


def test_handle_consult_002():
    """DynamoDB取得エラー時はエラーメッセージが返る"""
    with patch("handlers.consult.get_records_since", side_effect=Exception("DB error")):
        result = handle_consult("user1", "相談文（2週間）")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text


def test_handle_consult_003():
    """記録が0件のときは「記録がありません」が返る"""
    with patch("handlers.consult.get_records_since", return_value=[]):
        result = handle_consult("user1", "相談文（2週間）")
        assert isinstance(result, TextMessage)
        assert "ありません" in result.text


def test_handle_consult_004():
    """記録がある場合はAI生成の相談文が返る"""
    with patch("handlers.consult.get_records_since", return_value=_SAMPLE_RECORDS), \
         patch("handlers.consult.generate", return_value="先生への相談文です"):
        result = handle_consult("user1", "相談文（2週間）")
        assert isinstance(result, TextMessage)
        assert result.text == "先生への相談文です"


def test_handle_consult_005():
    """AI APIエラー時はエラーメッセージが返る"""
    error = anthropic.APIConnectionError(request=MagicMock())
    with patch("handlers.consult.get_records_since", return_value=_SAMPLE_RECORDS), \
         patch("handlers.consult.generate", side_effect=error):
        result = handle_consult("user1", "相談文（1ヶ月）")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text
