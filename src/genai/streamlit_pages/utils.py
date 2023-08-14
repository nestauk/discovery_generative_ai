from typing import Optional

import streamlit as st


def delete_messages_state(key: Optional[str] = None) -> None:
    """Delete the messages state."""
    try:
        del st.session_state["messages"]
    except KeyError:
        pass
