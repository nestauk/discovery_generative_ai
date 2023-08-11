import os
import random

from typing import List
from typing import Union

import pinecone
import streamlit as st

from genai.eyfs import ActivityGenerator
from genai.eyfs import get_embedding
from genai.utils import read_json


def eyfs_kb_bbc(index_name: str = "eyfs-index") -> None:
    """Run the EYFS + BBC activities app."""
    st.title("Generating activity plans grounded in EY foundation stages")
    areas_of_learning_desc = read_json("src/genai/eyfs/areas_of_learning.json")
    aol = list(areas_of_learning_desc.keys())
    index = get_index(index_name=index_name)

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

            # Search with Pinecone
            similar_docs = query_pinecone(
                index,
                encoded_query,
                areas_of_learning=areas_of_learning,
                top_n=4,
                max_n=4,
            )

        with st.spinner("Generating activities..."):
            res_box = st.empty()
            report = []
            # Create the prompt
            messages_placeholders = {
                "description": query,
                "areas_of_learning": areas_of_learning,
                "n_results": n_results,
                "location": location,
                "areas_of_learning_text": areas_of_learning_text,
                "activity_examples": "\n======\n".join(
                    [similar_doc["metadata"]["text"] for similar_doc in similar_docs]
                ),
            }

            r = ActivityGenerator.generate(
                model=selected_model,
                temperature=temperature,
                messages=messages,
                message_kwargs=messages_placeholders,
                stream=True,
            )

            for chunk in r:
                content = chunk["choices"][0].get("delta", {}).get("content")
                report.append(content)
                if chunk["choices"][0]["finish_reason"] != "stop":
                    result = "".join(report).strip()
                    res_box.markdown(f"{result}")
            # st.write(r["choices"][0]["message"]["content"])

        st.subheader("Sources")

        for similar_doc in similar_docs:
            title = similar_doc["metadata"]["title"]
            url = similar_doc["id"]
            category = similar_doc["metadata"]["areas_of_learning"]
            st.write(f"""- [{title}]({url}) {category}""")


@st.cache_resource
def get_index(index_name: str, environment: str = "us-west1-gcp") -> pinecone.index.Index:
    """Return and persist the pinecone index."""
    pinecone.init(api_key=os.environ["PINECONE_API_KEY"], environment=environment)
    index = pinecone.Index(index_name)
    return index


def sample_docs(num_docs: int, n: int) -> Union[List[int], ValueError]:
    """Sample docs (without replacement)."""
    try:
        return random.sample(range(num_docs), n)
    except ValueError:
        try:
            return random.sample(range(num_docs), num_docs)
        except ValueError as e:
            raise ValueError(f"Cannot sample docs: {e}")


def query_pinecone(
    index: pinecone.index.Index,
    encoded_query: list,
    areas_of_learning: list,
    top_n: int = 4,
    max_n: int = 4,
) -> list:
    """Query the pinecone index.

    Parameters
    ----------
    index
        Pinecone index.

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
    results = index.query(
        vector=encoded_query,
        top_k=top_n,
        include_metadata=True,
        filter={
            "areas_of_learning": {"$in": areas_of_learning},
        },
    )

    results = results["matches"]
    # Subset docs to fit the prompt length
    idx = sample_docs(len(results), max_n)

    return [results[i] for i in idx]
