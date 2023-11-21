import streamlit as st

from genai.eyfs import TextGenerator
from genai.eyfs import get_embedding
from genai.streamlit_pages.eyfs_kb_bbc_page import get_index
from genai.streamlit_pages.eyfs_kb_bbc_page import query_pinecone
from genai.utils import read_json


def eyfs_compare() -> None:
    """Compare the EYFS prototypes."""
    st.title("Compare the EYFS prototypes")
    index = get_index(index_name="eyfs-index")
    areas_of_learning_desc = read_json("src/genai/eyfs/areas_of_learning.json")
    aol = list(areas_of_learning_desc.keys())

    with st.sidebar:
        # Select a model, temperature and number of results
        selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"], index=1)
        # description = "<THIS IS WHERE THE GENERATOR WILL SHOW THE RESULTS>"
        n_results = 10
        temperature = st.slider(label="**Temperature**", min_value=0.0, max_value=2.0, value=0.6, step=0.1)

    # Select the areas of learning
    areas_of_learning = st.multiselect(label="**Areas of learning**", options=aol, default=aol)
    areas_of_learning_text = [v for k, v in areas_of_learning_desc.items() if k in areas_of_learning]

    # Describe each Area of Learning in an expanding window
    with st.expander("**Areas of Learning Description**"):
        for k, v in areas_of_learning_desc.items():
            if k in areas_of_learning:
                st.write(f"#### {k}")
                st.write(v.split("##")[-1])

    areas_of_learning_text = "\n\n".join(areas_of_learning_text)
    location = st.selectbox(label="**Location**", options=["Indoor", "Outdoor", "Indoor or Outdoor"], index=2)

    # Get the user input
    query = st.text_input(
        label="**What's the topic you want activities for?**",
        value="Let's create activities educating children on how whales breathe",
        help="Prompt the large language model with a some text and it will generate an activity plan for you.",
    )
    if st.button(label="**Generate**", help="Generate an answer."):
        eyfs_prototype, eyfs_bbc_prototype = st.columns(2)
        eyfs_prototype.subheader("EYFS-related activities")
        eyfs_bbc_prototype.subheader("EYFS-related activities with ext KB (BBC)")
        with eyfs_prototype:
            with st.spinner("Generating activities..."):
                res_box = st.empty()
                report = []
                # Create the messages
                paths = [
                    "src/genai/eyfs/prompts/system.json",
                    "src/genai/eyfs/prompts/context_and_task.json",
                    "src/genai/eyfs/prompts/constraints.json",
                    "src/genai/eyfs/prompts/situation.json",
                ]

                messages = [read_json(path) for path in paths]
                messages_placeholders = {
                    "description": query,
                    "areas_of_learning": areas_of_learning,
                    "n_results": n_results,
                    "location": location,
                    "areas_of_learning_text": areas_of_learning_text,
                }

                r = TextGenerator.generate(
                    model=selected_model,
                    temperature=temperature,
                    messages=messages,
                    message_kwargs=messages_placeholders,
                    stream=True,
                )

                for chunk in r:
                    content = chunk["choices"][0].get("delta", {}).get("content")
                    report.append(content)
                    if chunk["choices"][0]["finish_reason"] != "stop":
                        result = "".join(report).strip()
                        res_box.markdown(f"{result}")

        with eyfs_bbc_prototype:
            # Create the messages
            paths = [
                "src/genai/eyfs/prompts/system.json",
                "src/genai/eyfs/prompts/context_and_task_with_examples.json",
                "src/genai/eyfs/prompts/constraints.json",
                "src/genai/eyfs/prompts/situation.json",
            ]

            messages = [read_json(path) for path in paths]
            with st.spinner("Searching for relevant BBC activities..."):
                # Encode the query
                encoded_query = get_embedding(query)

                # Search with Chroma
                similar_docs = query_pinecone(
                    index,
                    encoded_query,
                    areas_of_learning=areas_of_learning,
                    top_n=4,
                    max_n=4,
                )

            with st.spinner("Generating activities..."):
                res_box = st.empty()
                report = []
                # Create the prompt
                messages_placeholders = {
                    "description": query,
                    "areas_of_learning": areas_of_learning,
                    "n_results": n_results,
                    "location": location,
                    "areas_of_learning_text": areas_of_learning_text,
                    "activity_examples": "\n======\n".join(
                        [similar_doc["metadata"]["text"] for similar_doc in similar_docs]
                    ),
                }

                r = TextGenerator.generate(
                    model=selected_model,
                    temperature=temperature,
                    messages=messages,
                    message_kwargs=messages_placeholders,
                    stream=True,
                )

                for chunk in r:
                    content = chunk["choices"][0].get("delta", {}).get("content")
                    report.append(content)
                    if chunk["choices"][0]["finish_reason"] != "stop":
                        result = "".join(report).strip()
                        res_box.markdown(f"{result}")

            st.subheader("Sources")

            for similar_doc in similar_docs:
                title = similar_doc["metadata"]["title"]
                url = similar_doc["id"]
                category = similar_doc["metadata"]["areas_of_learning"]
                st.write(f"""- [{title}]({url}) {category}""")
