import os

from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatLiteLLM
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores.qdrant import Qdrant
from qdrant_client import QdrantClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


load_dotenv()


# Initiate embeddings and qdrant client
model_kwargs = {"device": "cpu"}  # unchanged
encode_kwargs = {"normalize_embeddings": False}  # unchanged

hf_bge_base = HuggingFaceBgeEmbeddings(
    model_name="BAAI/bge-base-en-v1.5", model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)

client = QdrantClient(
    url=os.environ.get("QDRANT_URL"),
    api_key=os.environ.get("QDRANT_API_KEY"),
    prefer_grpc=True,
)

db = Qdrant(
    client=client,
    embeddings=hf_bge_base,
    collection_name=os.environ.get("QDRANT_COLLECTION_NAME"),
)

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


@app.command("/nw_search")  # noqa: E302
def nw_search(ack, respond, command):  # noqa: ANN001, ANN201
    """Slash command to search Nesta Way."""
    ack()
    docs = db.similarity_search_with_score(command["text"], k=3)
    # can structure responses using markdown blocks
    respond(f"""Searched the Nesta Way for: {command['text']}\nResult(s):\n{docs}""")


@app.command("/nw_ask")  # noqa: E302
def nw_ask(ack, respond, command):  # noqa: ANN001, ANN201
    """Slash command to RAG the Nesta Way."""
    # TODO: Handle offline LLM
    ack()

    llm = ChatLiteLLM(
        model_name="gpt-3.5-turbo",
        max_tokens=2000,
    )

    qa_with_sources = RetrievalQA.from_chain_type(llm=llm, retriever=db.as_retriever(), return_source_documents=True)

    res = qa_with_sources({"query": command["text"]})

    respond(f"""You asked: {res['query']}\n\nAnswer:\n{res['result']}\n\nSources:\n{res['source_documents']}""")


@app.command("/test_command")
def test_command(ack, respond, command):  # noqa: ANN001, ANN201
    """Slash command to test Slack Bolt."""
    ack()
    respond(f"test command received body: {command['text']}")


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
