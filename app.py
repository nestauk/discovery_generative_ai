"""Streamlit app for the Generative AI prototypes."""

import os

from typing import Dict
from typing import List

import openai
import streamlit as st

from dotenv import load_dotenv
from streamlit_option_menu import option_menu

from genai.eli3 import TextGenerator


load_dotenv()


APP_TITLE = "Nesta Discovery: Generative AI Prototypes"


def main() -> None:
    """Run the app."""
    with st.sidebar:
        selected = option_menu("Prototypes", ["Home page", "ELI3", "EYFS-based activity plan"], default_index=0)
    if selected == "Home page":
        st.title(APP_TITLE)
        st.write("Welcome to the Nesta Discovery Generative AI prototypes. Please select a prototype from the menu.")
    elif selected == "ELI3":
        eli3()
    elif selected == "EYFS-based activity plan":
        early_year_activity_plan()


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


def eli3() -> None:
    """Explain me a concept like I'm 3."""
    st.title("ELI3 prototype")

    # Create the generator
    selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"])
    try:
        generator = TextGenerator(
            path="src/genai/eli3/prompts/eli3.json",
            model_name=selected_model,
        )
    except Exception:  # Dirty hack to work with local secrets and not break the app on Streamlit Share
        generator = TextGenerator(
            api_key=st.secret("OPENAI_API_KEY"),
            path="src/genai/eli3/prompts/eli3.json",
            model_name=selected_model,
        )

    prompt_selector = st.radio(label="**Generate with custom prompt**", options=["Default", "Custom"])

    if prompt_selector == "Custom":
        prompt = st.text_area("Write your own prompt", value=generator.prompt_template.template)
    else:
        prompt = None

    # Get the user input
    question = st.text_input(
        label="**Question**",
        value="How can whales breath in water?",
        help="Ask the LLM a question.",
    )

    # Generate the answer
    if st.button(label="**Generate**", help="Generate an answer."):
        answer = generator.generate(question, prompt=prompt)
        st.write(answer)


