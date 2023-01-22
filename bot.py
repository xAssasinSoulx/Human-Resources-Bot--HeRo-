from slackeventsapi import SlackEventAdapter
from slack_sdk.web import WebClient
import os, sqlite3
from flask import Flask,request,render_template

from datetime import datetime

from sentiment_analyzer import sample_analyze_sentiment

# This `app` represents your existing Flask app
app = Flask(__name__)


def create_db_tables(conn):
    if conn is not None:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS messages ( 
                                    channel_id text NOT NULL, 
                                    sender_id text NOT NULL, 
                                    name text NOT NULL, 
                                    ts text NOT NULL,
                                    sentiment integer NOT NULL
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
    c.execute("""INSERT INTO messages(channel_id, sender_id, name, ts, sentiment) 
            VALUES (?,?,?,?,?);""", (message['channel'], message['user'], message['text'], message['ts'], sample_analyze_sentiment(message['text'])))
    c.execute("COMMIT")

    # If the incoming message contains "hi", then respond with a "Hello" message
    if message.get("subtype") is None and "hi" in message.get('text'):
        channel = message["channel"]
        message = "Hello <@%s>! :tada:" % message["user"]
        slack_client.chat_postMessage(channel=channel, text=message)

# Error events
@slack_events_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))

@app.template_filter('ctime')
def timectime(s):
    return datetime.fromtimestamp(float(s)).strftime('%a, %B %d')

# An example of one of your Flask app's routes
@app.route("/")
def hello():
    members = slack_client.users_list()['members']
    return render_template('mainpage.html', members = members)

@app.route("/<member_id>")
def profile(member_id=0):
    # member = next(member for member in slack_client.users_list()['members'] if member['id'] == member_id)
    member = {}
    c.execute("""SELECT * from messages""")
    records = c.fetchall()

    member_records = [ record for record in records if record[1] == member_id ]

    critical_records = [ record for record in member_records if record[4] < -0.7 ]

    ###
    gevents = service.events().list(calendarId='primary', pageToken=os.environ["PAGE_TOKEN"]).execute()
    events = []
    for gevent in gevents[-5:]:
        event = {}
        event['title'] = gevent['title']
        event['date'] = gevent['date']
        if member['email'] in gevent['attendees']:
            event['attendance'] = 'Attended'
        else:
            event['attendance'] = 'Absent'
        events.push(event)

    return render_template('profile.html', member=member, critical_records = critical_records, events=events)

# Start the server on port 3000
if __name__ == "__main__":
  app.run(port=3000)