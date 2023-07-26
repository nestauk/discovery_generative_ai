import json


def read_json(path: str) -> dict:
    """Read a JSON file and return a dictionary."""
    with open(path, "r") as f:
        return json.load(f)
