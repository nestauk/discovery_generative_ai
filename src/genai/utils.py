import json


def read_json(path: str) -> dict:
    """Read a JSON file and return a dictionary."""
    with open(path, "r") as f:
        return json.load(f)


def batch(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]  # noqa: E203
