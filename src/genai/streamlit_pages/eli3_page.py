import streamlit as st

from genai import MessageTemplate
from genai.eyfs import ActivityGenerator


def eli3() -> None:
    """Explain me a concept like I'm 3."""
    st.title("Explain like I am a three year old")

    # Create the generator
    with st.sidebar:
        selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"])
        temperature = st.slider(label="**Temperature**", min_value=0.0, max_value=2.0, value=0.6, step=0.1)

    message = MessageTemplate.load("src/genai/eli3/prompts/eli3.json")

    # Get the user input
    question = st.text_input(
        label="**Question**",
        value="How can whales breath in water?",
        help="Ask the large language model a question.",
    )

    # Generate the answer
    if st.button(label="**Generate**", help="Generate an answer."):
        messages_placeholders = {
            "input": question,
        }

        r = ActivityGenerator.generate(
            model=selected_model,
            temperature=temperature,
            messages=[message],
            message_kwargs=messages_placeholders,
        )

        st.write(r)
