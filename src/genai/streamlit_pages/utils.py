import streamlit as st


def delete_messages_state(key: str) -> None:
    """Delete the messages state."""
    try:
        del st.session_state["messages"]
    except KeyError:
        pass
