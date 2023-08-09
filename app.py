"""Streamlit app for the Generative AI prototypes."""

import os

import openai
import pandas as pd
import streamlit as st

from dotenv import load_dotenv
from streamlit_option_menu import option_menu

from genai.streamlit_pages import early_year_activity_plan
from genai.streamlit_pages import eli3


load_dotenv()


def auth_openai() -> None:
    """Authenticate with OpenAI."""
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
    except Exception:
        openai.api_key = st.secrets["OPENAI_API_KEY"]


auth_openai()


def main() -> None:
    """Run the app."""
    auth_openai()
    with st.sidebar:
        selected = option_menu(
            "Prototypes",
            ["Home page", "ELI3", "EYFS-based activities", "EYFS-based activities + BBC activities"],
            default_index=0,
        )
    if selected == "Home page":
        st.title("Nesta Discovery: Generative AI Prototypes")
        st.write("Welcome to the Nesta Discovery Generative AI prototypes. Please select a prototype from the menu.")
    elif selected == "ELI3":
        eli3()
    elif selected == "EYFS-based activities":
        early_year_activity_plan()
    elif selected == "EYFS-based activities + BBC activities":
        eyfs_kb()


def check_password() -> bool:
    """Return `True` if the user had the correct password."""

    def password_entered() -> None:
        """Check whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.

        return True


def eyfs_kb() -> None:
    """Add docstring"""
    from genai.eyfs.vector_db import get_embedding

    st.title("Testing")

    collection = read_bbc_and_embed("data/eyfs/tiny_happy_people - final - tiny_happy_people - final.csv")
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
                    f"""#### {id}\n\n**Euclidean distance**: {distance}\n\n**Text**: {text}\n\n**Metadata**: {metadata}"""
                )

        st.write(r)


@st.cache_resource
def read_bbc_and_embed(
    path: str = "data/eyfs/tiny_happy_people - final - tiny_happy_people - final.csv",
) -> pd.DataFrame:
    """Read the BBC dataset."""
    import chromadb

    from genai.eyfs.vector_db import batch
    from genai.eyfs.vector_db import get_embedding

    df = pd.read_csv(path)
    df = df.rename(columns={"Age Range (if applicable)": "Age"})
    df = df.dropna(subset=["text", "URL"])
    df = df.drop_duplicates(subset=["URL"])
    df["embedding"] = df["text"].apply(lambda row: get_embedding(row, model="text-embedding-ada-002"))

    embeddings = batch(df["embedding"].tolist(), 200)
    url = batch(df["URL"].tolist(), 200)
    age = batch(df["Age"].tolist(), 200)
    activity_type = batch(df["Type"].tolist(), 200)
    text = batch(df["text"].tolist(), 200)

    # Build a quick and dirty index
    client = chromadb.Client()

    collection = client.create_collection("eyfs_kb3")

    for batch_embeddings, batch_url, batch_age, batch_activity_type, batch_text in zip(
        embeddings, url, age, activity_type, text
    ):
        collection.add(
            ids=batch_url,
            embeddings=batch_embeddings,
            metadatas=[{"age": age, "activity": activity} for age, activity in zip(batch_age, batch_activity_type)],
            documents=batch_text,
        )

    return collection


if check_password():
    main()
