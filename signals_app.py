import copy
import json
import os
import uuid

from datetime import datetime
from typing import Union

import openai
import s3fs
import streamlit as st

from dotenv import load_dotenv

from genai import FunctionTemplate
from genai import MessageTemplate
from genai.eyfs import TextGenerator
from genai.message_history import InMemoryMessageHistory
from genai.message_history import TokenCounter


load_dotenv()

selected_model = "gpt-4-1106-preview"
# selected_model = "gpt-3.5-turbo-1106"
# selected_model = "gpt-4"
temperature = 0.000001

CHECK_COSTS = False

# Paths to prompts
PROMPT_PATH = "src/genai/sandbox/signals/data/"
PATH_SIGNALS_DATA = PROMPT_PATH + "signals_2024.json"
PATH_SYSTEM = PROMPT_PATH + "00_system.jsonl"
PATH_INTRO = PROMPT_PATH + "01_intro.jsonl"
PATH_ACTIONS = PROMPT_PATH + "intent_actions.json"
PATH_ILLUSTRATIONS = "src/genai/sandbox/signals/illustrations/"

# Top signal function
path_func_top_signal = PROMPT_PATH + "func_top_signal.json"
path_prompt_top_signal = PROMPT_PATH + "prompt_top_signal.jsonl"
# Top three signals function
path_func_top_three_signals = PROMPT_PATH + "func_top_three_signals.json"
path_prompt_top_three_signals = PROMPT_PATH + "prompt_top_three_signals.jsonl"
# Intent detection function
path_func_intent = PROMPT_PATH + "func_intent.json"
path_prompt_intent = PROMPT_PATH + "prompt_intent.jsonl"
# Prompt: Impact on the user
path_prompt_impact = PROMPT_PATH + "02_signal_impact.jsonl"
# Prompt: Summary of different signals
path_prompt_choice = PROMPT_PATH + "03_signal_choice.jsonl"
# Prompt: Following up on user's question
path_prompt_following_up = PROMPT_PATH + "04_follow_up.jsonl"

aws_key = os.environ["AWS_ACCESS_KEY_ID"]
aws_secret = os.environ["AWS_SECRET_ACCESS_KEY"]
s3_path = os.environ["S3_BUCKET"]


def auth_openai() -> None:
    """Authenticate with OpenAI."""
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
    except Exception:
        openai.api_key = st.secrets["OPENAI_API_KEY"]


def read_jsonl(path: str) -> list:
    """Read a JSONL file."""
    with open(path, "r") as f:
        return [json.loads(line) for line in f.readlines()]


def generate_signals_texts(signals_data: dict, chosen_signals: list = None) -> str:
    """
    Generate a description of the signals.

    Args:
        signals_data (dict): A dictionary of signals data.
        chosen_signals (list, optional): A list of signals to include in the description. Defaults to None.

    Returns:
        str: A description of the signals.
    """
    signals = [signal["short_name"] for signal in signals_data]
    signals_titles = [signal["title"] for signal in signals_data]
    signals_summaries = [signal["summary"] for signal in signals_data]

    if chosen_signals is None:
        chosen_signals = signals

    # Combine titles and summaries into a single string
    signals_description = ""
    for short_name, title, summary in zip(signals, signals_titles, signals_summaries):
        if short_name in chosen_signals:
            signals_description += f"Signal '{short_name}': {title}\n{summary}\n\n"

    return signals_description


def generate_action_texts(action_data: dict, active_signal: str = None) -> str:
    """
    Generate a description of the actions.

    Args:
        action_data (dict): A dictionary of actions data.
        active_signal (str, optional): The active signal. Defaults to None.

    Returns:
        str: A description of the actions.

    """
    actions = [a["name"] for a in action_data]
    action_descriptions = [a["description"] for a in action_data]
    action_text = ""
    for name, description in zip(actions, action_descriptions):
        if (name != "following_up") or (active_signal is None):
            action_text += f"Action '{name}': {description}\n\n"
        else:
            action_text += f"Action '{name}': User is following up with another question about the {active_signal} signal that's being discussed just now.\n\n"  # noqa: B950

    return action_text


# Prepare the data
signals_data = json.load(open(PATH_SIGNALS_DATA, "r"))
signals_dict = {s["short_name"]: s for s in signals_data}
signals_descriptions = generate_signals_texts(signals_data)
signals = [s["short_name"] for s in signals_data]

actions_data = json.load(open(PATH_ACTIONS, "r"))
actions_descriptions = generate_action_texts(actions_data)
actions = [a["name"] for a in actions_data]


