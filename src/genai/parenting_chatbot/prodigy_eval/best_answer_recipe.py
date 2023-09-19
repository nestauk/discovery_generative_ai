import prodigy

from prodigy.components.loaders import JSONL


@prodigy.recipe(
    "best_answer",
    dataset=("The dataset to save to", "positional", None, str),
    file_path=("Path to the questions and answers file", "positional", None, str),
)
def best_answer(dataset: str, file_path: str) -> dict:
    """Choose the best answer out of three given options."""

    # Load the data
    stream = JSONL(file_path)

    # Process the stream to format for Prodigy
    def format_stream(stream: list) -> dict:
        for item in stream:
            question = item["question"]
            options = [{"id": key, "text": value} for key, value in item["answers"].items()]
            yield {"text": question, "options": options}

    stream = format_stream(stream)

    return {
        "view_id": "choice",  # Use the choice interface
        "dataset": dataset,  # Name of the dataset
        "stream": stream,  # The data stream
        "config": {
            "choice_style": "single",
            "task_description": "Choose the best answer",  # Only allow one choice
            "choice_auto_accept": True,
            "buttons": ["accept", "ignore"],
        },
    }
