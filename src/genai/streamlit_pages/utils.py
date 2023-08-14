from typing import Optional

import streamlit as st


def delete_messages_state(key: Optional[str] = None) -> None:
    """Delete the messages state."""
    try:
        del st.session_state["messages"]
        del st.session_state["areas_of_learning_text"]
        del st.session_state["areas_of_learning"]
        del st.session_state["n_results"]
        del st.session_state["location"]
    except KeyError:
        pass
