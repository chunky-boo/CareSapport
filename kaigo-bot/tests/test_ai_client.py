from unittest.mock import patch, MagicMock
from services.ai_client import generate


def test_generate_001():
    """正常系: AIの応答テキストが返る"""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="AIの応答")]
    with patch("services.ai_client._client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        result = generate("テストプロンプト")
        assert result == "AIの応答"


def test_generate_002():
    """カスタムsystemとmax_tokensが反映される"""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="カスタム応答")]
    with patch("services.ai_client._client") as mock_client:
        mock_client.messages.create.return_value = mock_response
        result = generate("プロンプト", system="カスタムシステム", max_tokens=100)
        assert result == "カスタム応答"
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "カスタムシステム"
        assert call_kwargs["max_tokens"] == 100
