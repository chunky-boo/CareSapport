import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone, timedelta
from config import DYNAMODB_REGION, DYNAMODB_TABLE_NAME

_dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION)
_table = _dynamodb.Table(DYNAMODB_TABLE_NAME)

# SK値: 通常の記録はISO8601タイムスタンプ、ユーザー状態管理は"state"固定
_STATE_SK = "state"

_PERIOD_DELTAS = {
    "今日": lambda now: now.replace(hour=0, minute=0, second=0, microsecond=0),
    "今週": lambda now: now - timedelta(days=7),
    "今月": lambda now: now - timedelta(days=30),
}


def save_record(
    user_id: str,
    message: str,
    summary: str,
    category: str | None = None,
) -> None:
    item = {
        "userId": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
    return response.get("Items", [])


def get_pending_category(user_id: str) -> str | None:
    """カテゴリ選択後の次メッセージに使うカテゴリを取得する。"""
    response = _table.get_item(Key={"userId": user_id, "timestamp": _STATE_SK})
    item = response.get("Item")
    if not item:
        return None
    return item.get("pendingCategory")


def set_pending_category(user_id: str, category: str | None) -> None:
    """次の自由記述メッセージに紐付けるカテゴリを保存・クリアする。"""
    if category is None:
        _table.delete_item(Key={"userId": user_id, "timestamp": _STATE_SK})
    else:
        _table.put_item(
            Item={"userId": user_id, "timestamp": _STATE_SK, "pendingCategory": category}
        )
