import json
import os

from typing import Generator
from typing import List


def read_json(path: str, lines: bool = False) -> List[dict]:
    """Read a JSONL file."""
    with open(path, "r") as f:
        if lines:
            return [json.loads(line) for line in f.readlines()]
        return json.load(f)


def batch(lst: list, n: int) -> Generator:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def create_directory_if_not_exists(dir_path: str) -> None:
    """Create a directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
