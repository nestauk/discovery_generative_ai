import json


# Load data from the exported .jsonl file
with open("output.jsonl", "r") as file:
    annotations = [json.loads(line) for line in file]

# Now you can process the annotations
for entry in annotations:
    # Example: print the chosen answer for each question
    question = entry["text"]
    chosen_answer_id = entry["accept"][
        0
    ]  # 'accept' contains the IDs of the selected answers. Assuming single choice here.

    print(f"Question: {question}")
    print(f"Chosen Answer (ID): {chosen_answer_id}")
    print("-" * 40)