def predict_intent(user_message: str, active_signal: str) -> str:
    """Detect the intent of the user's message.

    Args:
        user_message (str): The user's message.
        messages (list): The history of messages.

    Returns:
        str: The intent of the user's message. Possible outputs are:
            - "explain": The user wants to know more about a signal.
            - "more_signals": The user wants to know more about a signal.
            - "follow_up": The user wants to know more about a signal.
            - "next_steps": The user wants to know more about a signal.
            - "none": The user's message does not match any intent.
    """
    func_intent = json.loads(open(path_func_intent).read())
    message_history = [MessageTemplate.load(m) for m in st.session_state.messages]
    message = MessageTemplate.load(path_prompt_intent)
    all_messages = message_history + [message]
    function = FunctionTemplate.load(func_intent)
    response = TextGenerator.generate(
        model=selected_model,
        temperature=temperature,
        messages=all_messages,
        message_kwargs={
            "intents": generate_action_texts(actions_data, active_signal=active_signal),
            "user_input": user_message,
        },
        stream=False,
        functions=[function.to_prompt()],
        function_call={"name": "predict_intent"},
    )
    intent = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])

    if CHECK_COSTS:
        cost_input = (
            TokenCounter._count_tokens_from_messages(
                messages=[m.to_prompt() for m in all_messages], model_name=selected_model
            )
            * 0.01
            / 1000
        )
        print(f"Intent cost: {cost_input}")  # noqa: T001

    return intent["prediction"]


def predict_top_signal(user_message: str, signals: list) -> str:
    """Predict the top signal from the user's message.

    Args:
        user_message (str): The user's message.

    Returns:
        str: The top signal from the user's message.
    """
    # Function call
    func_top_signal = json.loads(open(path_func_top_signal).read())
    func_top_signal["parameters"]["properties"]["prediction"]["enum"] = signals

    message = MessageTemplate.load(path_prompt_top_signal)
    function = FunctionTemplate.load(func_top_signal)

    response = TextGenerator.generate(
        model=selected_model,
        temperature=temperature,
        messages=[message],
        message_kwargs={"signals": signals_descriptions, "user_input": user_message},
        stream=False,
        functions=[function.to_prompt()],
        function_call={"name": "predict_top_signal"},
    )
    top_signal = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
    return top_signal["prediction"]


def predict_top_three_signals(user_message: str, allowed_signals: list) -> list:
    """Predict the top signal from the user's message.

    Args:
        user_message (str): The user's message.

    Returns:
        str: The top signal from the user's message.
    """
    # Function call
    func_top_signals = json.loads(open(path_func_top_three_signals).read())
    func_top_signals["parameters"]["properties"]["prediction"]["items"]["enum"] = allowed_signals
    message = MessageTemplate.load(path_prompt_top_three_signals)
    function_top_three = FunctionTemplate.load(func_top_signals)

    signals_descriptions_ = generate_signals_texts(signals_data, allowed_signals)

    response = TextGenerator.generate(
        model=selected_model,
        temperature=temperature,
        messages=[message],
        message_kwargs={"signals": signals_descriptions_, "user_input": user_message},
        stream=False,
        functions=[function_top_three.to_prompt()],
        function_call={"name": "predict_top_signals"},
    )
    top_signals = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
    return top_signals["prediction"]


