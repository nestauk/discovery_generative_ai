import chromadb
import streamlit as st

from chromadb.api.models.Collection import Collection

from genai.eyfs import get_embedding


def eyfs_kb_bbc(path: str = "data/eyfs/chroma_index/") -> None:
    """Run the EYFS + BBC activities app."""
    collection = get_collection(path=path, index_name="eyfs_chroma_index")
    query = st.text_input(
        label="**What's the topic you want activities for?**",
        value="sing a lullaby",
    )

    if st.button(label="**Generate**", help="Generate an answer."):
        encoded_query = get_embedding(query)
        r = collection.query(encoded_query, n_results=5)

        for ids, distances, metadatas, texts in zip(r["ids"], r["distances"], r["metadatas"], r["documents"]):
            for id, distance, metadata, text in zip(ids, distances, metadatas, texts):
                st.write(
                    f"""#### {id}\n\n**Euclidean distance**: {distance}\n\n**Text**: {text}\n\n**Area of learning**: {metadata["area_of_learning"]}"""  # noqa: B950
                )

        st.write(r)


@st.cache_resource
def get_collection(path: str, index_name: str) -> Collection:
    """Return and persist the chroma db collection."""
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(name=index_name)
    return collection
