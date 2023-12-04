import json
import os

import openai
import streamlit as st

from dotenv import load_dotenv

from genai import MessageTemplate
from genai.eyfs import TextGenerator
from genai.streamlit_pages.utils import reset_state


load_dotenv()

data_path = "src/genai/sandbox/signals/data/"
signals_data = json.load(open(data_path + "signals_2023.json", "r"))


def auth_openai() -> None:
    """Authenticate with OpenAI."""
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
    except Exception:
        openai.api_key = st.secrets["OPENAI_API_KEY"]


def generate_signals_texts(signals_data: dict):
    signals_titles = [signal["title"] for signal in signals_data]
    signals_summaries = [signal["summary"] for signal in signals_data]

    # Combine titles and summaries into a single string
    signals_description = ""
    no = 0
    for title, summary in zip(signals_titles, signals_summaries):
        no += 1
        signals_description += f"Signal {no}: {title}\n{summary}\n\n"

    return signals_description


def signals_bot(sidebar: bool = True) -> None:
    """Explain me a concept like I'm 3."""

    # Define your custom CSS
    # custom_css = """
    #     <style>
    #         /* Adjust the selector as needed */
    #         .stHeadingContainer {
    #             margin-top: -100px; /* Reduce the top margin */
    #         }
    #         #MainMenu {visibility: hidden;}
    #         footer {visibility: hidden;}
    #         header {
    #             visibility: hidden
    #         }
    #     </style>
    #     """

    # # Apply the custom CSS
    # st.markdown(custom_css, unsafe_allow_html=True)

    signals_descriptions = generate_signals_texts(signals_data)

    selected_model = "gpt-3.5-turbo"
    temperature = 0.6

    st.title("Signals chatbot")
    st.write("Some text here")

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.state = "start"
        # Write first message
        with st.chat_message("assistant"):
            opening_message = "Hi! I'm the Signals chatbot. I'm here to help you find out more about the Signals project. Tell me about yourself"
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": "###Instructions###\nYou are a helpful, kind, intelligent and polite futurist. Your task is to engage the user about future signals by helping the user imagine and appreciate how the signals will impact their life. You will personalise the user experience by taking the information provided by the user and tailoring your explanation to the user background.",
                }
            )
            st.session_state.messages.append({"role": "assistant", "content": opening_message})

    # # add input form
    # input_name = st.text_input("What's your name", value="")
    # input_interest = st.text_input("What are you interested in?", placeholder="For example: education, sustainability or health?")
    # input_job = st.text_input("What's your job", value="")

    # Display chat messages from history on app rerun.
    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_message = st.chat_input("My name is Mark, I'm interested in education and I'm a teacher")
    if user_message:
        # Write user message
        with st.chat_message("user"):
            st.markdown(user_message)
        # Add user message to history
        prompt = prompt2()
        st.session_state.messages.append({"role": "user", "content": prompt.to_prompt()})
        print(user_message)
        # Generate AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in TextGenerator.generate(
                model=selected_model,
                temperature=temperature,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                message_kwargs=None,
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        # Add AI response to history
        st.session_state.messages.append({"role": "assistant", "content": full_response})


def llm_call(selected_model: str, temperature: float, message: MessageTemplate, messages_placeholders: dict) -> str:
    """Call the LLM"""
    message_placeholder = st.empty()
    full_response = ""
    for response in TextGenerator.generate(
        model=selected_model,
        temperature=temperature,
        messages=[message],
        message_kwargs=messages_placeholders,
        stream=True,
    ):
        full_response += response.choices[0].delta.get("content", "")
        message_placeholder.markdown(full_response + "▌")

    message_placeholder.markdown(full_response)

    return full_response


def prompt2():
    """
    Generate a prompt for an overview of the impact of signals on the user
    """
    prompt = MessageTemplate.load(data_path + "prompt2.json")
    return prompt


def main() -> None:
    """Run the app."""
    auth_openai()
    signals_bot(sidebar=False)


main()
