import pinecone
import streamlit as st
from genai.streamlit_pages.utils import reset_state
from genai.utils import read_json
from genai.streamlit_pages.utils import get_index
from genai.streamlit_pages.utils import sample_docs
from genai.eyfs import get_embedding

from genai import MessageTemplate
from genai.eyfs import ActivityGenerator


def eyfs_dm_kb(index_name: str = "eyfs-index") -> None:
    """Run the Development Matters app."""
    st.title("Generate activities anchored to the Development Matters guidance")
    areas_of_learning_desc = read_json("src/genai/eyfs/areas_of_learning.json")
    aol = list(areas_of_learning_desc.keys())
    index = get_index(index_name=index_name)
    examples = None

    with st.sidebar:
        # Select a model, temperature and number of results
        selected_model = st.radio(
            label="**OpenAI model**",
            options=["gpt-3.5-turbo", "gpt-4"],
            index=1,
            on_change=reset_state,
        )

        temperature = st.slider(
            label="**Temperature**",
            min_value=0.0,
            max_value=2.0,
            value=0.6,
            step=0.1,
            on_change=reset_state,
        )

        st.button("Reset chat", on_click=reset_state, type="primary", help="Reset the chat history")

    choice = st.radio(
        label="**Select a learning goal**",
        options=["Pick a predefined learning goal", "Describe a learning goal"],
    )

    age_groups = st.multiselect(
        label="**Age group (in years)**",
        options=["0-3", "3-4", "4-5"],
        default=["0-3", "3-4", "4-5"],
        on_change=reset_state,
    )

    if choice == "Pick a predefined learning goal":
        # Select the areas of learning
        areas_of_learning = st.multiselect(
            label="**Areas of learning**",
            options=aol,
            default=aol,
            on_change=reset_state,
        )

        if areas_of_learning and age_groups:
            predefined_learning_goals = get_data(
                path="data/dm/dm.json",
                type_="learning_goals",
                areas_of_learning=areas_of_learning,
                age_groups=age_groups,
            )
            learning_goals = st.multiselect(
                label="**Predefined Learning Goals**",
                options=predefined_learning_goals,
                default=predefined_learning_goals[0],
                on_change=reset_state,
            )

            if st.button("Search for activity examples"):
                results = []
                for learning_goal in learning_goals:
                    search_results = query_pinecone(
                        index=index,
                        encoded_query=get_embedding(learning_goal),
                        areas_of_learning=areas_of_learning,
                        age_group=age_groups,
                        type_="examples",
                    )
                    results.extend(search_results)

                idx = sample_docs(num_docs=len(results), n=6)
                results = [results[i] for i in idx]

                examples = "\n\n".join([result["metadata"]["text"] for result in results])

                st.write(examples)

    elif choice == "Describe a learning goal":
        text_input = st.text_input(label="Describe a learning goal")

    if examples:
        if st.button("Generate activities"):
            


def get_data(path, type_, areas_of_learning, age_groups):
    """Get Learning Goals or Examples based on the selected areas of learning and age groups."""
    data = read_json(path)
    # Temp hack to exclude the template
    data = [d for d in data if d["area_of_learning"] != ""]

    predefined_learning_goals = []
    for elem in data:
        aol = elem["area_of_learning"]
        d = elem["age_group"]
        for age, age_dict in d.items():
            for k, items in age_dict.items():
                if k == type_ and aol in areas_of_learning and age in age_groups:
                    for item in items:
                        predefined_learning_goals.append(item)

    return predefined_learning_goals


def query_pinecone(
    index: pinecone.index.Index,
    encoded_query: list,
    areas_of_learning: list,
    age_group: list,
    type_: str,
    top_n: int = 5,
    max_n: int = 10,
) -> list:
    """Query the pinecone index.

    Parameters
    ----------
    index
        Pinecone index.

    query
        Query vector to search for.

    areas_of_learning
        Areas of learning to filter by.

    top_n
        Number of results to return.

    max_n
        Maximum number of results to keep as prompt examples.

    Returns
    -------
    docs
        List of documents.

    """
    results = index.query(
        vector=encoded_query,
        top_k=top_n,
        include_metadata=True,
        filter={
            "areas_of_learning": {"$in": areas_of_learning},
            "source": {"$eq": "dm"},
            "age_group": {"$in": age_group},
            "type_": {"$eq": type_},
        },
    )

    return results["matches"]
