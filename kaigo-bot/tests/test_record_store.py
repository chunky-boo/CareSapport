from unittest.mock import patch, MagicMock
from services.record_store import (
    save_record, get_records_by_period, get_records_since,
    get_records_by_date_range,
    get_pending_category, set_pending_category,
    get_pending_date, set_pending_date, clear_pending_state,
    get_pending_summary_start, set_pending_summary_start, clear_pending_summary_start,
    get_pending_summary_confirm, set_pending_summary_confirm, clear_pending_summary_confirm,
    get_pending_export_start, set_pending_export_start, clear_pending_export_start,
    get_pending_vital_step, set_pending_vital_step,
    get_pending_vital_data, set_pending_vital_data, clear_pending_vital,
)

_SAMPLE_RECORDS = [
    {"userId": "user1", "timestamp": "2026-05-01T00:00:00+00:00", "rawMessage": "熱が出た", "category": "体調"},
    {"userId": "user1", "timestamp": "state"},  # rawMessageなし → フィルタされる
]


# --- save_record ---

def test_save_record_001():
    """カテゴリなしで記録が保存される"""
    with patch("services.record_store._table") as mock_table:
        save_record("user1", "熱が出た", "要約")
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["rawMessage"] == "熱が出た"
        assert "category" not in item


def test_save_record_002():
    """カテゴリありで記録が保存される"""
    with patch("services.record_store._table") as mock_table:
        save_record("user1", "熱が出た", "要約", category="体調")
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["category"] == "体調"


def test_save_record_003():
    """timestamp指定で記録が保存される"""
    with patch("services.record_store._table") as mock_table:
        save_record("user1", "熱が出た", "要約", timestamp="2026-05-01T00:00:00+00:00")
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["timestamp"] == "2026-05-01T00:00:00+00:00"


# --- get_records_by_period ---

def test_get_records_by_period_001():
    """「今日」の記録が返り、rawMessageなしのアイテムはフィルタされる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.query.return_value = {"Items": _SAMPLE_RECORDS}
        result = get_records_by_period("user1", "今日")
        assert len(result) == 1
        assert result[0]["rawMessage"] == "熱が出た"


def test_get_records_by_period_002():
    """「今月」の記録が返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.query.return_value = {"Items": _SAMPLE_RECORDS}
        result = get_records_by_period("user1", "今月")
        assert len(result) == 1


def test_get_records_by_period_003():
    """未知の期間はデフォルト(今週)で動作する"""
    with patch("services.record_store._table") as mock_table:
        mock_table.query.return_value = {"Items": []}
        result = get_records_by_period("user1", "unknown")
        assert result == []


# --- get_records_since ---

def test_get_records_since_001():
    """指定日数分の記録が返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.query.return_value = {"Items": _SAMPLE_RECORDS}
        result = get_records_since("user1", 14)
        assert len(result) == 1


# --- get_records_by_date_range ---

def test_get_records_by_date_range_001():
    """指定期間の記録が返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.query.return_value = {"Items": _SAMPLE_RECORDS}
        result = get_records_by_date_range("user1", "2026-05-01", "2026-05-31")
        assert len(result) == 1


# --- pendingCategory ---

def test_get_pending_category_001():
    """pendingCategoryが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingCategory": "体調"}}
        assert get_pending_category("user1") == "体調"


def test_get_pending_category_002():
    """ステートが空のときNoneが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {}
        assert get_pending_category("user1") is None


def test_set_pending_category_001():
    """pendingCategoryをセットするとput_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        set_pending_category("user1", "体調")
        mock_table.put_item.assert_called_once()


def test_set_pending_category_002():
    """pendingCategory=NoneのときステートからKeyが削除される"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingCategory": "体調"}}
        set_pending_category("user1", None)
        mock_table.delete_item.assert_called_once()


# --- pendingDate ---

def test_get_pending_date_001():
    """pendingDateが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingDate": "2026-05-01T09:00"}}
        assert get_pending_date("user1") == "2026-05-01T09:00"


def test_set_pending_date_001():
    """pendingDateをセットするとput_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        set_pending_date("user1", "2026-05-01T09:00")
        mock_table.put_item.assert_called_once()


