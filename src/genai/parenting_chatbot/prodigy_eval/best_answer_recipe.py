from typing import Dict
from typing import List

import prodigy

from prodigy.components.loaders import JSONL


GLOBAL_CSS = (
    ".prodigy-content{font-size: 15px}"
    " .prodigy-option{width: 49%}"
    " .prodigy-option{align-items:flex-start}"
    " .prodigy-option{margin-right: 3px}"
    " .prodigy-container{max-width: 1200px}"
)


@prodigy.recipe(
    "best_answer",
    dataset=("The dataset to save to", "positional", None, str),
    file_path=("Path to the questions and answers file", "positional", None, str),
)
def best_answer(dataset: str, file_path: str) -> Dict:
    """
    Choose the best answer out of the given options.

    Arguments:
        dataset: The dataset to save to.
        file_path: Path to the questions and answers file.

    Returns:
        A dictionary containing the recipe configuration.

    """

    # Load the data
    stream = JSONL(file_path)

    # Process the stream to format for Prodigy
    def format_stream(stream: List) -> Dict:
        for item in stream:
            question = item["question"]
            options = [{"id": key, "html": value} for key, value in item["answers"].items()]
            yield {"html": question, "options": options}

    stream = format_stream(stream)

    return {
        # Use the choice interface
        "view_id": "choice",
        # Name of the dataset
        "dataset": dataset,
        # The data stream
        "stream": stream,
        "config": {
            # Only allow one choice
            "choice_style": "single",
            "task_description": "Choose the best answer",
            "choice_auto_accept": False,
            "buttons": ["accept", "ignore"],
            "global_css": GLOBAL_CSS,
            "feed_overlap": True,
        },
    }
