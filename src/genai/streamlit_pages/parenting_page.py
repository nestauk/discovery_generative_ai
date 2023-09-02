import json
import uuid

from datetime import datetime

import s3fs
import streamlit as st

from dotenv import load_dotenv
from streamlit_feedback import streamlit_feedback

from genai.message_history import InMemoryMessageHistory
from genai.prompt_template import MessageTemplate
from genai.streamlit_pages.utils import reset_state


load_dotenv()


def parenting_chatbot(aws_key: str, aws_secret: str, s3_path: str) -> None:
    """Parenting chatbot."""
    st.title("Parenting Chatbot")

    # model_name = "gpt-3.5-turbo"
    # max_tokens = 100

    with st.sidebar:
        st.button("Reset chat", on_click=reset_state, type="primary", help="Reset the chat history")

        # if st.button("Show feedback", type="primary"):
        #     st.write(st.session_state["user_feedback"])

    system_message = MessageTemplate(role="system", content="You are a good bot.")

    if "session_uuid" not in st.session_state:
        st.session_state["session_uuid"] = f"{current_time()}-{str(uuid.uuid4())}"

    if "user_feedback" not in st.session_state:
        st.session_state["user_feedback"] = []

    if "feedback" not in st.session_state:
        st.session_state["feedback"] = None

    if "memory" not in st.session_state:
        st.session_state["memory"] = InMemoryMessageHistory()
        st.session_state["memory"].add_message(system_message.to_prompt())

    if "messages" not in st.session_state:
        # instantiate the memory instead of None
        st.session_state["messages"] = [{"role": "assistant", "content": "You are a good bot."}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    prompt = st.chat_input("What's on your mind?")
    if prompt:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state["memory"].add_message({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            full_response = "I'm a confused bot."

            # Submit feedback
            streamlit_feedback(
                feedback_type="faces",
                single_submit=False,
                optional_text_label="[Optional] Please provide an explanation",
                key="feedback",
            )

            # for response in ActivityGenerator.generate(
            #     model=selected_model,
            #     temperature=temperature,
            #     messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            #     message_kwargs=None,
            #     stream=True,
            # ):
            #     full_response += response.choices[0].delta.get("content", "")
            #     message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        st.session_state["memory"].add_message({"role": "assistant", "content": full_response})

    # st.write(f"Messages: {st.session_state['messages']}")
    # st.write(st.session_state["memory"].get_messages(model_name=model_name, max_tokens=max_tokens))
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
            f"{s3_path}/{st.session_state['session_uuid']}",
            "feedback",
            user_feedback,
        )

        write_to_s3(
            aws_key,
            aws_secret,
            f"{s3_path}/{st.session_state['session_uuid']}",
            "messages",
            st.session_state["memory"].messages,
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