def signals_bot() -> None:
    """Explain me a concept like I'm 3."""

    # Define custom CSS
    custom_css = """
        <style>
        /* Adjust the selector as needed */
        .stHeadingContainer {
            margin-top: -100px; /* Reduce the top margin */
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {
            visibility: hidden
        }
        [data-testid="chatAvatarIcon-assistant"] {
            background-color: #A59BEE !important;
        }
        [data-testid="chatAvatarIcon-user"] {
            background-color: #97D9E3 !important;
        }

        html, body, [class*="st-"] {
            font-family: 'Averta', 'Avenir', "Source Sans Pro", sans-serif;
        }

        .stChatFloatingInputContainer {
            position: relative;
        }
        </style>
        """

    # Apply the custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)

    st.title("Personalised futures: let our chatbot guide you through our Future Signals for 2024")
    st.markdown(
        "Undoubtedly, the rise of generative artificial intelligence (AI) has been one of the main trends of 2023, with ChatGPT chosen as [the word of the year](https://www.economist.com/culture/2023/12/07/our-word-of-the-year-for-2023) by *The Economist*. Reflecting on this trend, we have built an experimental generative AI chatbot of our own to help you engage more deeply with our [Signals for 2024](https://www.nesta.org.uk/feature/future-signals-2024/).\n\nThis is an experiment in creating a more interactive reading experience using 2023's big new technology. **Scroll down** to meet our chatbot, Scout, which will try to relate this year's Signals to you and your life. You can provide a little information about yourself and Scout will try to come up with ways that these Signals might be relevant to you.\n\nScout also provides a signal of the potential new ways we might interact with information in the future, with customised bots helping us explore and synthesise reams of written text, data, charts and videos to find what matters the most to us.\n\n**Guidance**\n\n*The chatbot uses OpenAI's GPT-4, a cutting-edge AI model. Nesta does not save the conversations, and OpenAI claims to delete all data in 30 days. **Nonetheless, please do not share any information that could identify you or that is sensitive or confidential.** Please remember, this is an experimental chatbot; it can make mistakes and 'hallucinate' - [another word of the year](https://www.cam.ac.uk/research/news/cambridge-dictionary-names-hallucinate-word-of-the-year-2023) - or show biases despite our efforts to instruct it to be inclusive and sensitive. After trying out the chatbot, we invite you to leave us feedback using [this form](https://forms.gle/UWcnpgKg9WG7JmPt5).*\n\n**Meet Scout...**",  # noqa: B950
        unsafe_allow_html=True,  # noqa: B950
    )  # noqa: B950

    # First time running the app
    if "messages" not in st.session_state:
        # Record of messages to display on the app
        st.session_state.messages = []
        # Record of messages to send to the LLM
        st.session_state["memory"] = InMemoryMessageHistory()
        st.session_state["messages_intent"] = []
        st.session_state["messages_signal"] = []
        # Keep track of which state we're in
        st.session_state.state = "start"
        # Fetch system and introduction messages
        st.session_state.signals = []

        # Add system message to the history
        system_message = read_jsonl(PATH_SYSTEM)[0]
        system_message = MessageTemplate.load(system_message)
        system_message.format_message(**{"signals": signals_descriptions})
        st.session_state["memory"].add_message(system_message.to_prompt())
        # Add the intro messages
        intro_messages = read_jsonl(PATH_INTRO)
        for m in intro_messages:
            st.session_state.messages.append(m)
            st.session_state["memory"].add_message(m)
            st.session_state["messages_intent"].append("intro")
            st.session_state["messages_signal"].append("none")
        # Keep count of the number of unique sessions
        timestamp = current_time()
        st.session_state["session_log"] = f"{timestamp}-{str(uuid.uuid4())}"
        write_to_s3(
            key=aws_key,
            secret=aws_secret,
            s3_path=f"{s3_path}/session-logs-signals",
            filename="session_counter",
            data={"session": st.session_state["session_log"], "time": timestamp},
            how="a",
        )

    # Display chat messages on app rerun
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if st.session_state["messages_intent"][i] == "new_signal":
                signal_to_explain = st.session_state["messages_signal"][i]
                st.image(
                    PATH_ILLUSTRATIONS + signals_dict[signal_to_explain]["img"],
                    caption="Illustration by Chen Wu",
                    use_column_width=True,
                )
            st.markdown(message["content"])

    # Get user message
    user_message = st.chat_input("")
    if user_message:
        updated_css = """
            <style>
            .stChatFloatingInputContainer {
                position: fixed;
            }
            </style>
            """
        st.markdown(updated_css, unsafe_allow_html=True)
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_message)
        st.session_state.messages.append({"role": "user", "content": user_message})
        st.session_state["memory"].add_message({"role": "user", "content": user_message})
        st.session_state["messages_intent"].append("user")
        st.session_state["messages_signal"].append("none")
        if st.session_state.state == "start":
            intent = "new_signal"
            st.session_state.user_info = user_message
            st.session_state.state = "chatting"
        else:
            intent = predict_intent(user_message, active_signal=st.session_state.active_signal)

        if intent == "new_signal":
            # Filter out signals that have already been covered
            allowed_signals = [s for s in signals if s not in st.session_state.signals]
            # Determine the most relevant signal to explain
            signal_to_explain = predict_top_signal(user_message, allowed_signals)
            # Keep track of already discussed signals
            st.session_state.signals.append(signal_to_explain)
            st.session_state.active_signal = signal_to_explain
            # Generate a message about the signal
            instruction = MessageTemplate.load(path_prompt_impact)
            message_history = st.session_state["memory"].get_messages(max_tokens=3000) + [instruction]
            with st.chat_message("assistant"):
                # Show the signal image
                st.image(
                    PATH_ILLUSTRATIONS + signals_dict[signal_to_explain]["img"],
                    caption="Illustration by Chen Wu",
                    use_column_width=True,
                )
                # Type the response
                full_response = llm_call(
                    selected_model,
                    temperature,
                    messages=message_history,
                    messages_placeholders={
                        "signal": signals_dict[signal_to_explain]["full_text"],
                        "user_input": st.session_state.user_info,
                    },
                )
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state["memory"].add_message({"role": "assistant", "content": full_response})
                st.session_state["messages_intent"].append(copy.deepcopy(intent))
                st.session_state["messages_signal"].append(copy.deepcopy(signal_to_explain))

        elif intent == "more_signals":
            # Filter out signals that have already been covered
            allowed_signals = [s for s in signals if s not in st.session_state.signals]
            # Determine the top three signals to explain
            top_signals = predict_top_three_signals(st.session_state.user_info, allowed_signals)
            top_signals_text = generate_signals_texts(signals_data, top_signals)
            # Generate a message about the three signals
            instruction = MessageTemplate.load(path_prompt_choice)
            message_history = st.session_state["memory"].get_messages(max_tokens=3000) + [instruction]
            with st.chat_message("assistant"):
                full_response = llm_call(
                    selected_model,
                    temperature,
                    messages=message_history,
                    messages_placeholders={"signals": top_signals_text, "user_input": st.session_state.user_info},
                )
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state["memory"].add_message({"role": "assistant", "content": full_response})
                st.session_state["messages_intent"].append(copy.deepcopy(intent))
                st.session_state["messages_signal"].append("none")

        elif intent == "following_up":
            # Generate follow up message
            instruction = MessageTemplate.load(path_prompt_following_up)
            message_history = st.session_state["memory"].get_messages(max_tokens=3000) + [instruction]
            with st.chat_message("assistant"):
                full_response = llm_call(
                    selected_model,
                    temperature,
                    messages=message_history,
                    messages_placeholders={
                        "signal": signals_dict[st.session_state.active_signal]["full_text"],
                        "user_input": user_message,
                    },
                )
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state["memory"].add_message({"role": "assistant", "content": full_response})
                st.session_state["messages_intent"].append(copy.deepcopy(intent))
                st.session_state["messages_signal"].append("none")

        if CHECK_COSTS:
            # Keep track of the number of messages
            def transform_message(m: Union[MessageTemplate, dict]) -> dict:
                """Transform all messages to dictionary format (quick hack)"""
                try:
                    return m.to_prompt()
                except AttributeError:
                    return m

            cost_input = (
                TokenCounter._count_tokens_from_messages(
                    messages=[transform_message(m) for m in message_history], model_name=selected_model
                )
                * 0.01
                / 1000
            )
            cost_output = (
                TokenCounter._count_tokens_from_messages(
                    messages=[{"role": "assistant", "content": full_response}], model_name=selected_model
                )
                * 0.03
                / 1000
            )
            cost_total = cost_input + cost_output
            print(f"Total cost: {cost_total}")  # noqa: T001

        write_to_s3(
            key=aws_key,
            secret=aws_secret,
            s3_path=f"{s3_path}/session-logs-signals",
            filename="message_counter",
            data={
                "session": st.session_state["session_log"],
                "time": current_time(),
                "intent": intent,
                "signal": st.session_state.active_signal,
            },
            how="a",
        )


