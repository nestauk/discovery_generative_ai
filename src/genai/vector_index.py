import os

from typing import Optional

import pinecone

from genai.utils import batch


class PineconeIndex:
    """Wrap the Pinecone API.

    Note that this is a very thin and untested wrapper. It is not intended for production use.
    Its main purpose is to support this repo's prototypes and tiny indexes.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> None:
        """Initialize the index."""

        # Connect to pinecone
        if api_key and environment:
            pinecone.init(
                api_key=api_key,
                environment=environment,
            )
        else:
            pinecone.init(
                api_key=os.environ["PINECONE_API_KEY"],
                environment=os.environ["PINECONE_REGION"],
            )

    def connect(self, index_name: str) -> pinecone.index.Index:
        """Connect to the index."""
        if index_name not in pinecone.list_indexes():
            raise ValueError(f"Index {index_name} does not exist.")

        return pinecone.Index(index_name)

    def build_and_upsert(
        self,
        index_name: str,
        dimension: int,
        metadata_config: dict,
        metric: str,
        docs: list,
        batch_size: int = 100,
        delete_if_exists: bool = False,
        **kwargs,
    ) -> None:
        """Build the index (if it does not exist) and add docs.

        Parameters
        ----------
        index_name
            Name of the index.

        dimension
            Length of the indexed vectors.

        metadata_config
            The metadata config.

        metric
            The distance metric to use.

        docs
            The documents to index.

        batch_size
            The batch size to use when indexing.

        delete_if_exists
            Whether to delete the index if it already exists.

        """
        if delete_if_exists:
            self.delete(index_name)

        if index_name in pinecone.list_indexes():
            index = self.connect(index_name)
        else:
            pinecone.create_index(
                index_name,
                dimension=dimension,
                metadata_config=metadata_config,
                metric=metric,
            )

            index = self.connect(index_name)

        for batched_docs in batch(docs, batch_size):
            index.upsert(batched_docs)

    @staticmethod
    def delete(index_name: str) -> None:
        """Delete the index."""
        try:
            pinecone.delete_index(index_name)
        except Exception as e:
            print(e)  # noqa: T001
