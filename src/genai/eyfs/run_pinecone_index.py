"""Join the BBC activities with the labelled activities and build a pinecone index."""

import os

from typing import Generator

import numpy as np
import openai
import pandas as pd
import pinecone

from dotenv import load_dotenv

from genai.eyfs import get_embedding
from genai.utils import batch
from genai.utils import read_json


load_dotenv()


openai.api_key = os.environ["OPENAI_API_KEY"]
PATH_TO_LABELLED_ACTIVITIES = "data/eyfs_labels/parsed_json.jsonl"
PATH_TO_BBC_ACTIVITIES = "data/eyfs/tiny_happy_people - final - tiny_happy_people - final.csv"
INDEX_NAME = "eyfs-index"
ENCODER_NAME = "text-embedding-ada-002"


def get_labelled_bbc_activities(path: str) -> pd.DataFrame:
    """Read and clean the labelled BBC activities file and return a dataframe."""
    data = read_json(path, lines=True)
    df = pd.concat([pd.DataFrame([line]) for line in data])
    df["prediction"] = df["prediction"].apply(lambda row: row if row else np.nan)
    df = df[~df.prediction.isnull()]
    df = df[df.prediction != "None"]
    df = df.rename({"prediction": "areas_of_learning", "url": "URL"}, axis=1)

    return df


def get_bbc_activities(path: str) -> pd.DataFrame:
    """Read and clean the BBC activities file and return a dataframe."""
    df = pd.read_csv(path)
    df = df.rename(columns={"Age Range (if applicable)": "Age", "CONTENT": "title"})
    df = df.dropna(subset=["text", "URL"])
    df = df.drop_duplicates(subset=["URL"])

    return df


def build_vector_index(
    items: Generator,
    index_name: str,
    vector_size: int = 1536,
    metric: str = "euclidean",
    environment: str = "us-west1-gcp",
) -> None:
    """Build a vector index from a dataframe.

    Parameters
    ----------
    items
        The items to be indexed.

    index_name
        Name of the index.

    vector_size
        Length of the indexed vectors.

    metric
        The distance metric to use.

    environment
        The cloud environment to use.

    """
    # Connect to pinecone
    pinecone.init(
        api_key=os.environ["PINECONE_API_KEY"],
        environment=environment,
    )

    # Search by this metadata
    metadata_config = {"indexed": ["areas_of_learning"]}

    # Build a new index every time
    if index_name in pinecone.list_indexes():
        pinecone.delete_index(index_name)

    pinecone.create_index(
        index_name,
        dimension=vector_size,
        metadata_config=metadata_config,
        metric=metric,
    )

    index = pinecone.Index(index_name)
    for batched_items in items:
        index.upsert(batched_items)


def main() -> None:
    """Run the script."""
    # Read and merge dataframes
    labels = get_labelled_bbc_activities(PATH_TO_LABELLED_ACTIVITIES)
    bbc = get_bbc_activities(PATH_TO_BBC_ACTIVITIES)

    df = labels.merge(bbc[["SHORT DESCRIPTION", "text", "URL", "title"]], how="left", left_on="URL", right_on="URL")

    # Encode the BBC activities' text
    df["embedding"] = df["text"].apply(lambda row: get_embedding(row, model=ENCODER_NAME))

    # Batch items
    items = []
    for tup in df.itertuples():
        item = (
            tup.URL,
            tup.embedding,
            {"areas_of_learning": tup.areas_of_learning, "title": tup.title, "text": tup.text},
        )
        items.append(item)

    items = batch(items, 100)

    # Build the index
    build_vector_index(items, INDEX_NAME, vector_size=len(df["embedding"].iloc[0]))


if "__main__" == __name__:
    main()
