import streamlit as st

from genai import MessageTemplate
from genai.eyfs.eyfs import ActivityGenerator
from genai.streamlit_pages.utils import delete_messages_state
from genai.utils import read_json


def delete_message_placeholder_state() -> None:
    """Delete the message placeholder state."""
    try:
        del st.session_state["areas_of_learning_text"]
        del st.session_state["areas_of_learning"]
        del st.session_state["n_results"]
        del st.session_state["location"]
    except Exception:
        pass


def early_year_activity_plan() -> None:
    """Come up with activities for children."""
    st.title("Generating activity plans grounded in EY foundation stages")
    areas_of_learning_desc = read_json("src/genai/eyfs/areas_of_learning.json")
    aol = list(areas_of_learning_desc.keys())

    with st.sidebar:
        # Select a model, temperature and number of results
        selected_model = st.radio(
            label="**OpenAI model**",
            options=["gpt-3.5-turbo", "gpt-4"],
            index=1,
            on_change=delete_messages_state,
        )
        description = "<THIS IS WHERE THE GENERATOR WILL SHOW THE RESULTS>"
        n_results = 10
        temperature = st.slider(
            label="**Temperature**",
            min_value=0.0,
            max_value=2.0,
            value=0.6,
            step=0.1,
            on_change=delete_messages_state,
        )

    # Select the areas of learning
    areas_of_learning = st.multiselect(
        label="**Areas of learning**",
        options=aol,
        default=aol,
        on_change=delete_messages_state,
    )
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
        "src/genai/eyfs/prompts/context_and_task_chat.json",
        "src/genai/eyfs/prompts/constraints.json",
        # "src/genai/eyfs/prompts/situation.json",
    ]

    prompt_templates = [MessageTemplate.load(path) for path in paths]

    # # Get the user input
    # description = st.text_input(
    #     label="**What's the topic you want activities for?**",
    #     value="Let's create activities educating children on how whales breath",
    #     help="Prompt the large language model with a some text and it will generate an activity plan for you.",
    # )

    # keys = ["areas_of_learning", "n_results", "location", "areas_of_learning_text"]
    # if any(k not in st.session_state for k in keys):
    #     st.session_state.messages = [
    #         {"role": prompt_template.role, "content": prompt_template.content} for prompt_template in prompt_templates
    #     ]

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": prompt_template.role, "content": prompt_template.content} for prompt_template in prompt_templates
        ]

    # Display chat messages from history on app rerun.
    # The first message is the prompt, so we skip it.
    for message in st.session_state.messages[len(prompt_templates) :]:
        # for message in st.session_state.messages:
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

            # r = ActivityGenerator.generate(
            #     model=selected_model,
            #     temperature=temperature,
            #     messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            #     message_kwargs={
            #         "description": prompt,
            #         "areas_of_learning": areas_of_learning,
            #         "n_results": n_results,
            #         "location": location,
            #         "areas_of_learning_text": areas_of_learning_text,
            #     },
            #     stream=True,
            # )

            for response in ActivityGenerator.generate(
                model=selected_model,
                temperature=temperature,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                message_kwargs={
                    "description": prompt,
                    "areas_of_learning": areas_of_learning,
                    "n_results": n_results,
                    "location": location,
                    "areas_of_learning_text": areas_of_learning_text,
                },
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # # Generate the answer
    # if st.button(label="**Generate**", help="Generate an answer."):
    #     with st.spinner("Generating activities..."):
    #         res_box = st.empty()
    #         report = []
    # messages_placeholders = {
    #     "description": description,
    #     "areas_of_learning": areas_of_learning,
    #     "n_results": n_results,
    #     "location": location,
    #     "areas_of_learning_text": areas_of_learning_text,
    # }

    #         r = ActivityGenerator.generate(
    #             model=selected_model,
    #             temperature=temperature,
    #             messages=messages,
    #             message_kwargs=messages_placeholders,
    #             stream=True,
    #         )

    #         for chunk in r:
    #             content = chunk["choices"][0].get("delta", {}).get("content")
    #             report.append(content)
    #             if chunk["choices"][0]["finish_reason"] != "stop":
    #                 result = "".join(report).strip()
    #                 res_box.markdown(f"{result}")
