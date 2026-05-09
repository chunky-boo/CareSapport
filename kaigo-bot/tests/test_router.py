from unittest.mock import patch, MagicMock
from linebot.v3.messaging import TextMessage
from handlers.router import route, _dispatch, _fuzzy_match

_DUMMY_REPLY = TextMessage(text="dummy")


def test_route_001():
    """Phase 0: 確認応答がヒットした場合にその返答が返る"""
    with patch("handlers.router.handle_summary_confirm", return_value=_DUMMY_REPLY):
        result = route("user1", "はい")
        assert result.text == "dummy"


def test_route_002():
    """Phase 1: 完全一致ハンドラがヒットした場合にその返答が返る"""
    with patch("handlers.router.handle_summary_confirm", return_value=None), \
         patch("handlers.router.handle_vital_input", return_value=None), \
         patch("handlers.router.handle_top_menu", return_value=_DUMMY_REPLY):
        result = route("user1", "記録")
        assert result.text == "dummy"


def test_route_003():
    """Phase 2: 部分一致ハンドラがヒットした場合にその返答が返る"""
    with patch("handlers.router.handle_summary_confirm", return_value=None), \
         patch("handlers.router.handle_vital_input", return_value=None), \
         patch("handlers.router.handle_top_menu", return_value=None), \
         patch("handlers.router.handle_record_prompt", return_value=None), \
         patch("handlers.router.handle_summary", return_value=None), \
         patch("handlers.router.handle_consult", return_value=None), \
         patch("handlers.router.handle_free_record", return_value=_DUMMY_REPLY) as mock_free:
        with patch("handlers.router._fuzzy_match", return_value=_DUMMY_REPLY):
            result = route("user1", "今週どうだった？")
            assert result.text == "dummy"


def test_route_004():
    """Phase 3: すべてのフェーズがミスした場合に自由記述フォールバックが返る"""
    with patch("handlers.router.handle_summary_confirm", return_value=None), \
         patch("handlers.router.handle_vital_input", return_value=None), \
         patch("handlers.router._dispatch", return_value=None), \
         patch("handlers.router._fuzzy_match", return_value=None), \
         patch("handlers.router.handle_free_record", return_value=_DUMMY_REPLY):
        result = route("user1", "お母さん今日元気だった")
        assert result.text == "dummy"


def test_route_005():
    """Phase 0.5: バイタル入力中にhandle_vital_inputがヒットした場合にその返答が返る"""
    with patch("handlers.router.handle_summary_confirm", return_value=None), \
         patch("handlers.router.handle_vital_input", return_value=_DUMMY_REPLY):
        result = route("user1", "36.5")
        assert result.text == "dummy"


def test_dispatch_001():
    """handle_top_menuがヒットした場合にその返答が返る"""
    with patch("handlers.router.handle_top_menu", return_value=_DUMMY_REPLY):
        result = _dispatch("user1", "記録")
        assert result.text == "dummy"


def test_dispatch_002():
    """handle_record_promptがヒットした場合にカテゴリを保存して返答が返る"""
    with patch("handlers.router.handle_top_menu", return_value=None), \
         patch("handlers.router.handle_record_prompt", return_value=_DUMMY_REPLY), \
         patch("handlers.router.set_pending_category") as mock_set_cat:
        result = _dispatch("user1", "体調を記録")
        assert result.text == "dummy"
        mock_set_cat.assert_called_once_with("user1", "体調")


def test_dispatch_003():
    """handle_summaryがヒットした場合にその返答が返る"""
    with patch("handlers.router.handle_top_menu", return_value=None), \
         patch("handlers.router.handle_record_prompt", return_value=None), \
         patch("handlers.router.handle_summary", return_value=_DUMMY_REPLY):
        result = _dispatch("user1", "今日のまとめ")
        assert result.text == "dummy"


def test_dispatch_004():
    """handle_consultがヒットした場合にその返答が返る"""
    with patch("handlers.router.handle_top_menu", return_value=None), \
         patch("handlers.router.handle_record_prompt", return_value=None), \
         patch("handlers.router.handle_summary", return_value=None), \
         patch("handlers.router.handle_consult", return_value=_DUMMY_REPLY):
        result = _dispatch("user1", "相談文（2週間）")
        assert result.text == "dummy"


def test_dispatch_005():
    """すべてのハンドラがミスした場合にNoneが返る"""
    with patch("handlers.router.handle_top_menu", return_value=None), \
         patch("handlers.router.handle_record_prompt", return_value=None), \
         patch("handlers.router.handle_summary", return_value=None), \
         patch("handlers.router.handle_consult", return_value=None):
        result = _dispatch("user1", "unknown")
        assert result is None


def test_dispatch_006():
    """「バイタルを記録」でhandle_vital_startが呼ばれる"""
    with patch("handlers.router.handle_top_menu", return_value=None), \
         patch("handlers.router.handle_vital_start", return_value=_DUMMY_REPLY):
        result = _dispatch("user1", "バイタルを記録")
        assert result.text == "dummy"


def test_fuzzy_match_001():
    """期間キーワード+サマリー意図キーワードで期間サマリーにディスパッチされる"""
    with patch("handlers.router.handle_top_menu", return_value=None), \
         patch("handlers.router.handle_record_prompt", return_value=None), \
         patch("handlers.router.handle_summary", return_value=_DUMMY_REPLY):
        result = _fuzzy_match("user1", "今週どうだった？")
        assert result is not None


def test_fuzzy_match_002():
    """トップメニューキーワードゆれで正規キーワードにディスパッチされる"""
    with patch("handlers.router.handle_top_menu", return_value=_DUMMY_REPLY):
        result = _fuzzy_match("user1", "きろく")
        assert result is not None


def test_fuzzy_match_003():
    """どのキーワードにも一致しない場合にNoneが返る"""
    result = _fuzzy_match("user1", "xyzxyzxyz")
    assert result is None
