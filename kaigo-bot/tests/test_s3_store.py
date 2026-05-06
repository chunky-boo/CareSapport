from unittest.mock import patch
from services.s3_store import upload_csv_and_get_url

_SAMPLE_RECORDS = [
    {"timestamp": "2026-05-01T00:00:00+00:00", "rawMessage": "熱が出た", "category": "体調"},
    {"timestamp": "2026-05-01T03:00:00+00:00", "rawMessage": "薬を飲んだ"},
]


def test_upload_csv_and_get_url_001():
    """記録がS3にアップロードされ、署名付きURLが返る"""
    with patch("services.s3_store._s3") as mock_s3:
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/file.csv"
        url = upload_csv_and_get_url("user1", _SAMPLE_RECORDS, "2026-05-01", "2026-05-31")
        assert url == "https://s3.example.com/file.csv"
        mock_s3.put_object.assert_called_once()
        put_kwargs = mock_s3.put_object.call_args[1]
        assert "user1" in put_kwargs["Key"]
        assert put_kwargs["ContentType"] == "text/csv; charset=utf-8"


def test_upload_csv_and_get_url_002():
    """CSVのBodyがBOM付きUTF-8で生成される"""
    with patch("services.s3_store._s3") as mock_s3:
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/file.csv"
        upload_csv_and_get_url("user1", _SAMPLE_RECORDS, "2026-05-01", "2026-05-31")
        body = mock_s3.put_object.call_args[1]["Body"]
        assert body.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
