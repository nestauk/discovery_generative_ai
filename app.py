"""Streamlit app for the Generative AI prototypes."""

import os

import openai
import streamlit as st

from dotenv import load_dotenv
from streamlit_option_menu import option_menu

from genai.streamlit_pages import early_year_activity_plan
from genai.streamlit_pages import eli3
from genai.streamlit_pages import eyfs_compare
from genai.streamlit_pages import eyfs_dm_kb
from genai.streamlit_pages import eyfs_kb_bbc
from genai.streamlit_pages import parenting_chatbot
from genai.streamlit_pages.utils import reset_state


load_dotenv()


def auth_openai() -> None:
    """Authenticate with OpenAI."""
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
    except Exception:
        openai.api_key = st.secrets["OPENAI_API_KEY"]


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


def main() -> None:
    """Run the app."""
    auth_openai()
    with st.sidebar:
        selected = option_menu(
            "Prototypes",
            [
                "Home page",
                "ELI3",
                "EYFS-based activities",
                "EYFS-based activities + BBC activities",
                "EYFS prototypes comparison",
                "Development Matters prototype",
                "Parenting Chatbot",
            ],
            default_index=0,
            on_change=reset_state,
            key="menu_selection",
        )
    if selected == "Home page":
        st.title("Nesta Discovery: Generative AI Prototypes")
        st.write("Welcome to the Nesta Discovery Generative AI prototypes. Please select a prototype from the menu.")
    elif selected == "ELI3":
        eli3()
    elif selected == "EYFS-based activities":
        early_year_activity_plan()
    elif selected == "EYFS-based activities + BBC activities":
        eyfs_kb_bbc()
    elif selected == "EYFS prototypes comparison":
        eyfs_compare()
    elif selected == "Development Matters prototype":
        eyfs_dm_kb()
    elif selected == "Parenting Chatbot":
        parenting_chatbot()


# if check_password():
# main()
main()
