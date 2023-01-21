from slackeventsapi import SlackEventAdapter
from slack_sdk.web import WebClient
import os
 
# Our app's Slack Event Adapter for receiving actions via the Events API
signing_secret = os.environ["SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(signing_secret, "/slack/events")

# Create a SlackClient for your bot to use for Web API requests
bot_user_access_token = os.environ["BOT_USER_ACCESS_TOKEN"]
slack_client = WebClient(bot_user_access_token)

# Send a message to show that bot is online
slack_client.chat_postMessage( channel="#general", text="Hello, I'm online now! :tada:")

# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]
    print(message['text'])
    # If the incoming message contains "hi", then respond with a "Hello" message
    if message.get("subtype") is None and "hi" in message.get('text'):
        channel = message["channel"]
        message = "Hello <@%s>! :tada:" % message["user"]
        slack_client.chat_postMessage(channel=channel, text=message)


# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))


# Start the slack event adapter on port 3000
slack_events_adapter.start(port=3000)