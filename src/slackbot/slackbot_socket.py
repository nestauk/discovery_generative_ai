import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


# Listens to incoming messages that contain "hello"
@app.message("hello")
def message_hello(message, say):  # noqa: ANN001, ANN201
    """Send a message to the channel where the event was triggered"""
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Hey there <@{message['user']}>!"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Click Me"},
                    "action_id": "button_click",
                },
            }
        ],
        text=f"Hey there <@{message['user']}>!",
    )


@app.action("button_click")
def action_button_click(body, ack, say):  # noqa: ANN001, ANN201
    """Listen for button_click ation from message_hello"""
    # Acknowledge the action
    ack()
    say(f"<@{body['user']['id']}> clicked the button")


# @app.command("/nw_search")  # noqa: E302
# async def nw_search(ack, respond, command):  # noqa: ANN001, ANN201
#    """Slash command to search Nesta Way."""
#    await ack()
#    docs = await db.asimilarity_search(command["text"], top_k=4)
#    # can structure responses using markdown blocks
#    await respond(f"""Slash command received! {command['text']}\nResult:\n{docs}""")

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
