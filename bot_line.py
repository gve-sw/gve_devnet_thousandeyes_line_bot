"""
Copyright (c) 2024 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""


import os
import sys
import json
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)

from dotenv import load_dotenv

load_dotenv()
user_ids = []

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)


def parse_alert(alert_body):
    alert_id = alert_body['alert']['id']
    alert_name = alert_body['alert']['test']['name']
    alert_domain = alert_body['alert']['targets']
    alert_rule = alert_body['alert']["rule"]["expression"]
    alert_details = len(alert_body["alert"]["details"])
    alert_message = "alert id: " + \
        str(alert_id) + "\nalert name: " + str(alert_name) + "\nalert domain: " + str(alert_domain) + \
        "\nalert rule: " + str(alert_rule) + \
        "\nalert details: " + str(alert_details)
    return alert_message


@app.route("/", methods=['POST'])
def verifyServer():
    # test webhook endpoint
    return 'OK'


@app.route("/te_alerts", methods=['POST'])
def receive_te_alerts():
    alert_body = request.get_json()
    alert_message = parse_alert(alert_body)
    print("received webhook from TE.")
    for user in user_ids:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(PushMessageRequest(
                to=str(user), messages=[TextMessage(text=alert_message)]))

    return 'OK'


@ app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print(body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@ handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(
                    text="you are now subscribed to ThousandEyes Alert")]
            )
        )
        user_ids.append(event.source.user_id)
        # line_bot_api.push_message(PushMessageRequest(
        #     to=event.source.user_id, messages=[TextMessage(text="TE Alerts")]))


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=5100, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(host='0.0.0.0', debug=options.debug, port=options.port, ssl_context=(
        os.environ.get("CERTIFICATE"), os.environ.get("PRIVATE_KEY")))
