import streamlit as st

from genai.message_history import InMemoryMessageHistory
from genai.message_history import TokenCounter
from genai.prompt_template import MessageTemplate
from genai.streamlit_pages.utils import reset_state


def parenting_chatbot() -> None:
    st.title("Parenting Chatbot")

    model_name = "gpt-3.5-turbo"
    max_tokens = 100

    with st.sidebar:
        st.button("Reset chat", on_click=reset_state, type="primary", help="Reset the chat history")
        if st.button("Clear memory", type="primary", help="Reset the chat history"):
            st.session_state["memory"].clear_messages()

    system_message = MessageTemplate(role="system", content="You are a good bot.")

    if "memory" not in st.session_state:
        # instantiate the memory instead of None
        st.session_state["memory"] = InMemoryMessageHistory()
        st.session_state["memory"].add_message(system_message.to_prompt())

    if "messages" not in st.session_state:
        # instantiate the memory instead of None
        st.session_state["messages"] = [{"role": "assistant", "content": "You are a good bot."}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    prompt = st.chat_input("What's on your mind?")
    if prompt:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state["memory"].add_message({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            full_response = "I'm a confused bot."
            # for response in ActivityGenerator.generate(
            #     model=selected_model,
            #     temperature=temperature,
            #     messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            #     message_kwargs=None,
            #     stream=True,
            # ):
            #     full_response += response.choices[0].delta.get("content", "")
            #     message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state["memory"].add_message({"role": "assistant", "content": full_response})

    # st.write(f"Messages: {st.session_state['messages']}")
    st.write(st.session_state["memory"].get_messages(model_name=model_name, max_tokens=max_tokens))
