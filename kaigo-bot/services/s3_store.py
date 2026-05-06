import io
import csv
import boto3
from datetime import datetime, timezone, timedelta
from config import DYNAMODB_REGION, S3_BUCKET_NAME, S3_PRESIGNED_URL_EXPIRY

_s3 = boto3.client("s3", region_name=DYNAMODB_REGION)
_JST = timezone(timedelta(hours=9))


def upload_csv_and_get_url(user_id: str, records: list[dict], start_date: str, end_date: str) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日付", "時刻", "カテゴリ", "記録内容"])

    for r in records:
        ts = datetime.fromisoformat(r["timestamp"]).astimezone(_JST)
        writer.writerow([
            ts.strftime("%Y-%m-%d"),
            ts.strftime("%H:%M"),
            r.get("category", ""),
            r.get("rawMessage", ""),
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM付きでExcelでも文字化けしない
    key = f"exports/{user_id}/care_records_{start_date}_{end_date}.csv"

    _s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=csv_bytes,
        ContentType="text/csv; charset=utf-8",
    )

    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": key},
        ExpiresIn=S3_PRESIGNED_URL_EXPIRY,
    )
