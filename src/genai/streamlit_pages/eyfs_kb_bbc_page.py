import pinecone
import streamlit as st

from genai import MessageTemplate
from genai.eyfs import TextGenerator
from genai.eyfs import get_embedding
from genai.streamlit_pages.utils import get_index
from genai.streamlit_pages.utils import reset_state
from genai.streamlit_pages.utils import sample_docs
from genai.utils import read_json


def eyfs_kb_bbc(index_name: str = "eyfs-index") -> None:
    """Run the EYFS + BBC activities app."""
    st.title("Generating activity plans grounded in EY foundation stages")
    areas_of_learning_desc = read_json("src/genai/eyfs/areas_of_learning.json")
    aol = list(areas_of_learning_desc.keys())
    index = get_index(index_name=index_name)

    with st.sidebar:
        # Select a model, temperature and number of results
        selected_model = st.radio(
            label="**OpenAI model**",
            options=["gpt-3.5-turbo", "gpt-4"],
            index=1,
            on_change=reset_state,
        )
        n_results = 10
        temperature = st.slider(
            label="**Temperature**",
            min_value=0.0,
            max_value=2.0,
            value=0.6,
            step=0.1,
            on_change=reset_state,
        )

        st.button("Reset chat", on_click=reset_state, type="primary", help="Reset the chat history")

    # Select the areas of learning
    areas_of_learning = st.multiselect(
        label="**Areas of learning**",
        options=aol,
        default=aol,
        on_change=reset_state,
    )
    areas_of_learning_text = [v for k, v in areas_of_learning_desc.items() if k in areas_of_learning]

    # Describe each Area of Learning in an expanding window
    with st.expander("**Areas of Learning Description**"):
        for k, v in areas_of_learning_desc.items():
            if k in areas_of_learning:
                st.write(f"#### {k}")
                st.write(v.split("##")[-1])

    areas_of_learning_text = "\n\n".join(areas_of_learning_text)
    location = st.selectbox(label="**Location**", options=["Indoor", "Outdoor", "Indoor or Outdoor"], index=2)

    # Create the messages
    paths = [
        "src/genai/eyfs/prompts/system.json",
        "src/genai/eyfs/prompts/context_and_task_with_examples.json",
        "src/genai/eyfs/prompts/constraints.json",
        "src/genai/eyfs/prompts/situation.json",
    ]

    prompt_templates = [MessageTemplate.load(path) for path in paths]

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": prompt_template.role, "content": prompt_template.content} for prompt_template in prompt_templates
        ]

    # Display chat messages from history on app rerun.
    # The first messages are the prompt, so we skip it.
    for message in st.session_state.messages[len(prompt_templates) :]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Let's create activities educating children on how whales breathe")
    if prompt:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Add user message to chat history
        # The very first message will be used to fill in the prompt template
        # after that, we store the user messages in the chat history
        if len(st.session_state.messages) == len(prompt_templates):
            query = prompt
            with st.spinner("Searching for relevant BBC activities..."):
                # Encode the query
                encoded_query = get_embedding(query)

                # Search with Pinecone
                similar_docs = query_pinecone(
                    index,
                    encoded_query,
                    areas_of_learning=areas_of_learning,
                    top_n=4,
                    max_n=4,
                )

                if "similar_docs" not in st.session_state:
                    st.session_state["similar_docs"] = similar_docs

        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            query = ""

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            messages_placeholders = {
                "description": query,
                "areas_of_learning": areas_of_learning,
                "n_results": n_results,
                "location": location,
                "areas_of_learning_text": areas_of_learning_text,
                "activity_examples": "\n======\n".join(
                    [similar_doc["metadata"]["text"] for similar_doc in st.session_state["similar_docs"]]
                ),
            }

            st.text(messages_placeholders["activity_examples"])

            r = TextGenerator.generate(
                model=selected_model,
                temperature=temperature,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                message_kwargs=messages_placeholders,
                stream=True,
            )

            for response in r:
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            if len(st.session_state.messages) == len(prompt_templates):
                st.subheader("Sources")
                for similar_doc in st.session_state["similar_docs"]:
                    title = similar_doc["metadata"]["title"]
                    url = similar_doc["id"]
                    category = similar_doc["metadata"]["areas_of_learning"]
                    st.write(f"""- [{title}]({url}) {category}""")
        st.session_state.messages.append({"role": "assistant", "content": full_response})


def query_pinecone(
    index: pinecone.index.Index,
    encoded_query: list,
    areas_of_learning: list,
    top_n: int = 4,
    max_n: int = 4,
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
            "source": {"$eq": "BBC"},
        },
    )

    results = results["matches"]
    # Subset docs to fit the prompt length
    idx = sample_docs(len(results), max_n)

    return [results[i] for i in idx]
