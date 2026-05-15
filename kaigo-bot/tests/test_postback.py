from unittest.mock import patch, MagicMock
from linebot.v3.messaging import TextMessage
from handlers.postback import handle_postback


def _params(**kwargs):
    """PostbackEventParams の代替として属性付きオブジェクトを返す"""
    m = MagicMock()
    for k, v in kwargs.items():
        setattr(m, k, v)
    return m


# --- action=select_date ---

def test_handle_postback_001():
    """select_date: datetimeなしのときNoneが返る"""
    params = _params(datetime=None)
    result = handle_postback("user1", "action=select_date", params)
    assert result is None


def test_handle_postback_002():
    """select_date: datetime指定でカテゴリ選択Quick Replyが返る"""
    with patch("handlers.postback.set_pending_date"):
        params = _params(datetime="2026-05-01T09:00")
        result = handle_postback("user1", "action=select_date", params)
        assert isinstance(result, TextMessage)
        assert "5月1日" in result.text
        assert "09:00" in result.text


# --- action=summary_start_date ---

def test_handle_postback_003():
    """summary_start_date: dateなしのときNoneが返る"""
    params = _params(date=None)
    result = handle_postback("user1", "action=summary_start_date", params)
    assert result is None


def test_handle_postback_004():
    """summary_start_date: date指定で年月日入りの終了日選択Quick Replyが返る"""
    with patch("handlers.postback.set_pending_summary_start"):
        params = _params(date="2026-05-01")
        result = handle_postback("user1", "action=summary_start_date", params)
        assert isinstance(result, TextMessage)
        assert "2026年5月1日" in result.text
        assert "いつまで" in result.text


# --- action=summary_end_date ---

def test_handle_postback_005():
    """summary_end_date: dateなしのときNoneが返る"""
    params = _params(date=None)
    result = handle_postback("user1", "action=summary_end_date", params)
    assert result is None


def test_handle_postback_006():
    """summary_end_date: 開始日がタイムアウトしていた場合にエラーメッセージが返る"""
    with patch("handlers.postback.get_pending_summary_start", return_value=None):
        params = _params(date="2026-05-31")
        result = handle_postback("user1", "action=summary_end_date", params)
        assert isinstance(result, TextMessage)
        assert "タイムアウト" in result.text


def test_handle_postback_007():
    """summary_end_date: 終了日が開始日より前のときエラーメッセージが返る"""
    with patch("handlers.postback.get_pending_summary_start", return_value="2026-05-31"), \
         patch("handlers.postback.clear_pending_summary_start"):
        params = _params(date="2026-05-01")
        result = handle_postback("user1", "action=summary_end_date", params)
        assert isinstance(result, TextMessage)
        assert "開始日" in result.text


def test_handle_postback_008():
    """summary_end_date: 365日超のときキャップして確認ダイアログが返る"""
    with patch("handlers.postback.get_pending_summary_start", return_value="2024-01-01"), \
         patch("handlers.postback.clear_pending_summary_start"), \
         patch("handlers.postback.set_pending_summary_confirm"):
        params = _params(date="2026-01-02")
        result = handle_postback("user1", "action=summary_end_date", params)
        assert isinstance(result, TextMessage)
        assert "1年を超えている" in result.text


def test_handle_postback_009():
    """summary_end_date: 365日以内のとき確認ダイアログが返る"""
    with patch("handlers.postback.get_pending_summary_start", return_value="2026-05-01"), \
         patch("handlers.postback.clear_pending_summary_start"), \
         patch("handlers.postback.set_pending_summary_confirm"):
        params = _params(date="2026-05-31")
        result = handle_postback("user1", "action=summary_end_date", params)
        assert isinstance(result, TextMessage)
        assert "よろしいですか" in result.text
        assert result.quick_reply is not None


# --- action=export_start_date ---

def test_handle_postback_010():
    """export_start_date: dateなしのときNoneが返る"""
    params = _params(date=None)
    result = handle_postback("user1", "action=export_start_date", params)
    assert result is None


def test_handle_postback_011():
    """export_start_date: date指定で終了日選択Quick Replyが返る"""
    with patch("handlers.postback.set_pending_export_start"):
        params = _params(date="2026-05-01")
        result = handle_postback("user1", "action=export_start_date", params)
        assert isinstance(result, TextMessage)
        assert "いつまで" in result.text


# --- action=export_end_date ---

def test_handle_postback_012():
    """export_end_date: dateなしのときNoneが返る"""
    params = _params(date=None)
    result = handle_postback("user1", "action=export_end_date", params)
    assert result is None


def test_handle_postback_013():
    """export_end_date: 開始日がタイムアウトしていた場合にエラーメッセージが返る"""
    with patch("handlers.postback.get_pending_export_start", return_value=None):
        params = _params(date="2026-05-31")
        result = handle_postback("user1", "action=export_end_date", params)
        assert isinstance(result, TextMessage)
        assert "タイムアウト" in result.text


def test_handle_postback_014():
    """export_end_date: 終了日が開始日より前のときエラーメッセージが返る"""
    with patch("handlers.postback.get_pending_export_start", return_value="2026-05-31"), \
         patch("handlers.postback.clear_pending_export_start"):
        params = _params(date="2026-05-01")
        result = handle_postback("user1", "action=export_end_date", params)
        assert isinstance(result, TextMessage)
        assert "開始日" in result.text


def test_handle_postback_015():
    """export_end_date: 正常な期間でCSVエクスポートが実行される"""
    with patch("handlers.postback.get_pending_export_start", return_value="2026-05-01"), \
         patch("handlers.postback.clear_pending_export_start"), \
         patch("handlers.postback.handle_export", return_value=TextMessage(text="CSV完了")):
        params = _params(date="2026-05-31")
        result = handle_postback("user1", "action=export_end_date", params)
        assert isinstance(result, TextMessage)
        assert result.text == "CSV完了"


# --- action=search_date ---

def test_handle_postback_016():
    """search_date: dateなしのときNoneが返る"""
    params = _params(date=None)
    result = handle_postback("user1", "action=search_date", params)
    assert result is None


def test_handle_postback_017():
    """search_date: date指定で検索結果が返る"""
    with patch("handlers.postback.handle_search", return_value=TextMessage(text="検索結果")):
        params = _params(date="2026-05-01")
        result = handle_postback("user1", "action=search_date", params)
        assert isinstance(result, TextMessage)
        assert result.text == "検索結果"


# --- 未知のaction ---

def test_handle_postback_018():
    """未知のactionのときNoneが返る"""
    params = _params()
    result = handle_postback("user1", "action=unknown", params)
    assert result is None
