"""Streamlit app for the Generative AI prototypes."""

import streamlit as st

from streamlit_option_menu import option_menu

from genai.eli3 import TextGenerator


APP_TITLE = "Nesta Discovery: Generative AI Prototypes"

with st.sidebar:
    selected = option_menu("Prototypes", ["Home page", "ELI3", "Dummy"], default_index=1)


def main() -> None:
    """Run the main chunk of the streamlit app."""
    if selected == "Home page":
        st.title(APP_TITLE)
        st.write("Welcome to the Nesta Discovery Generative AI prototypes.")
    elif selected == "ELI3":
        eli3()
    elif selected == "Dummy":
        st.title("Dummy prototype")


def eli3() -> None:
    """Explain me a concept like I'm 3."""
    st.title("ELI3 prototype")

    # Create the generator
    selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"])
    generator = TextGenerator(path="src/genai/eli3/prompts/eli3.json", model_name=selected_model)

    # Get the user input
    question = st.text_input(
        label="**Question**",
        value="How can whales breath in water?",
        help="Ask the LLM a question.",
    )

    # Generate the answer
    if st.button(label="Generate", help="Generate an answer."):
        answer = generator.generate(question)
        st.write(answer)


main()
