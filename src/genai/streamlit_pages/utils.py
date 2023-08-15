from typing import Optional

import streamlit as st


def reset_state(key: Optional[str] = None) -> None:
    """Delete the message placeholder state."""
    keys = ["areas_of_learning_text", "areas_of_learning", "n_results", "location", "messages", "choice", "choices"]
    for key in keys:
        try:
            del st.session_state[key]
        except KeyError:
            pass
