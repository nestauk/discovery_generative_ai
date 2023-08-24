import os

from typing import Dict

from fastapi import FastAPI
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.app.async_app import AsyncApp


# Create an instance of AsyncApp and FastAPI
bolt = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))
app = FastAPI()

# Initiate qdrant client and embeddings
model_kwargs = {"device": "cpu"}  # unchanged
encode_kwargs = {"normalize_embeddings": False}  # unchanged

hf_bge_base = HuggingFaceBgeEmbeddings(
    model_name="BAAI/bge-base-en", model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)

db = Qdrant(
    client=QdrantClient(url="http://localhost:6334", prefer_grpc=True),
    collection_name="nesta_way_bge-base-en",
    embeddings=hf_bge_base,
)


# Define FastAPI endpoints
@app.get("/")  # noqa: E302
async def root() -> Dict[str, str]:
    """Root endpoint for FastAPI."""
    return {"message": "Hello, World!"}


# Create an instance of AsyncSlackRequestHandler and add it as a route to FastAPI
handler = AsyncSlackRequestHandler(bolt)
app.add_route("/slack/events", handler, methods=["POST"])


# Define Slash command
@bolt.command("/nw_search")  # noqa: E302
async def nw_search(ack, respond, command):  # noqa: ANN001, ANN201
    """Slash command to search Nesta Way."""
    await ack()
    docs = await db.asimilarity_search(command["text"], top_k=4)
    # can structure responses using markdown blocks
    await respond(f"""Slash command received! {command['text']}\nResult:\n{docs}""")


# Include FastAPI app in the main script
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("serve_vdb:app", host="0.0.0.0", port=8000)
