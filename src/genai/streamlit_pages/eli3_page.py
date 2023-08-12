import streamlit as st

from genai import MessageTemplate
from genai.eyfs import ActivityGenerator


def eli3() -> None:
    """Explain me a concept like I'm 3."""
    st.title("Explain like I am a three year old")

    # Create the generator
    with st.sidebar:
        selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"])
        temperature = st.slider(label="**Temperature**", min_value=0.0, max_value=2.0, value=0.6, step=0.1)

    st.session_state["openai_model"] = selected_model
    st.session_state["temperature"] = temperature

    st.write(st.session_state["openai_model"])
    st.write(st.session_state["temperature"])

    message = MessageTemplate.load("src/genai/eli3/prompts/eli3.json")

    # if "messages" not in st.session_state:
    #     st.session_state.messages = [message]

    # for message in st.session_state.messages[1:]:
    #     try:
    #         with st.chat_message(message.role):
    #             st.markdown(message.content)
    #     except:
    #         pass
    #
    # for message in st.session_state.messages:
    #     st.write("Here 2")
    #     with st.chat_message(message["role"]):
    #         st.write("Here 3")
    #         st.markdown(message["content"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.write("Here 1")

    for message in st.session_state.messages:
        st.write("Here 2")
        with st.chat_message(message.role):
            st.write("Here 3")
            st.markdown(message.content)

    if prompt := st.chat_input("What is up?"):
        msg = MessageTemplate.load({"role": "user", "content": prompt})
        st.session_state.messages.append(msg)

        with st.chat_message("user"):
            st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            messages_placeholders = {
                "input": "msg.content",
            }
        except UnboundLocalError:
            messages_placeholders = {
                "input": "",
            }

        for m in st.session_state.messages:
            st.text(m)

        r = ActivityGenerator.generate(
            model=st.session_state["openai_model"],
            temperature=st.session_state["temperature"],
            messages=[MessageTemplate(role=m.role, content=m.content) for m in st.session_state.messages],
            message_kwargs=messages_placeholders,
            stream=True,
        )

        for response in r:
            full_response += response.choices[0].delta.get("content", "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append(MessageTemplate.load({"role": "assistant", "content": full_response}))

    # st.write(f"""END {st.session_state.messages}""")
    # # Get the user input
    # question = st.text_input(
    #     label="**Question**",
    #     value="How can whales breath in water?",
    #     help="Ask the large language model a question.",
    # )

    # # Generate the answer
    # if st.button(label="**Generate**", help="Generate an answer."):
    #     res_box = st.empty()
    #     report = []
    # messages_placeholders = {
    #     "input": question,
    # }

    # r = ActivityGenerator.generate(
    #     model=selected_model,
    #     temperature=temperature,
    #     messages=[message],
    #     message_kwargs=messages_placeholders,
    #     stream=True,
    # )

    #     for chunk in r:
    #         content = chunk["choices"][0].get("delta", {}).get("content")
    #         report.append(content)
    #         if chunk["choices"][0]["finish_reason"] != "stop":
    #             result = "".join(report).strip()
    #             res_box.markdown(f"{result}")
