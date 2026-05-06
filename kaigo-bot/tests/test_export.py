from unittest.mock import patch
from linebot.v3.messaging import TextMessage
from handlers.export import handle_export_menu, handle_export

_SAMPLE_RECORDS = [
    {"timestamp": "2026-05-01T00:00:00+00:00", "rawMessage": "熱が出た", "category": "体調"},
]


def test_handle_export_menu_001():
    """開始日選択DatetimePickerが返る"""
    result = handle_export_menu()
    assert isinstance(result, TextMessage)
    assert "開始日" in result.text
    assert result.quick_reply is not None


def test_handle_export_001():
    """DynamoDB取得エラー時はエラーメッセージが返る"""
    with patch("handlers.export.get_records_by_date_range", side_effect=Exception("DB error")):
        result = handle_export("user1", "2026-05-01", "2026-05-31")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text


def test_handle_export_002():
    """記録が0件のときは「記録がありません」が返る"""
    with patch("handlers.export.get_records_by_date_range", return_value=[]):
        result = handle_export("user1", "2026-05-01", "2026-05-31")
        assert isinstance(result, TextMessage)
        assert "ありません" in result.text


def test_handle_export_003():
    """S3アップロードエラー時はエラーメッセージが返る"""
    with patch("handlers.export.get_records_by_date_range", return_value=_SAMPLE_RECORDS), \
         patch("handlers.export.upload_csv_and_get_url", side_effect=Exception("S3 error")):
        result = handle_export("user1", "2026-05-01", "2026-05-31")
        assert isinstance(result, TextMessage)
        assert "失敗" in result.text


def test_handle_export_004():
    """正常系: CSVのURLを含むメッセージが返る"""
    with patch("handlers.export.get_records_by_date_range", return_value=_SAMPLE_RECORDS), \
         patch("handlers.export.upload_csv_and_get_url", return_value="https://s3.example.com/file.csv"):
        result = handle_export("user1", "2026-05-01", "2026-05-31")
        assert isinstance(result, TextMessage)
        assert "https://s3.example.com/file.csv" in result.text
        assert "1件" in result.text
