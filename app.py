"""Streamlit app for the Generative AI prototypes."""

import os

import openai
import streamlit as st

from dotenv import load_dotenv
from streamlit_option_menu import option_menu

from genai.eli3 import TextGenerator
from genai.eyfs.eyfs import ActivityGenerator
from genai.utils import read_json


load_dotenv()


APP_TITLE = "Nesta Discovery: Generative AI Prototypes"


def main() -> None:
    """Run the app."""
    with st.sidebar:
        selected = option_menu("Prototypes", ["Home page", "ELI3", "EYFS-based activity plan"], default_index=0)
    if selected == "Home page":
        st.title(APP_TITLE)
        st.write("Welcome to the Nesta Discovery Generative AI prototypes. Please select a prototype from the menu.")
    elif selected == "ELI3":
        eli3()
    elif selected == "EYFS-based activity plan":
        early_year_activity_plan()


def check_password() -> bool:
    """Return `True` if the user had the correct password."""

    def password_entered() -> None:
        """Check whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.

        return True


def eli3() -> None:
    """Explain me a concept like I'm 3."""
    st.title("ELI3 prototype")

    # Create the generator
    selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"])
    try:
        generator = TextGenerator(
            path="src/genai/eli3/prompts/eli3.json",
            model_name=selected_model,
        )
    except Exception:  # Dirty hack to work with local secrets and not break the app on Streamlit Share
        generator = TextGenerator(
            api_key=st.secret("OPENAI_API_KEY"),
            path="src/genai/eli3/prompts/eli3.json",
            model_name=selected_model,
        )

    prompt_selector = st.radio(label="**Generate with custom prompt**", options=["Default", "Custom"])

    if prompt_selector == "Custom":
        prompt = st.text_area("Write your own prompt", value=generator.prompt_template.template)
    else:
        prompt = None

    # Get the user input
    question = st.text_input(
        label="**Question**",
        value="How can whales breath in water?",
        help="Ask the large language model a question.",
    )

    # Generate the answer
    if st.button(label="**Generate**", help="Generate an answer."):
        answer = generator.generate(question, prompt=prompt)
        st.write(answer)


def early_year_activity_plan() -> None:
    """Come up with activities for children."""
    st.title("Generating activity plans grounded in EY foundation stages")
    auth_openai()
    areas_of_learning_desc = read_json("src/genai/eyfs/areas_of_learning.json")
    aol = list(areas_of_learning_desc.keys())

    with st.sidebar:
        # Select a model, temperature and number of results
        selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"], index=1)
        description = "<THIS IS WHERE THE GENERATOR WILL SHOW THE RESULTS>"
        n_results = 10
        temperature = st.slider(label="**Temperature**", min_value=0.0, max_value=1.0, value=0.6, step=0.1)

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

    # Create the messages
    paths = [
        "src/genai/eyfs/prompts/system.json",
        "src/genai/eyfs/prompts/context_and_task.json",
        "src/genai/eyfs/prompts/constraints.json",
        "src/genai/eyfs/prompts/situation.json",
    ]

    messages = [read_json(path) for path in paths]

    # Get the user input
    description = st.text_input(
        label="**What's the topic you want activities for?**",
        value="Let's create activities educating children on how whales breath",
        help="Prompt the large language model with a some text and it will generate an activity plan for you.",
    )

    # Generate the answer
    if st.button(label="**Generate**", help="Generate an answer."):
        with st.spinner("Generating activities..."):
            messages_placeholders = {
                "description": description,
                "areas_of_learning": areas_of_learning,
                "n_results": n_results,
                "location": location,
                "areas_of_learning_text": areas_of_learning_text,
            }

            r = ActivityGenerator.generate(
                model=selected_model,
                temperature=temperature,
                messages=messages,
                message_kwargs=messages_placeholders,
            )

            st.write(r["choices"][0]["message"]["content"])


def auth_openai() -> None:
    """Authenticate with OpenAI."""
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
    except Exception:
        openai.api_key = st.secrets["OPENAI_API_KEY"]


if check_password():
    main()
