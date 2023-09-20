import argparse
import os

import boto3

from dotenv import load_dotenv


parser = argparse.ArgumentParser(description="Names and locations of inputs and outputs")

parser.add_argument(
    "--s3_path",
    type=str,
    dest="s3_path",
    help="Path to the file in the S3 bucket",
    default="prototypes/parenting-chatbot/prodigy_evaluation/prodigy_training_data.jsonl",
)

parser.add_argument(
    "--out_path",
    type=str,
    dest="out_path",
    help="Path to save the file locally",
    default="src/genai/parenting_chatbot/prodigy_eval/data",
)

parser.add_argument(
    "--out_name", type=str, dest="out_name", help="Name to save the file under", default="prodigy_training_data.jsonl"
)

args, unknown = parser.parse_known_args()

load_dotenv()

s3_path = os.environ["S3_BUCKET"]


def fetch_from_s3(bucket_name: str, s3_path_to_file: str, local_path_to_file: str, filename: str) -> None:
    """Fetch data from the s3 bucket and store it locally.

    Args:
        bucket_name (str): Name of the bucket
        s3_path_to_file (str): Filepath including the name of the file in the bucket.
        local_path_to_file (str): Filepath indicating where you want to save the file locally.
        filename (str): Name of the file to save locally eg 'data.jsonl'.
    """
    s3 = boto3.client("s3")
    s3.download_file(bucket_name, s3_path_to_file, os.path.join(local_path_to_file, filename))


if __name__ == "__main__":
    if not os.path.exists(args.out_path):
        os.makedirs(args.out_path)

    fetch_from_s3(s3_path, args.s3_path, args.out_path, args.out_name)
