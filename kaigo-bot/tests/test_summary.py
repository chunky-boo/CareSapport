from unittest.mock import patch, MagicMock
import anthropic
from linebot.v3.messaging import TextMessage
from handlers.summary import (
    _build_summary,
    handle_summary,
    handle_summary_confirm,
    handle_summary_range,
)

_SAMPLE_RECORDS = [
    {"timestamp": "2026-05-01T00:00:00+00:00", "rawMessage": "熱が出た", "category": "体調"},
]


def test_build_summary_001():
    """AI生成成功時はサマリーテキストが返る"""
    with patch("handlers.summary.generate", return_value="今週は体調不良が1回ありました"):
        result = _build_summary(_SAMPLE_RECORDS, "今週")
        assert isinstance(result, TextMessage)
        assert result.text == "今週は体調不良が1回ありました"


def test_build_summary_002():
    """AI APIエラー時はエラーメッセージが返る"""
    error = anthropic.APIConnectionError(request=MagicMock())
    with patch("handlers.summary.generate", side_effect=error):
        result = _build_summary(_SAMPLE_RECORDS, "今週")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text


def test_handle_summary_001():
    """PERIOD_MAPにないキーワードでNoneが返る"""
    result = handle_summary("user1", "unknown")
    assert result is None


def test_handle_summary_002():
    """DynamoDB取得エラー時はエラーメッセージが返る"""
    with patch("handlers.summary.get_records_by_period", side_effect=Exception("DB error")):
        result = handle_summary("user1", "今日のまとめ")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text


def test_handle_summary_003():
    """記録が0件のときは「記録はまだありません」が返る"""
    with patch("handlers.summary.get_records_by_period", return_value=[]):
        result = handle_summary("user1", "今日のまとめ")
        assert isinstance(result, TextMessage)
        assert "ありません" in result.text


def test_handle_summary_004():
    """記録がある場合はAIサマリーが返る"""
    with patch("handlers.summary.get_records_by_period", return_value=_SAMPLE_RECORDS), \
         patch("handlers.summary.generate", return_value="まとめ結果"):
        result = handle_summary("user1", "今日のまとめ")
        assert isinstance(result, TextMessage)
        assert result.text == "まとめ結果"


def test_handle_summary_confirm_001():
    """確認待ち状態がなければNoneが返る"""
    with patch("handlers.summary.get_pending_summary_confirm", return_value=None):
        result = handle_summary_confirm("user1", "はい")
        assert result is None


def test_handle_summary_confirm_002():
    """「いいえ」でキャンセルメッセージが返る"""
    with patch("handlers.summary.get_pending_summary_confirm", return_value=("2026-01-01", "2026-12-31")), \
         patch("handlers.summary.clear_pending_summary_confirm"):
        result = handle_summary_confirm("user1", "いいえ")
        assert isinstance(result, TextMessage)
        assert "キャンセル" in result.text


def test_handle_summary_confirm_003():
    """「はい」でサマリーが生成される"""
    with patch("handlers.summary.get_pending_summary_confirm", return_value=("2026-01-01", "2026-03-31")), \
         patch("handlers.summary.clear_pending_summary_confirm"), \
         patch("handlers.summary.get_records_by_date_range", return_value=_SAMPLE_RECORDS), \
         patch("handlers.summary.generate", return_value="サマリー結果"):
        result = handle_summary_confirm("user1", "はい")
        assert isinstance(result, TextMessage)
        assert result.text == "サマリー結果"


def test_handle_summary_confirm_004():
    """「はい」「いいえ」以外はNoneが返る"""
    with patch("handlers.summary.get_pending_summary_confirm", return_value=("2026-01-01", "2026-12-31")):
        result = handle_summary_confirm("user1", "わからない")
        assert result is None


def test_handle_summary_range_001():
    """DynamoDB取得エラー時はエラーメッセージが返る"""
    with patch("handlers.summary.get_records_by_date_range", side_effect=Exception("DB error")):
        result = handle_summary_range("user1", "2026-05-01", "2026-05-31")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text


def test_handle_summary_range_002():
    """記録が0件のときは「記録はありません」が返る"""
    with patch("handlers.summary.get_records_by_date_range", return_value=[]):
        result = handle_summary_range("user1", "2026-05-01", "2026-05-31")
        assert isinstance(result, TextMessage)
        assert "ありません" in result.text


def test_handle_summary_range_003():
    """記録がある場合はAIサマリーが返る"""
    with patch("handlers.summary.get_records_by_date_range", return_value=_SAMPLE_RECORDS), \
         patch("handlers.summary.generate", return_value="期間サマリー"):
        result = handle_summary_range("user1", "2026-05-01", "2026-05-31")
        assert isinstance(result, TextMessage)
        assert result.text == "期間サマリー"
