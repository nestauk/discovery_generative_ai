import random
import time

import openai
import streamlit as st

from genai import MessageTemplate
from genai.eyfs import ActivityGenerator


def chatbot():
    st.title("Simple chat")

    st.write(st.session_state.messages)
    # del st.session_state["messages"]
    prompt_template = MessageTemplate.load("src/genai/eli3/prompts/eli3.json")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": prompt_template.role, "content": prompt_template.content}]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages[1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    prompt = st.chat_input("Say something")
    if prompt:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in ActivityGenerator.generate(
                model="gpt-3.5-turbo",
                temperature=0.6,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                message_kwargs={"input": ""},
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})


# import openai
# import streamlit as st


# def chatbot():
#     st.title("ChatGPT-like clone")

#     if "openai_model" not in st.session_state:
#         st.session_state["openai_model"] = "gpt-3.5-turbo"

#     if "messages" not in st.session_state:
#         st.session_state.messages = []

#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     if prompt := st.chat_input("What is up?"):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.chat_message("assistant"):
#             message_placeholder = st.empty()
#             full_response = ""
#             for response in openai.ChatCompletion.create(
#                 model=st.session_state["openai_model"],
#                 messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
#                 stream=True,
#             ):
#                 full_response += response.choices[0].delta.get("content", "")
#                 message_placeholder.markdown(full_response + "▌")
#             message_placeholder.markdown(full_response)
#         st.session_state.messages.append({"role": "assistant", "content": full_response})

#     st.write(st.session_state.messages)
