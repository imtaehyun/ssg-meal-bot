# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from firebase import firebase

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
firebase_url = os.getenv('FIREBASE_URL', None)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)
if firebase_url is None:
    print('Specify FIREBASE_URL as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

firebase = firebase.FirebaseApplication(firebase_url, None)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    print(event)

    msg = None
    if event.message.type == 'join':
        pass
    elif '메뉴' in event.message.text:
        date = event.message.text.replace('메뉴', '').strip()
        msg = get_menu_text(date)
    else:
        pass

    if msg:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=str(msg))
        )


def get_menu_text(date=None):
    if not date or len(date) != 8:
        now = datetime.today()
        date = now.strftime('%Y%m%d')

    result = firebase.get('/menus/' + date, None)

    if result:
        message = [date + ' 식당 메뉴\n']

        for key, value in result.items():
            message.append("[{}]".format(key))
            for menu in value:
                message.append(menu)
            message.append(" ")

        return "\n".join(message)
    else:
        return '등록된 메뉴가 없습니다.'


if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))

    app.run(host='0.0.0.0', port=port, debug=True)