import os
from openai import OpenAI
from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)


client = OpenAI(
    base_url="http://localhost:1234/v1", # Launch the LM Studio application
    api_key="lm-studio"  # LM Studio does not require an API key
)


app = Flask(__name__)

# Initialize the configuration for the LINE Bot API using the access token from environment variables
configuration = Configuration(access_token = os.getenv('CHANNEL_ACCESS_TOKEN'))
# Create a webhook handler instance using the channel secret from environment variables
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


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
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# Get a response from the gpt-oss:20b model
history = [{"role": "system", "content": "你是一名用繁體中文教日文的老師，會用容易且好理解的方式讓學生理解。"},]

def get_llm_response(user_message):
    history.append({"role": "user", "content": user_message})
    result = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages = history,
        temperature=0.7,
    )
    history.append({"role": "assistant", "content": ""})
    return result.choices[0].message.content


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                #Return the AI's response
                messages=[TextMessage(text = get_llm_response(event.message.text))]
            )
        )

if __name__ == "__main__":
    app.run()
