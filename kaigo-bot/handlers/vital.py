from linebot.v3.messaging import TextMessage
from services.record_store import (
    get_pending_vital_step, set_pending_vital_step,
    get_pending_vital_data, set_pending_vital_data,
    clear_pending_vital, save_record,
)

_STEPS = ["temperature", "blood_pressure", "pulse"]

_PROMPTS = {
    "temperature":    "体温を入力してください。\n例：36.5\n（スキップ→「-」、キャンセル→「キャンセル」）",
    "blood_pressure": "血圧を入力してください。\n例：120/80\n（スキップ→「-」、キャンセル→「キャンセル」）",
    "pulse":          "脈拍を入力してください。\n例：72\n（スキップ→「-」、キャンセル→「キャンセル」）",
}

_LABELS = {
    "temperature":    "体温",
    "blood_pressure": "血圧",
    "pulse":          "脈拍",
}

_CANCEL_WORDS = {"キャンセル", "cancel", "やめる", "中止"}


def handle_vital_start(user_id: str) -> TextMessage:
    """バイタル入力フローを開始し、体温を質問する。"""
    set_pending_vital_step(user_id, "temperature")
    set_pending_vital_data(user_id, {})
    return TextMessage(text=_PROMPTS["temperature"])


def handle_vital_input(user_id: str, message: str) -> TextMessage | None:
    """バイタル入力中のメッセージを処理する。ステートがなければ None を返す。"""
    step = get_pending_vital_step(user_id)
    if step is None:
        return None

    if message in _CANCEL_WORDS:
        clear_pending_vital(user_id)
        return TextMessage(text="バイタル入力をキャンセルしました。")

    data = get_pending_vital_data(user_id)
    data[step] = None if message == "-" else message

    current_idx = _STEPS.index(step)
    if current_idx + 1 < len(_STEPS):
        next_step = _STEPS[current_idx + 1]
        set_pending_vital_step(user_id, next_step)
        set_pending_vital_data(user_id, data)
        return TextMessage(text=_PROMPTS[next_step])

    # 全ステップ完了
    clear_pending_vital(user_id)
    parts = [(k, v) for k, v in data.items() if v is not None]
    if not parts:
        return TextMessage(text="全項目スキップされたため、記録しませんでした。")

    raw_message = " ".join(f"{_LABELS[k]}:{v}" for k, v in parts)
    display = "\n".join(f"・{_LABELS[k]}: {v}" for k, v in parts)
    save_record(user_id, raw_message, raw_message, category="バイタル")
    return TextMessage(text=f"バイタルを記録しました！\n{display}")
