import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS, SYSTEM_PROMPT

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generate(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """Claude APIを呼び出してテキストを返す。失敗時は anthropic.APIError を送出する。"""
    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