def early_year_activity_plan() -> None:
    """Come up with activities for children."""
    st.title("Generating activity plans grounded in EY foundation stages")
    auth_openai()

    areas_of_learning_desc = {
        "Communication and Language": """##Communication and Language##\nThe development of children’s spoken language underpins all seven areas of learning and development. Children’s back-and-forth interactions from an early age form the foundations for language and cognitive development. The number and quality of the conversations they have with adults and peers throughout the day in a language-rich environment is crucial. By commenting on what children are interested in or doing, and echoing back what they say with new vocabulary added, practitioners will build children's language effectively. Reading frequently to children, and engaging them actively in stories, non-fiction, rhymes and poems, and then providing them with extensive opportunities to use and embed new words in a range of contexts, will give children the opportunity to thrive. Through conversation, story-telling and role play, where children share their ideas with support and modelling from their teacher, and sensitive questioning that invites them to elaborate, children become comfortable using a rich range of vocabulary and language structures.""",
        "Personal, Social and Emotional Development": """##Personal, Social and Emotional Development##\nChildren’s personal, social and emotional development (PSED) is crucial for children to lead healthy and happy lives, and is fundamental to their cognitive development. Underpinning their personal development are the important attachments that shape their social world. Strong, warm and supportive relationships with adults enable children to learn how to understand their own feelings and those of others. Children should be supported to manage emotions, develop a positive sense of self, set themselves simple goals, have confidence in their own abilities, to persist and wait for what they want and direct attention as necessary. Through adult modelling and guidance, they will learn how to look after their bodies, including healthy eating, and manage personal needs independently. Through supported interaction with other children, they learn how to make good friendships, co-operate and resolve conflicts peaceably. These attributes will provide a secure platform from which children can achieve at school and in later life.""",
        "Physical Development": """##Physical Development##\nPhysical activity is vital in children’s all-round development, enabling them to pursue happy, healthy and active lives7. Gross and fine motor experiences develop incrementally throughout early childhood, starting with sensory explorations and the development of a child’s strength, co-ordination and positional awareness through tummy time, crawling and play movement with both objects and adults. By creating games and providing opportunities for play both indoors and outdoors, adults can support children to develop their core strength, stability, balance, spatial awareness, co-ordination and agility. Gross motor skills provide the foundation for developing healthy bodies and social and emotional well-being. Fine motor control and precision helps with hand-eye co-ordination, which is later linked to early literacy. Repeated and varied opportunities to explore and play with small world activities, puzzles, arts and crafts and the practice of using small tools, with feedback and support from adults, allow children to develop proficiency, control and confidence.""",
        "Literacy": """##Literacy##\nIt is crucial for children to develop a life-long love of reading. Reading consists of two dimensions: language comprehension and word reading. Language comprehension (necessary for both reading and writing) starts from birth. It only develops when adults talk with children about the world around them and the books (stories and non-fiction) they read with them, and enjoy rhymes, poems and songs together. Skilled word reading, taught later, involves both the speedy working out of the pronunciation of unfamiliar printed words (decoding) and the speedy recognition of familiar printed words. Writing involves transcription (spelling and handwriting) and composition (articulating ideas and structuring them in speech, before writing).""",
        "Mathematics": """##Mathematics##\nDeveloping a strong grounding in number is essential so that all children develop the necessary building blocks to excel mathematically. Children should be able to count confidently, develop a deep understanding of the numbers to 10, the relationships between them and the patterns within those numbers. By providing frequent and varied opportunities to build and apply this understanding - such as using manipulatives, including small pebbles and tens frames for organising counting - children will develop a secure base of knowledge and vocabulary from which mastery of mathematics is built. In addition, it is important that the curriculum includes rich opportunities for children to develop their spatial reasoning skills across all areas of mathematics including shape, space and measures. It is important that children develop positive attitudes and interests in mathematics, look for patterns and relationships, spot connections, ‘have a go’, talk to adults and peers about what they notice and not be afraid to make mistakes.""",
        "Understanding the World": """##Understanding the World##\nUnderstanding the world involves guiding children to make sense of their physical world and their community. The frequency and range of children’s personal experiences increases their knowledge and sense of the world around them – from visiting parks, libraries and museums to meeting important members of society such as police officers, nurses and firefighters. In addition, listening to a broad selection of stories, non-fiction, rhymes and poems will foster their understanding of our culturally, socially, technologically and ecologically diverse world. As well as building important knowledge, this extends their familiarity with words that support understanding across domains. Enriching and widening children’s vocabulary will support later reading comprehension.""",
        "Expressive Arts and Design": """##Expressive Arts and Design##\nThe development of children’s artistic and cultural awareness supports their imagination and creativity. It is important that children have regular opportunities to engage with the arts, enabling them to explore and play with a wide range of media and materials. The quality and variety of what children see, hear and participate in is crucial for developing their understanding, self-expression, vocabulary and ability to communicate through the arts. The frequency, repetition and depth of their experiences are fundamental to their progress in interpreting and appreciating what they hear, respond to and observe.""",
    }

    with st.sidebar:
        # Create the generator
        selected_model = st.radio(label="**OpenAI model**", options=["gpt-3.5-turbo", "gpt-4"])
        # n_results = st.slider(label="**Number of results**", min_value=1, max_value=10, value=5, step=1)

        description = "<THIS IS WHERE THE GENERATOR WILL SHOW THE RESULTS>"
        n_results = 10

        temperature = st.slider(label="**Temperature**", min_value=0.0, max_value=1.0, value=0.0, step=0.1)

    aol = [
        "Communication and Language",
        "Personal, Social and Emotional Development",
        "Physical Development",
        "Literacy",
        "Mathematics",
        "Understanding the World",
        "Expressive Arts and Design",
    ]
    areas_of_learning = st.multiselect(label="**Areas of learning**", options=aol, default=aol)
    areas_of_learning_text = [v for k, v in areas_of_learning_desc.items() if k in areas_of_learning]
    with st.expander("**Areas of Learning Description**"):
        for k, v in areas_of_learning_desc.items():
            if k in areas_of_learning:
                st.write(f"#### {k}")
                st.write(v.split("##")[-1])

    areas_of_learning_text = "\n\n".join(areas_of_learning_text)
    # difficulty = st.selectbox(label="**Activity difficulty**", options=["Easy", "Medium", "Hard"], index=1)
    location = st.selectbox(label="**Location**", options=["Indoor", "Outdoor", "Indoor or Outdoor"], index=2)

    messages = [
        {
            "role": "system",
            "content": "You are a very creative and highly educated assistant who loves designing early year education programmes.",
        },
        {
            "role": "user",
            "content": f"""###Context###The UK's Early Years Foundation Stage framework recommends that educational programmes must involve activities and experiences for children, as set out under each of the areas of learning described below.\n\n##Areas of Learning###\n{areas_of_learning_text}\n\n###Instructions###\nI am an early years educator and I am working with children 3-4 years old. I will describe you a situation in the ###Description### section. Please propose conversations and activities I could do with the children to extend their learning.\n\nTypes of activities:\n- Conversations: Asking them questions about the topic\n- Puzzles, games, role play, arts and crafts\n\n###Formatting###\nReturn the proposed activities in the following format:\n\n## Conversations\n### <activity_name>\n\n**Activity description**:<activity_description>\n\n**Areas of learning**:<list_of_areas_of_learning>\n\n### <activity_name>\n\n**Activity description**:<activity_description>\n\n**Areas of learning**:<list_of_areas_of_learning>\n\n## Games and Crafts\n### <activity_name>\n\n**Activity description**:<activity_description>\n\n**Areas of learning**:<list_of_areas_of_learning>\n\n### <activity_name>\n\n**Activity description**:<activity_description>\n\n**Areas of learning**:<list_of_areas_of_learning>\n""",  # noqa: B950
        },
        {
            "role": "user",
            "content": f"###Requirements for the activities###\n1. Your suggestions must be fun and engaging for the children.\n2. Your suggestions must be novel, inspiring and memorable.\n3. You must suggest topics for conversation with the children and questions to ask them.\n4. Your proposed activities engage children in the following Areas of Learning: {areas_of_learning}.\n5. You must generate {n_results} activities.\n6. Your proposed activities must be played {location}",  # noqa: B950
        },
    ]

    selected_system_messages = "".join(get_messages_by_role(messages, role="system"))
    selected_user_messages = {"Default": "\n\n".join(get_messages_by_role(messages, role="user"))}

    prompt_selector = st.selectbox(
        label="**Pick a prompt or write a custom one**",
        options=["Default", "Custom"],
    )

    if prompt_selector == "Custom":
        user_message = st.text_area("**Write your own prompt**", value=selected_user_messages["Default"])
        messages = [{"role": "system", "content": selected_system_messages}, {"role": "user", "content": user_message}]
    else:
        with st.expander("**Inspect the default prompt**"):
            # newlines are messed up https://github.com/streamlit/streamlit/issues/868
            st.write(selected_system_messages)
            st.write(selected_user_messages["Default"])

    # Get the user input
    description = st.text_input(
        label="**What's the topic you want activities for?**",
        value="Let's create activities educating children on how whales breath",
        help="Prompt the LLM with a some text and it will generate an activity plan for you.",
    )

    # Generate the answer
    if st.button(label="**Generate**", help="Generate an answer."):
        with st.spinner("Generating activities..."):
            messages.append({"role": "user", "content": f"###Description###\n{description}\n\n###Activities###\n"})

            r = openai.ChatCompletion.create(
                model=selected_model,
                messages=messages,
                temperature=temperature,
            )

            st.write(r["choices"][0]["message"]["content"])


def get_messages_by_role(messages: List[Dict], role: str) -> list:
    """Get all user messages."""
    return [message["content"] for message in messages if message["role"] == role]


def auth_openai() -> None:
    """Authenticate with OpenAI."""
    try:
        openai.api_key = os.environ["OPENAI_API_KEY"]
    except Exception:
        openai.api_key = st.secrets["OPENAI_API_KEY"]


if check_password():
    main()