def test_set_pending_date_002():
    """pendingDate=NoneのときステートからKeyが削除される"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingDate": "2026-05-01T09:00"}}
        set_pending_date("user1", None)
        mock_table.delete_item.assert_called_once()


def test_clear_pending_state_001():
    """ステートアイテムが削除される"""
    with patch("services.record_store._table") as mock_table:
        clear_pending_state("user1")
        mock_table.delete_item.assert_called_once()


# --- pendingSummaryStart ---

def test_get_pending_summary_start_001():
    """pendingSummaryStartが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingSummaryStart": "2026-05-01"}}
        assert get_pending_summary_start("user1") == "2026-05-01"


def test_set_pending_summary_start_001():
    """pendingSummaryStartをセットするとput_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        set_pending_summary_start("user1", "2026-05-01")
        mock_table.put_item.assert_called_once()


def test_clear_pending_summary_start_001():
    """pendingSummaryStartを削除するとdelete_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingSummaryStart": "2026-05-01"}}
        clear_pending_summary_start("user1")
        mock_table.delete_item.assert_called_once()


# --- pendingSummaryConfirm ---

def test_get_pending_summary_confirm_001():
    """start/endが両方あるときタプルが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {
            "Item": {"pendingConfirmStart": "2026-05-01", "pendingConfirmEnd": "2026-05-31"}
        }
        result = get_pending_summary_confirm("user1")
        assert result == ("2026-05-01", "2026-05-31")


def test_get_pending_summary_confirm_002():
    """start/endがどちらかないときNoneが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        result = get_pending_summary_confirm("user1")
        assert result is None


def test_set_pending_summary_confirm_001():
    """pendingConfirmStart/Endをセットするとput_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        set_pending_summary_confirm("user1", "2026-05-01", "2026-05-31")
        mock_table.put_item.assert_called_once()


def test_clear_pending_summary_confirm_001():
    """pendingConfirmStart/Endを削除するとdelete_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {
            "Item": {"pendingConfirmStart": "2026-05-01", "pendingConfirmEnd": "2026-05-31"}
        }
        clear_pending_summary_confirm("user1")
        mock_table.delete_item.assert_called_once()


# --- pendingExportStart ---

def test_get_pending_export_start_001():
    """pendingExportStartが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingExportStart": "2026-05-01"}}
        assert get_pending_export_start("user1") == "2026-05-01"


def test_set_pending_export_start_001():
    """pendingExportStartをセットするとput_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        set_pending_export_start("user1", "2026-05-01")
        mock_table.put_item.assert_called_once()


def test_clear_pending_export_start_001():
    """pendingExportStartを削除するとdelete_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingExportStart": "2026-05-01"}}
        clear_pending_export_start("user1")
        mock_table.delete_item.assert_called_once()


# --- pendingVital ---

def test_get_pending_vital_step_001():
    """pendingVitalStepが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingVitalStep": "temperature"}}
        assert get_pending_vital_step("user1") == "temperature"


def test_set_pending_vital_step_001():
    """pendingVitalStepをセットするとput_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        set_pending_vital_step("user1", "blood_pressure")
        mock_table.put_item.assert_called_once()


def test_get_pending_vital_data_001():
    """pendingVitalDataが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {"pendingVitalData": {"temperature": "36.5"}}}
        assert get_pending_vital_data("user1") == {"temperature": "36.5"}


def test_get_pending_vital_data_002():
    """pendingVitalDataがないとき空dictが返る"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        assert get_pending_vital_data("user1") == {}


def test_set_pending_vital_data_001():
    """pendingVitalDataをセットするとput_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {"Item": {}}
        set_pending_vital_data("user1", {"temperature": "36.5"})
        mock_table.put_item.assert_called_once()


def test_clear_pending_vital_001():
    """pendingVital系キーをすべて削除するとdelete_itemが呼ばれる"""
    with patch("services.record_store._table") as mock_table:
        mock_table.get_item.return_value = {
            "Item": {"pendingVitalStep": "pulse", "pendingVitalData": {"temperature": "36.5"}}
        }
        clear_pending_vital("user1")
        mock_table.delete_item.assert_called_once()
