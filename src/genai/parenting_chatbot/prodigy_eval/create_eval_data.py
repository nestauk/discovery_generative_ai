"""
Generate data for Prodigy platform to evaluate answers to questions about raising babies

Usage: Run the script from the repo root directory
$ poetry run python src/genai/parenting_chatbot/prodigy_eval/create_eval_data.py

The final output file is stored in data/answers.jsonl file
following the format: {"question": your-question, "answers": {"human": human-answer, "rag": rag-answer, "gpt4": gpt4-answer}}

"""

from itertools import combinations

import pandas as pd


# Constants
DATA_DIR = "src/genai/parenting_chatbot/prodigy_eval/data/"
QUESTION_FILE = DATA_DIR + "questions.jsonl"
ANSWER_FILE = DATA_DIR + "answers_{}.jsonl"
OUTPUT_FILE = DATA_DIR + "answers.jsonl"
# Define answer types and load corresponding answers
ANSWER_TYPES = ["human", "rag", "gpt4"]
# html formatting prefix and suffix for questions
QUESTION_PREFIX = "Which one is a better answer to this question:\n\n<span style='font-weight: bold; font-size:30px'>"
QUESTION_SUFFIX = "</span>"

if __name__ == "__main__":
    # Load questions
    questions = pd.read_json(QUESTION_FILE, lines=True)["question"].to_list()
    # Load answers
    answers = [
        pd.read_json(path_or_buf=ANSWER_FILE.format(answer_type), lines=True)[answer_type]
        for answer_type in ANSWER_TYPES
    ]

    answers_df = (
        # Construct a dataframe with columns: question, human, rag, and gpt4
        pd.DataFrame({"question": questions, "human": answers[0], "rag": answers[1], "gpt4": answers[2]})
        # Melt the dataframe for pairwise combinations and rename the resulting column
        .melt(id_vars=["question"], value_vars=ANSWER_TYPES).rename(columns={"value": "answer"})
        # Add html formatting to the question
        .assign(question=lambda df: QUESTION_PREFIX + df["question"] + QUESTION_SUFFIX)
        # Format the answer as a dictionary {answer_type: answer}
        .assign(answer=lambda df: df.apply(lambda x: {x["variable"]: x["answer"]}, axis=1))
    )

    # Generate pairwise combinations of answer types
    answer_type_pairs = list(combinations(ANSWER_TYPES, 2))

    # Aggregate answers based on the pairwise combinations of answer types
    dataframes = []
    for answer_type_pair in answer_type_pairs:
        subset_df = answers_df[answers_df["variable"].isin(answer_type_pair)]
        aggregated_df = subset_df.groupby("question").agg(lambda x: x.tolist()).reset_index()
        dataframes.append(aggregated_df)

    # Combine the results, merge dictionaries and save the output
    (
        pd.concat(dataframes, ignore_index=True)
        .assign(answers=lambda df: df.apply(lambda x: {k: v for d in x["answer"] for k, v in d.items()}, axis=1))
        .drop(columns=["variable", "answer"])
        .sort_values(by="question")
        .reset_index(drop=True)
        .to_json(path_or_buf=OUTPUT_FILE, orient="records", lines=True)
    )
