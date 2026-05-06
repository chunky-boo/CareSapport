import ssl
import certifi
ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent
import config
from handlers.router import route
from handlers.postback import handle_postback

configuration = Configuration(access_token=config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    if config.MAINTENANCE_MODE:
        reply = TextMessage(text=config.MAINTENANCE_MESSAGE)
    else:
        reply = route(event.source.user_id, event.message.text)
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=event.reply_token, messages=[reply])
        )


@handler.add(PostbackEvent)
def handle_postback_event(event):
    if config.MAINTENANCE_MODE:
        reply = TextMessage(text=config.MAINTENANCE_MESSAGE)
    else:
        reply = handle_postback(
            event.source.user_id,
            event.postback.data,
            event.postback.params,
        )
    if reply:
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(reply_token=event.reply_token, messages=[reply])
            )


def lambda_handler(event, context):
    signature = event["headers"].get("x-line-signature", "")
    try:
        handler.handle(event["body"], signature)
    except InvalidSignatureError:
        return {"statusCode": 400, "body": "Invalid signature"}
    return {"statusCode": 200, "body": "OK"}
