import json

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