def llm_call(selected_model: str, temperature: float, messages: MessageTemplate, messages_placeholders: dict) -> str:
    """Call the LLM"""
    message_placeholder = st.empty()
    full_response = ""
    for response in TextGenerator.generate(
        model=selected_model,
        temperature=temperature,
        messages=messages,
        message_kwargs=messages_placeholders,
        stream=True,
    ):
        full_response += response.choices[0].delta.get("content", "")
        message_placeholder.markdown(full_response + "▌")

    message_placeholder.markdown(full_response)

    return full_response


def write_to_s3(key: str, secret: str, s3_path: str, filename: str, data: dict, how: str = "a") -> None:
    """Write data to a jsonl file in S3.

    Parameters
    ----------
    key
        AWS access key ID.

    secret
        AWS secret access key.

    s3_path
        S3 bucket path.

    filename
        Name of the file to write to.

    data
        Data to write to the file.

    how
        How to write to the file. Default is "a" for append. Use "w" to overwrite.

    """
    fs = s3fs.S3FileSystem(key=key, secret=secret)
    with fs.open(f"{s3_path}/{filename}.jsonl", how) as f:
        f.write(f"{json.dumps(data)}\n")


def current_time() -> str:
    """Return the current time as a string. Used as part of the session UUID."""
    # Get current date and time
    current_datetime = datetime.now()

    # Convert to a long number format
    datetime_string = current_datetime.strftime("%Y%m%d%H%M%S")

    return datetime_string


def main() -> None:
    """Run the app."""
    auth_openai()

    signals_bot()


main()
