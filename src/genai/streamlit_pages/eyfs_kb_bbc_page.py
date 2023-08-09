import random

from typing import Union

import chromadb
import streamlit as st

from chromadb.api.models.Collection import Collection

from genai.eyfs import ActivityGenerator
from genai.eyfs import get_embedding
from genai.utils import read_json


def eyfs_kb_bbc(path: str = "data/eyfs/chroma_index/") -> None:
    """Run the EYFS + BBC activities app."""
    st.title("Generating activity plans grounded in EY foundation stages")
    areas_of_learning_desc = read_json("src/genai/eyfs/areas_of_learning.json")
    aol = list(areas_of_learning_desc.keys())
    collection = get_collection(path=path, index_name="eyfs_chroma_index")

    with st.sidebar:
        # Select a model, temperature and number of results
        selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"], index=1)
        # query = "<THIS IS WHERE THE GENERATOR WILL SHOW THE RESULTS>"
        n_results = 10
        temperature = st.slider(label="**Temperature**", min_value=0.0, max_value=2.0, value=0.6, step=0.1)

    # Select the areas of learning
    areas_of_learning = st.multiselect(label="**Areas of learning**", options=aol, default=aol)
    areas_of_learning_text = [v for k, v in areas_of_learning_desc.items() if k in areas_of_learning]

    # Describe each Area of Learning in an expanding window
    with st.expander("**Areas of Learning Description**"):
        for k, v in areas_of_learning_desc.items():
            if k in areas_of_learning:
                st.write(f"#### {k}")
                st.write(v.split("##")[-1])

    areas_of_learning_text = "\n\n".join(areas_of_learning_text)
    location = st.selectbox(label="**Location**", options=["Indoor", "Outdoor", "Indoor or Outdoor"], index=2)

    # Create the messages
    paths = [
        "src/genai/eyfs/prompts/system.json",
        "src/genai/eyfs/prompts/context_and_task_with_examples.json",
        "src/genai/eyfs/prompts/constraints.json",
        "src/genai/eyfs/prompts/situation.json",
    ]

    messages = [read_json(path) for path in paths]

    # Get the user input
    query = st.text_input(
        label="**What's the topic you want activities for?**",
        value="Let's create activities educating children on how whales breath",
        help="Prompt the large language model with a some text and it will generate an activity plan for you.",
    )

    if st.button(label="**Generate**", help="Generate an answer."):
        with st.spinner("Searching for relevant BBC activities..."):
            # Encode the query
            encoded_query = get_embedding(query)

            # Search with Chroma
            docs, urls, categories = query_chroma(
                collection,
                encoded_query,
                areas_of_learning=areas_of_learning,
                top_n=4,
                max_n=4,
            )

        with st.spinner("Generating activities..."):
            # Create the prompt
            messages_placeholders = {
                "description": query,
                "areas_of_learning": areas_of_learning,
                "n_results": n_results,
                "location": location,
                "areas_of_learning_text": areas_of_learning_text,
                "activity_examples": "\n======\n".join(docs),
            }

            r = ActivityGenerator.generate(
                model=selected_model,
                temperature=temperature,
                messages=messages,
                message_kwargs=messages_placeholders,
            )

            st.write(r)

            st.subheader("Sources")

            for url, doc, category in zip(urls, docs, categories):
                st.write(f"""**URL**: {url}\n\n**Text**: {doc}\n\n**Area of learning**: {category}\n\n====\n\n""")


@st.cache_resource
def get_collection(path: str, index_name: str) -> Collection:
    """Return and persist the chroma db collection."""
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(name=index_name)
    return collection


def try_sample_docs(num_docs: int, n: int) -> Union[list, ValueError]:
    """Sample docs (without replacement)."""
    try:
        return random.sample(range(num_docs), n)
    except ValueError as e:
        return e


def sample_docs(num_docs: int, n: int) -> Union[list, ValueError]:
    """Sample docs (without replacement)."""
    idx = try_sample_docs(num_docs, n)
    if isinstance(idx, ValueError):
        idx = sample_docs(num_docs, num_docs)
        if isinstance(idx, ValueError):
            raise ValueError(f"Cannot sample docs: {idx}")
    return idx


def query_chroma(
    collection: Collection,
    encoded_query: list,
    areas_of_learning: list,
    top_n: int = 4,
    max_n: int = 4,
) -> tuple:
    """Query the chroma db collection.

    Parameters
    ----------
    collection
        Chroma db index.

    query
        Query vector to search for.

    areas_of_learning
        Areas of learning to filter by.

    top_n
        Number of results to return.

    max_n
        Maximum number of results to keep as prompt examples.

    Returns
    -------
    docs
        List of documents.

    urls
        List of urls.

    """
    encoded_query = get_embedding("sing a song")

    docs = []
    urls = []
    aol = []
    for area_of_learning in areas_of_learning:
        r = collection.query(encoded_query, n_results=top_n, where={"area_of_learning": area_of_learning})
        urls.extend(r["ids"][0])
        docs.extend(r["documents"][0])
        aol.extend([v["area_of_learning"] for v in r["metadatas"][0]])

    # Subset docs to fit the prompt length
    idx = sample_docs(len(docs), max_n)

    docs = [docs[i] for i in idx]
    urls = [urls[i] for i in idx]
    aol = [aol[i] for i in idx]

    return docs, urls, aol
