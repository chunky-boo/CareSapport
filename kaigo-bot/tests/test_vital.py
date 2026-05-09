from unittest.mock import patch
from linebot.v3.messaging import TextMessage
from handlers.vital import handle_vital_start, handle_vital_input


# --- handle_vital_start ---

def test_handle_vital_start_001():
    """フロー開始で体温の質問が返り、ステートが設定される"""
    with patch("handlers.vital.set_pending_vital_step") as mock_step, \
         patch("handlers.vital.set_pending_vital_data") as mock_data:
        result = handle_vital_start("user1")
        assert isinstance(result, TextMessage)
        assert "体温" in result.text
        mock_step.assert_called_once_with("user1", "temperature")
        mock_data.assert_called_once_with("user1", {})


# --- handle_vital_input: ステートなし ---

def test_handle_vital_input_001():
    """バイタルステートがないときNoneが返る"""
    with patch("handlers.vital.get_pending_vital_step", return_value=None):
        result = handle_vital_input("user1", "36.5")
        assert result is None


# --- handle_vital_input: キャンセル ---

def test_handle_vital_input_002():
    """「キャンセル」でフローがキャンセルされる"""
    with patch("handlers.vital.get_pending_vital_step", return_value="temperature"), \
         patch("handlers.vital.clear_pending_vital") as mock_clear:
        result = handle_vital_input("user1", "キャンセル")
        assert isinstance(result, TextMessage)
        assert "キャンセル" in result.text
        mock_clear.assert_called_once_with("user1")


def test_handle_vital_input_003():
    """「やめる」でもキャンセルされる"""
    with patch("handlers.vital.get_pending_vital_step", return_value="temperature"), \
         patch("handlers.vital.clear_pending_vital"):
        result = handle_vital_input("user1", "やめる")
        assert isinstance(result, TextMessage)
        assert "キャンセル" in result.text


# --- handle_vital_input: 各ステップの遷移 ---

def test_handle_vital_input_004():
    """体温入力後に血圧の質問が返る"""
    with patch("handlers.vital.get_pending_vital_step", return_value="temperature"), \
         patch("handlers.vital.get_pending_vital_data", return_value={}), \
         patch("handlers.vital.set_pending_vital_step") as mock_step, \
         patch("handlers.vital.set_pending_vital_data") as mock_data:
        result = handle_vital_input("user1", "36.5")
        assert isinstance(result, TextMessage)
        assert "血圧" in result.text
        mock_step.assert_called_once_with("user1", "blood_pressure")
        mock_data.assert_called_once_with("user1", {"temperature": "36.5"})


def test_handle_vital_input_005():
    """血圧入力後に脈拍の質問が返る"""
    with patch("handlers.vital.get_pending_vital_step", return_value="blood_pressure"), \
         patch("handlers.vital.get_pending_vital_data", return_value={"temperature": "36.5"}), \
         patch("handlers.vital.set_pending_vital_step") as mock_step, \
         patch("handlers.vital.set_pending_vital_data"):
        result = handle_vital_input("user1", "120/80")
        assert isinstance(result, TextMessage)
        assert "脈拍" in result.text
        mock_step.assert_called_once_with("user1", "pulse")


# --- handle_vital_input: 最終ステップ（記録） ---

def test_handle_vital_input_006():
    """脈拍入力後に記録完了メッセージが返る"""
    with patch("handlers.vital.get_pending_vital_step", return_value="pulse"), \
         patch("handlers.vital.get_pending_vital_data", return_value={"temperature": "36.5", "blood_pressure": "120/80"}), \
         patch("handlers.vital.clear_pending_vital"), \
         patch("handlers.vital.save_record") as mock_save:
        result = handle_vital_input("user1", "72")
        assert isinstance(result, TextMessage)
        assert "記録しました" in result.text
        assert "体温" in result.text
        assert "血圧" in result.text
        assert "脈拍" in result.text
        mock_save.assert_called_once()
        call_kwargs = mock_save.call_args
        assert call_kwargs[1]["category"] == "バイタル"


# --- handle_vital_input: スキップ（「-」） ---

def test_handle_vital_input_007():
    """「-」でスキップして次のステップに進む"""
    with patch("handlers.vital.get_pending_vital_step", return_value="temperature"), \
         patch("handlers.vital.get_pending_vital_data", return_value={}), \
         patch("handlers.vital.set_pending_vital_step"), \
         patch("handlers.vital.set_pending_vital_data") as mock_data:
        result = handle_vital_input("user1", "-")
        assert isinstance(result, TextMessage)
        assert "血圧" in result.text
        saved_data = mock_data.call_args[0][1]
        assert saved_data["temperature"] is None


def test_handle_vital_input_008():
    """全項目スキップのとき「記録しませんでした」が返る"""
    with patch("handlers.vital.get_pending_vital_step", return_value="pulse"), \
         patch("handlers.vital.get_pending_vital_data", return_value={"temperature": None, "blood_pressure": None}), \
         patch("handlers.vital.clear_pending_vital"), \
         patch("handlers.vital.save_record") as mock_save:
        result = handle_vital_input("user1", "-")
        assert isinstance(result, TextMessage)
        assert "スキップ" in result.text
        mock_save.assert_not_called()
