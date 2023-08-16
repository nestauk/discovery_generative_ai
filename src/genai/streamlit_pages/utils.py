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
    keys = ["areas_of_learning_text", "areas_of_learning", "n_results", "location", "messages", "choice", "choices"]
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
