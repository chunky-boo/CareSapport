from unittest.mock import patch, MagicMock
import anthropic
from linebot.v3.messaging import TextMessage
from handlers.record import handle_record_prompt, handle_free_record


def test_handle_record_prompt_001():
    """CATEGORY_PROMPTSに存在するキーワードで促しメッセージが返る"""
    result = handle_record_prompt("体調を記録")
    assert isinstance(result, TextMessage)
    assert "体調" in result.text


def test_handle_record_prompt_002():
    """CATEGORY_PROMPTSに存在しないキーワードでNoneが返る"""
    result = handle_record_prompt("unknown")
    assert result is None


def test_handle_free_record_001():
    """正常系: AI返答が返りDynamoDBに保存される"""
    with patch("handlers.record.generate", return_value="記録しました"), \
         patch("handlers.record.get_pending_category", return_value=None), \
         patch("handlers.record.get_pending_date", return_value=None), \
         patch("handlers.record.save_record") as mock_save, \
         patch("handlers.record.clear_pending_state"):
        result = handle_free_record("user1", "今日元気だった")
        assert isinstance(result, TextMessage)
        assert result.text == "記録しました"
        mock_save.assert_called_once()


def test_handle_free_record_002():
    """AI APIエラー時はエラーメッセージが返る"""
    error = anthropic.APIConnectionError(request=MagicMock())
    with patch("handlers.record.generate", side_effect=error):
        result = handle_free_record("user1", "今日元気だった")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text


def test_handle_free_record_003():
    """pendingCategoryがある場合はカテゴリ付きで保存される"""
    with patch("handlers.record.generate", return_value="記録しました"), \
         patch("handlers.record.get_pending_category", return_value="体調"), \
         patch("handlers.record.get_pending_date", return_value=None), \
         patch("handlers.record.save_record") as mock_save, \
         patch("handlers.record.clear_pending_state"):
        handle_free_record("user1", "熱が出た")
        _, kwargs = mock_save.call_args
        assert kwargs.get("category") == "体調"


def test_handle_free_record_004():
    """pendingDateがある場合は指定日時でタイムスタンプが設定される"""
    with patch("handlers.record.generate", return_value="記録しました"), \
         patch("handlers.record.get_pending_category", return_value=None), \
         patch("handlers.record.get_pending_date", return_value="2026-05-01T09:00"), \
         patch("handlers.record.save_record") as mock_save, \
         patch("handlers.record.clear_pending_state"):
        handle_free_record("user1", "朝の記録")
        _, kwargs = mock_save.call_args
        assert kwargs.get("timestamp") is not None
        assert "2026-05-01" in kwargs.get("timestamp")


def test_handle_free_record_005():
    """DynamoDB保存エラー時もAI返答は返る"""
    with patch("handlers.record.generate", return_value="記録しました"), \
         patch("handlers.record.get_pending_category", return_value=None), \
         patch("handlers.record.get_pending_date", return_value=None), \
         patch("handlers.record.save_record", side_effect=Exception("DB error")), \
         patch("handlers.record.clear_pending_state"):
        result = handle_free_record("user1", "今日元気だった")
        assert isinstance(result, TextMessage)
        assert result.text == "記録しました"
