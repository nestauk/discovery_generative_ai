import os

from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient  # noqa: F401
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp


# Initiate qdrant client and embeddings
model_kwargs = {"device": "cpu"}  # unchanged
encode_kwargs = {"normalize_embeddings": False}  # unchanged

hf_bge_base = HuggingFaceBgeEmbeddings(
    model_name="BAAI/bge-base-en", model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)

client = QdrantClient(
    url="http://localhost:6334",
    prefer_grpc=True,
)

db = Qdrant(
    client=client,
    embeddings=hf_bge_base,
    collection_name="nesta_way_bge-base-en",
)
# (
#    client=QdrantClient(url="http://localhost:6334", prefer_grpc=True),
#    collection_name="nesta_way_bge-base-en",
#    embeddings=hf_bge_base,
# )


# Initializes your app with your bot token and socket mode handler
app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))


# Listens to incoming messages that contain "hello"
@app.message("hello")
async def message_hello(message, say):  # noqa: ANN001, ANN201
    """Send a message to the channel where the event was triggered"""
    await say(
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
async def action_button_click(body, ack, say):  # noqa: ANN001, ANN201
    """Listen for button_click ation from message_hello"""
    # Acknowledge the action
    await ack()
    await say(f"<@{body['user']['id']}> clicked the button")


@app.command("/nw_search")  # noqa: E302
async def nw_search(ack, respond, command):  # noqa: ANN001, ANN201
    """Slash command to search Nesta Way."""
    await ack()
    docs = await db.asimilarity_search_with_score(command["text"], k=3)
    # can structure responses using markdown blocks
    await respond(f"""Slash command received! {command['text']}\nResult(s):\n{docs}""")


@app.command("/test_command")
async def test_command(ack, respond, command):  # noqa: ANN001, ANN201
    """Slash command to test Slack Bolt."""
    await ack()
    await respond(f"test command received body: {command['text']}")


async def main():  # noqa: ANN001, ANN201
    """App entry point."""
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


# Start your app
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
