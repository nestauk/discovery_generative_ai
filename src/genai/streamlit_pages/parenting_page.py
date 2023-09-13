import json
import uuid

from datetime import datetime

import s3fs
import streamlit as st

from dotenv import load_dotenv
from streamlit_feedback import streamlit_feedback

from genai.eyfs import TextGenerator
from genai.eyfs import get_embedding
from genai.message_history import InMemoryMessageHistory
from genai.prompt_template import FunctionTemplate
from genai.prompt_template import MessageTemplate
from genai.streamlit_pages.utils import get_index
from genai.streamlit_pages.utils import query_pinecone
from genai.streamlit_pages.utils import reset_state


load_dotenv()


def parenting_chatbot(aws_key: str, aws_secret: str, s3_path: str) -> None:
    """Parenting chatbot."""
    st.title("Parenting Chatbot")

    selected_model = "gpt-3.5-turbo"
    temperature = 0.6
    # max_tokens = 100

    pinecone_index = get_index(index_name="eyfs-index")

    with st.sidebar:
        st.button("Reset chat", on_click=reset_state, type="primary", help="Reset the chat history")

        # if st.button("Show feedback", type="primary"):
        #     st.write(st.session_state["user_feedback"])

    system_message = MessageTemplate.load("src/genai/parenting_chatbot/prompts/system.json")
    filter_refs_function = FunctionTemplate.load("src/genai/parenting_chatbot/prompts/filter_refs_function.json")
    filter_refs_user_message = MessageTemplate.load("src/genai/parenting_chatbot/prompts/filter_refs_user.json")
    filter_refs_system_message = MessageTemplate.load("src/genai/parenting_chatbot/prompts/filter_refs_system.json")

    if "session_uuid" not in st.session_state:
        st.session_state["session_uuid"] = f"{current_time()}-{str(uuid.uuid4())}"

    # if "user_feedback" not in st.session_state:
    #     st.session_state["user_feedback"] = []

    # Single submitted feedback
    if "feedback" not in st.session_state:
        st.session_state["feedback"] = None

    # st.session_state["memory"] controls the flow to OpenAI and logging
    if "memory" not in st.session_state:
        st.session_state["memory"] = InMemoryMessageHistory()
        st.session_state["memory"].add_message(system_message.to_prompt())

    # st.session_state["messages"] shows the conversation in the UI
    if "messages" not in st.session_state:
        # instantiate the memory instead of None
        # st.session_state["messages"] = [{"role": "assistant", "content": "You are a good bot."}]
        st.session_state["messages"] = [system_message.to_prompt()]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    prompt = st.chat_input("What's on your mind?")
    if prompt:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Search the vector index
        search_results = query_pinecone(
            index=pinecone_index,
            encoded_query=get_embedding(prompt),
            top_n=3,
            filters={
                "source": {"$eq": "nhs_full_page"},
            },
        )

        nhs_texts = []
        nhs_urls = []
        for result in search_results:
            pred = TextGenerator.generate(
                temperature=0.0,
                messages=[filter_refs_system_message, filter_refs_user_message],
                message_kwargs={"text": result["metadata"]["text"], "question": prompt},
                functions=[filter_refs_function.to_prompt()],
                function_call={"name": filter_refs_function.name},
            )

            pred = json.loads(pred["choices"][0]["message"]["function_call"]["arguments"])["prediction"]

            # st.text(pred)
            # st.text(result["metadata"]["text"])

            if pred:
                nhs_texts.append(result["metadata"]["text"])
                nhs_urls.append(result["metadata"]["url"])

        if nhs_texts:
            nhs_texts = "\n===\n".join(nhs_texts)

        # Log message for the UI before adding the references
        st.session_state["messages"].append({"role": "user", "content": prompt})
        # Add user message to chat history
        prompt = f"""###NHS Start for Life references###\n{nhs_texts}\n\n###User message###\n{prompt}"""
        # st.session_state["messages"].append({"role": "user", "content": prompt})
        st.session_state["memory"].add_message({"role": "user", "content": prompt})

        # st.text(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            # full_response = "I'm a confused bot."

            for response in TextGenerator.generate(
                model=selected_model,
                temperature=temperature,
                messages=st.session_state["memory"].get_messages(),
                message_kwargs=None,
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")

            # Submit feedback
            streamlit_feedback(
                feedback_type="faces",
                single_submit=False,
                optional_text_label="[Optional] Please provide an explanation",
                key="feedback",
            )

            message_placeholder.markdown(full_response)

            # Display NHS URLs in chat message container
            if nhs_urls:
                with st.expander("NHS Start for Life references"):
                    for url in nhs_urls:
                        st.markdown(f"[{url}]({url})")

        st.session_state["messages"].append({"role": "assistant", "content": full_response})
        st.session_state["memory"].add_message({"role": "assistant", "content": full_response})

        # st.write(f"Messages: {st.session_state['messages']}")
        # st.write(st.session_state["memory"].get_messages(model_name=model_name, max_tokens=max_tokens))

    # Log feedback and messages
    if st.session_state["feedback"]:
        user_feedback = {
            "user_message": st.session_state["messages"][-2],
            "assistant_message": st.session_state["messages"][-1],
            "feedback_score": st.session_state["feedback"]["score"],
            "feedback_text": st.session_state["feedback"]["text"],
        }

        write_to_s3(
            aws_key,
            aws_secret,
            f"{s3_path}/session-logs/{st.session_state['session_uuid']}",
            "feedback",
            user_feedback,
            how="a",
        )

    write_to_s3(
        aws_key,
        aws_secret,
        f"{s3_path}/session-logs/{st.session_state['session_uuid']}",
        "messages",
        st.session_state["messages"],
        how="w",
    )


def write_to_s3(key: str, secret: str, s3_path: str, filename: str, data: dict, how: str = "a") -> None:
    """Write data to a jsonl file in S3.

    Parameters
    ----------
    key
        AWS access key ID.

    secret
        AWS secret access key.

    s3_path
        S3 bucket path.

    filename
        Name of the file to write to.

    data
        Data to write to the file.

    how
        How to write to the file. Default is "a" for append. Use "w" to overwrite.

    """
    fs = s3fs.S3FileSystem(key=key, secret=secret)
    with fs.open(f"{s3_path}/{filename}.jsonl", how) as f:
        f.write(f"{json.dumps(data)}\n")


def current_time() -> str:
    """Return the current time as a string. Used as part of the session UUID."""
    # Get current date and time
    current_datetime = datetime.now()

    # Convert to a long number format
    datetime_string = current_datetime.strftime("%Y%m%d%H%M%S")

    return datetime_string
