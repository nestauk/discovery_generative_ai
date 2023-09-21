import json
import os

from typing import Generator
from typing import List

import boto3


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


def read_jsonl_from_s3(s3_uri: str) -> List[dict]:
    """Read a JSONL file from S3."""
    s3_uri = s3_uri.replace("s3://", "")
    bucket_name = s3_uri.split("/")[0]
    file_key = "/".join(s3_uri.split("/")[1:])

    s3 = boto3.client("s3")
    s3_object = s3.get_object(Bucket=bucket_name, Key=file_key)
    content = s3_object["Body"].read().decode("utf-8")

    return [json.loads(line) for line in content.strip().split("\n")]
