# Creating a Prodigy app to evaluate parenting chatbot answers

## Setup instructions

To install prodigy, you will need to run `python -m pip install --upgrade prodigy -f https://XXXX-XXXX-XXXX-XXXX@download.prodi.gy`, replacing 'XXXX' with your key (see the docs [here](https://prodi.gy/docs/install)).

Create a directory `src/genai/parenting_chatbot/prodigy_eval/data/` (this is temporary - we will store files on s3 in future).

Run `python src/genai/parenting_chatbot/prodigy_eval/create_data.py`. This will save data to `src/genai/parenting_chatbot/prodigy_eval/data/training_data.jsonl` and this will be the training data that your annotators annotate via the Prodigy app.

Next, run `prodigy best_answer answer_data src/genai/parenting_chatbot/prodigy_eval/data/training_data.jsonl -F src/genai/parenting_chatbot/prodigy_eval/best_answer_recipe.py`. Once you run this line, a URL should be given to you in the command line. Visit this URL to access the Prodigy app.

Select an answer to each question, click the green tick button at the bottom, and when you're done, click the "save" icon at the top left.

Make the output from your annotations available by running `prodigy db-out answer_data > output.jsonl`.

If you would like a summary of the selection you made for each question, run `python analyse_annotations.py`. This will print each question + the selection (human/gpt4/RAG) to the command line.

## Troubleshooting

**I just started a new session in Prodigy, but it says there are already some examples.**

Prodigy has its own mysterious SQLite database. Whenever you want to see the data, you run
```
prodigy db-out name_of_your_data > output.jsonl
```

If you were running a session earlier and saved annotations to `name_of_your_data`, then you want to start a new session but use the name `name_of_your_data` again, Prodigy will tell you that you already have X annotations because you saved X annotations to this dataset earlier.

The solution is to run:
```
prodigy drop name_of_your_data
```

OR just pick a new dataset name, and then Prodigy will create a new dataset.
