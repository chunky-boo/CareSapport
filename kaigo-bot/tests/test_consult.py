from unittest.mock import patch, MagicMock
import anthropic
from linebot.v3.messaging import TextMessage
from handlers.consult import handle_consult_menu, handle_consult

_SAMPLE_RECORDS = [
    {"timestamp": "2026-05-01T00:00:00+00:00", "rawMessage": "熱が出た", "category": "体調"},
]

# JST 01:00 (深夜) = UTC 前日 16:00 → [:10] では日付が1日ずれるケース
_LATE_NIGHT_RECORDS = [
    {"timestamp": "2026-05-01T16:00:00+00:00", "rawMessage": "深夜に記録", "category": "体調"},  # JST: 2026-05-02T01:00
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


def test_handle_consult_007():
    """カテゴリなしの記録は「その他」としてプロンプトに渡される"""
    no_category_record = [{"timestamp": "2026-05-01T00:00:00+00:00", "rawMessage": "記録"}]
    captured = {}
    def fake_generate(prompt, **kwargs):
        captured["prompt"] = prompt
        return "相談文"
    with patch("handlers.consult.get_records_since", return_value=no_category_record), \
         patch("handlers.consult.generate", side_effect=fake_generate):
        handle_consult("user1", "相談文（2週間）")
    assert "[その他]" in captured["prompt"]
    assert "[未分類]" not in captured["prompt"]


def test_handle_consult_008():
    """CONSULT_MAX_RECORDSを超える記録は最新件数に切り詰められる"""
    from config import CONSULT_MAX_RECORDS
    from datetime import datetime, timezone, timedelta
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    many_records = [
        {"timestamp": (base + timedelta(days=i)).isoformat(), "rawMessage": f"記録{i}", "category": "体調"}
        for i in range(CONSULT_MAX_RECORDS + 10)
    ]
    captured = {}
    def fake_generate(prompt, **kwargs):
        captured["prompt"] = prompt
        return "相談文"
    with patch("handlers.consult.get_records_since", return_value=many_records), \
         patch("handlers.consult.generate", side_effect=fake_generate):
        handle_consult("user1", "相談文（3ヶ月）")
    # プロンプト内の記録件数がMAX以下であること
    assert captured["prompt"].count("・") <= CONSULT_MAX_RECORDS


def test_handle_consult_006():
    """深夜(JST)の記録日付がJSTで正しくプロンプトに渡される（UTC日付でない）"""
    captured = {}
    def fake_generate(prompt, **kwargs):
        captured["prompt"] = prompt
        return "相談文"
    with patch("handlers.consult.get_records_since", return_value=_LATE_NIGHT_RECORDS), \
         patch("handlers.consult.generate", side_effect=fake_generate):
        handle_consult("user1", "相談文（2週間）")
    # UTC[:10]="2026-05-01" ではなく JST日付="2026-05-02" が含まれること
    assert "2026-05-02" in captured["prompt"]
    assert "2026-05-01" not in captured["prompt"]
