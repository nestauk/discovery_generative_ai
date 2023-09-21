import os
import random

from typing import List
from typing import Optional
from typing import Union

import pinecone
import streamlit as st

from genai.vector_index import PineconeIndex


def reset_state(key: Optional[str] = None) -> None:
    """Delete the message placeholder state."""
    keys = [
        "similar_docs",
        "areas_of_learning_text",
        "areas_of_learning",
        "n_results",
        "location",
        "messages",
        "choice",
        "choices",
        "examples",
        "learning_goals",
        "full_response",
        "memory",
        "feedback",
        "user_feedback",
        "session_uuid",
    ]
    for key in keys:
        try:
            del st.session_state[key]
        except KeyError:
            pass


@st.cache_resource
def get_index(index_name: str, environment: str = "us-west1-gcp") -> pinecone.index.Index:
    """Return and persist the pinecone index."""
    conn = PineconeIndex(api_key=os.environ["PINECONE_API_KEY"], environment=environment)
    index = conn.connect(index_name=index_name)
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
    filters: dict,
    top_n: int = 5,
    max_n: int = 10,
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

    """
    results = index.query(
        vector=encoded_query,
        top_k=top_n,
        include_metadata=True,
        filter=filters,
    )

    return results["matches"]
