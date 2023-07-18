"""Streamlit app for the Generative AI prototypes."""

from os import listdir
from os.path import isfile
from os.path import join

import streamlit as st

from streamlit_option_menu import option_menu

from genai.eli3 import TextGenerator


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
        help="Ask the LLM a question.",
    )

    # Generate the answer
    if st.button(label="**Generate**", help="Generate an answer."):
        answer = generator.generate(question, prompt=prompt)
        st.write(answer)


def early_year_activity_plan() -> None:
    """Come up with activities for children."""
    st.title("Generating activity plans grounded in EY foundation stages")

    # Create the generator
    selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"])

    list_of_prompts = get_prompts(prompts_dir="src/genai/ey_activity_plan/prompts/")

    prompt_selector = st.selectbox(
        label="**Pick a prompt or write a custom one**", options=list_of_prompts + ["Custom"]
    )

    if prompt_selector == "Custom":
        generator = load_llm(
            path_to_prompt="src/genai/ey_activity_plan/prompts/early_year_activity_plan.json",
            selected_model=selected_model,
        )
        prompt = st.text_area("Write your own prompt", value=generator.prompt_template.template)
    else:
        generator = load_llm(
            path_to_prompt=prompt_selector,
            selected_model=selected_model,
        )
        prompt = None
        with st.expander("**Inspect the prompt**"):
            # newlines are messed up https://github.com/streamlit/streamlit/issues/868
            st.write(generator.prompt_template.template)

    # Get the user input
    question = st.text_input(
        label="**How can I help you?**",
        value="A kid came into my lesson talking about having found a snail in their garden at the weekend.",
        help="Prompt the LLM with a some text and it will generate an activity plan for you.",
    )

    # Generate the answer
    if st.button(label="**Generate**", help="Generate an answer."):
        answer = generator.generate(question, prompt=prompt)
        st.write(answer)


def get_prompts(prompts_dir: str) -> list:
    """Get all the prompts from a directory."""
    return [join(prompts_dir, f) for f in listdir(prompts_dir) if isfile(join(prompts_dir, f))]


def load_llm(path_to_prompt: str, selected_model: str) -> TextGenerator:
    """Load the LLM."""
    try:
        generator = TextGenerator(
            path=path_to_prompt,
            model_name=selected_model,
        )
    except Exception:  # Dirty hack to work with local secrets and not break the app on Streamlit Share
        generator = TextGenerator(
            api_key=st.secret("OPENAI_API_KEY"),
            path=path_to_prompt,
            model_name=selected_model,
        )

    return generator


if check_password():
    main()
