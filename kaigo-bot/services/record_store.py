import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone, timedelta
from config import DYNAMODB_REGION, DYNAMODB_TABLE_NAME

_dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION)
_table = _dynamodb.Table(DYNAMODB_TABLE_NAME)

_STATE_SK = "state"
_STATE_TTL_HOURS = 2
_JST = timezone(timedelta(hours=9))

_PERIOD_DELTAS = {
    # JST 0:00 を UTC に変換してから比較。UTC midnight だと 09:00 JST 以降しか拾えない
    "今日": lambda now: now.astimezone(_JST).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc),
    "今週": lambda now: now - timedelta(days=7),
    "今月": lambda now: now - timedelta(days=30),
}


def save_record(
    user_id: str,
    message: str,
    summary: str,
    category: str | None = None,
    timestamp: str | None = None,
) -> None:
    item = {
        "userId": user_id,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "rawMessage": message,
        "summary": summary,
    }
    if category:
        item["category"] = category
    _table.put_item(Item=item)


def get_records_by_period(user_id: str, period: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    since_fn = _PERIOD_DELTAS.get(period, _PERIOD_DELTAS["今週"])
    since = since_fn(now)
    response = _table.query(
        KeyConditionExpression=Key("userId").eq(user_id)
        & Key("timestamp").gte(since.isoformat())
    )
    return [r for r in response.get("Items", []) if "rawMessage" in r]


def get_records_since(user_id: str, days: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    response = _table.query(
        KeyConditionExpression=Key("userId").eq(user_id)
        & Key("timestamp").gte(since.isoformat())
    )
    return [r for r in response.get("Items", []) if "rawMessage" in r]


def get_records_by_date_range(user_id: str, start_date: str, end_date: str) -> list[dict]:
    jst = timezone(timedelta(hours=9))
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=jst)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=jst)
    response = _table.query(
        KeyConditionExpression=Key("userId").eq(user_id)
        & Key("timestamp").between(
            start_dt.astimezone(timezone.utc).isoformat(),
            end_dt.astimezone(timezone.utc).isoformat(),
        )
    )
    return [r for r in response.get("Items", []) if "rawMessage" in r]


# --- ステート管理（pendingCategory / pendingDate） ---

def _get_state(user_id: str) -> dict:
    response = _table.get_item(Key={"userId": user_id, "timestamp": _STATE_SK})
    item = response.get("Item") or {}
    return {k: v for k, v in item.items() if k not in ("userId", "timestamp", "ttl")}


def _save_state(user_id: str, state: dict) -> None:
    if not state:
        _table.delete_item(Key={"userId": user_id, "timestamp": _STATE_SK})
        return
    ttl = int((datetime.now(timezone.utc) + timedelta(hours=_STATE_TTL_HOURS)).timestamp())
    _table.put_item(Item={"userId": user_id, "timestamp": _STATE_SK, "ttl": ttl, **state})


def get_pending_category(user_id: str) -> str | None:
    return _get_state(user_id).get("pendingCategory")


def set_pending_category(user_id: str, category: str | None) -> None:
    state = _get_state(user_id)
    if category is None:
        state.pop("pendingCategory", None)
    else:
        state["pendingCategory"] = category
    _save_state(user_id, state)


def get_pending_date(user_id: str) -> str | None:
    return _get_state(user_id).get("pendingDate")


def set_pending_date(user_id: str, date: str | None) -> None:
    state = _get_state(user_id)
    if date is None:
        state.pop("pendingDate", None)
    else:
        state["pendingDate"] = date
    _save_state(user_id, state)


def clear_pending_state(user_id: str) -> None:
    _table.delete_item(Key={"userId": user_id, "timestamp": _STATE_SK})


def get_pending_summary_start(user_id: str) -> str | None:
    return _get_state(user_id).get("pendingSummaryStart")


def set_pending_summary_start(user_id: str, date: str) -> None:
    state = _get_state(user_id)
    state["pendingSummaryStart"] = date
    _save_state(user_id, state)


def clear_pending_summary_start(user_id: str) -> None:
    state = _get_state(user_id)
    state.pop("pendingSummaryStart", None)
    _save_state(user_id, state)


def get_pending_summary_confirm(user_id: str) -> tuple[str, str] | None:
    state = _get_state(user_id)
    start = state.get("pendingConfirmStart")
    end = state.get("pendingConfirmEnd")
    if start and end:
        return start, end
    return None


def set_pending_summary_confirm(user_id: str, start_date: str, end_date: str) -> None:
    state = _get_state(user_id)
    state["pendingConfirmStart"] = start_date
    state["pendingConfirmEnd"] = end_date
    _save_state(user_id, state)


def clear_pending_summary_confirm(user_id: str) -> None:
    state = _get_state(user_id)
    state.pop("pendingConfirmStart", None)
    state.pop("pendingConfirmEnd", None)
    _save_state(user_id, state)


def get_pending_export_start(user_id: str) -> str | None:
    return _get_state(user_id).get("pendingExportStart")


def set_pending_export_start(user_id: str, date: str) -> None:
    state = _get_state(user_id)
    state["pendingExportStart"] = date
    _save_state(user_id, state)


def clear_pending_export_start(user_id: str) -> None:
    state = _get_state(user_id)
    state.pop("pendingExportStart", None)
    _save_state(user_id, state)


# --- バイタル入力フロー ---

def get_pending_vital_step(user_id: str) -> str | None:
    return _get_state(user_id).get("pendingVitalStep")


def set_pending_vital_step(user_id: str, step: str) -> None:
    state = _get_state(user_id)
    state["pendingVitalStep"] = step
    _save_state(user_id, state)


def get_pending_vital_data(user_id: str) -> dict:
    return _get_state(user_id).get("pendingVitalData") or {}


def set_pending_vital_data(user_id: str, data: dict) -> None:
    state = _get_state(user_id)
    state["pendingVitalData"] = data
    _save_state(user_id, state)


def clear_pending_vital(user_id: str) -> None:
    state = _get_state(user_id)
    state.pop("pendingVitalStep", None)
    state.pop("pendingVitalData", None)
    _save_state(user_id, state)
