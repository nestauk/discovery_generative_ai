"""Join the BBC activities with the labelled activities and build a Chroma index."""

import os

import chromadb
import numpy as np
import openai
import pandas as pd

from dotenv import load_dotenv

from genai.eyfs import get_embedding
from genai.utils import batch
from genai.utils import read_json


load_dotenv()


openai.api_key = os.environ["OPENAI_API_KEY"]
PATH_TO_LABELLED_ACTIVITIES = "data/eyfs_labels/parsed_json.jsonl"
PATH_TO_BBC_ACTIVITIES = "data/eyfs/tiny_happy_people - final - tiny_happy_people - final.csv"
PATH_TO_CHROMA_INDEX = "data/eyfs/chroma_index"
INDEX_NAME = "eyfs_chroma_index"


def get_labelled_bbc_activities(path: str) -> pd.DataFrame:
    """Read and clean the labelled BBC activities file and return a dataframe.

    Currently, we keep the first prediction only.
    Chromadb doesn't support a list in metadata (or searching lists).
    PR: https://github.com/chroma-core/chroma/pull/840
    """
    data = read_json(path, lines=True)
    df = pd.concat([pd.DataFrame([line]) for line in data])
    df["prediction"] = df["prediction"].apply(lambda row: row[0] if row else np.nan)
    df = df[~df.prediction.isnull()]
    # df = df.explode("prediction")
    df = df[df.prediction != "None"]
    # df = df.groupby("url")["prediction"].apply(list).reset_index()
    df = df.rename({"prediction": "areas_of_learning", "url": "URL"}, axis=1)

    return df


def get_bbc_activities(path: str) -> pd.DataFrame:
    """Read and clean the BBC activities file and return a dataframe."""
    df = pd.read_csv(path)
    df = df.rename(columns={"Age Range (if applicable)": "Age"})
    df = df.dropna(subset=["text", "URL"])
    df = df.drop_duplicates(subset=["URL"])

    return df


def build_chroma_index(
    path: str,
    index_name: str,
    df: pd.DataFrame,
    batch_size: int = 200,
) -> None:
    """Build a chroma index from a dataframe.

    Parameters
    ----------
    path
        Where the index will be saved.

    index_name
        Name of the index.

    df
        Dataframe containing the data to index. It must contain the following columns:
        - URL
        - text
        - embedding
        - areas_of_learning

    batch_size
        Batch size to use when adding documents to the index.

    Returns
    -------
    collection
        The chroma index.

    """
    # Build a quick and dirty index
    client = chromadb.PersistentClient(path)
    collection = client.get_or_create_collection(index_name)

    embeddings = batch(df["embedding"].tolist(), batch_size)
    url = batch(df["URL"].tolist(), batch_size)
    area_of_learnings = batch(df["areas_of_learning"].tolist(), batch_size)
    text = batch(df["text"].tolist(), batch_size)

    for batch_embeddings, batch_url, batch_area_of_learnings, batch_text in zip(
        embeddings, url, area_of_learnings, text
    ):
        collection.add(
            ids=batch_url,
            embeddings=batch_embeddings,
            metadatas=[{"area_of_learning": aol} for aol in batch_area_of_learnings],
            documents=batch_text,
        )

    return collection


def main() -> None:
    """Run the script."""
    # Read and merge dataframes
    labels = get_labelled_bbc_activities(PATH_TO_LABELLED_ACTIVITIES)
    bbc = get_bbc_activities(PATH_TO_BBC_ACTIVITIES)

    df = labels.merge(bbc[["SHORT DESCRIPTION", "text", "URL"]], how="left", left_on="URL", right_on="URL")

    # Encode the BBC activities' text
    df["embedding"] = df["text"].apply(lambda row: get_embedding(row, model="text-embedding-ada-002"))

    build_chroma_index(PATH_TO_CHROMA_INDEX, INDEX_NAME, df)


if "__main__" == __name__:
    main()
