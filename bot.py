from slackeventsapi import SlackEventAdapter
from slack_sdk.web import WebClient
import os, sqlite3
from flask import Flask

# This `app` represents your existing Flask app
app = Flask(__name__)

def create_db_tables(conn):
    if conn is not None:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS messages ( 
                                    channel_id text NOT NULL, 
                                    sender_id text NOT NULL, 
                                    name text NOT NULL, 
                                    ts text NOT NULL
                                );""")
    else:
        print("Error! cannot create the database connection.")

    return c

conn = sqlite3.connect('database.db', check_same_thread=False)

c = create_db_tables(conn)
 
# Initialize Slack WebClient and Event Adapter
slack_client = WebClient(os.environ["BOT_USER_ACCESS_TOKEN"])
slack_events_adapter = SlackEventAdapter(os.environ["SIGNING_SECRET"], "/slack/events", app)

# Send a message to indicate that bot is online
slack_client.chat_postMessage(channel="#general", text="Hello, I'm online now! :tada:")

# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):

    # Extract message from json response
    message = event_data["event"]

    # Log the sended message
    print("LOG: following message sent -> " + message['text'])

    # Insert message into messages table
    # if message['user'] is not slack_client.bots_info['bot']['id']:
    print(slack_client.bots_info(token=os.environ["BOT_USER_ACCESS_TOKEN"]))
    c.execute("""INSERT INTO messages(channel_id, sender_id, name, ts) 
            VALUES (?,?,?,?);""", (message['channel'], message['user'], message['text'], message['ts']))
    c.execute("COMMIT")

    # If the incoming message contains "hi", then respond with a "Hello" message
    if message.get("subtype") is None and "hi" in message.get('text'):
        channel = message["channel"]
        message = "Hello <@%s>! :tada:" % message["user"]
        slack_client.chat_postMessage(channel=channel, text=message)

    # If the incoming message contains "hi", then respond with a "Hello" message
    if message.get("subtype") is None and "employees" in message.get('text'):

        c.execute("""SELECT * from messages""")
        records = c.fetchall()

        
        channel = message["channel"]

        for col in records[-5:]:
            message = col[0] + " | <@" + col[1] + "> | " + col[2] + " | " + col[3] 
            slack_client.chat_postMessage(channel=channel, text=message)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))




# An example of one of your Flask app's routes
@app.route("/")
def hello():
  return "Hello there!"

# Start the server on port 3000
if __name__ == "__main__":
  app.run(port=3000)