import prodigy

from prodigy.components.loaders import JSONL


@prodigy.recipe("compare_strings")
def compare_strings(dataset, input_file):
    stream = JSONL(input_file)
    html_template = "{{text1}}<br/><br/>{{text2}}"  # format this however you want

    return {"dataset": dataset, "stream": stream, "view_id": "html", "config": {"html_template": html_template}}
