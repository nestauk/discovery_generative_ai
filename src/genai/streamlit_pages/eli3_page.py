import streamlit as st

from genai import MessageTemplate
from genai.eyfs import TextGenerator
from genai.streamlit_pages.utils import reset_state


def eli3() -> None:
    """Explain me a concept like I'm 3."""
    st.title("Explain like I am a three year old")

    # Create the generator
    with st.sidebar:
        selected_model = st.radio(
            label="**OpenAI model**",
            options=["gpt-3.5-turbo", "gpt-4"],
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

    prompt_template = MessageTemplate.load("src/genai/eli3/prompts/eli3_chat_2.json")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": prompt_template.role, "content": prompt_template.content}]

    # Display chat messages from history on app rerun.
    # The first message is the prompt, so we skip it.
    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    prompt = st.chat_input("How do whales breath?")
    if prompt:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

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
        st.session_state.messages.append({"role": "assistant", "content": full_response})
