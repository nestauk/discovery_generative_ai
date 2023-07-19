import os

from typing import Optional
from typing import Union

from dotenv import load_dotenv
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.prompts import load_prompt
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate


load_dotenv()


class ActivityGenerator:
    """Generate text from a prompt."""

    def __init__(
        self,
        human_template: str,
        system_template: Union[str, None] = None,
        api_key: str = os.environ["OPENAI_API_KEY"],  # type: ignore
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> None:
        """Initialize the classifier."""
        # This assumes your OpenAI API key is stored in an environment variable
        self.chat = ChatOpenAI(
            openai_api_key=api_key,
            model_name=model_name,  # type: ignore
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )  # type: ignore

        # Load the prompt templates
        self.prompt_template = load_prompt(human_template)
        self.system_template = system_template

        if system_template:
            self.system_template = load_prompt(system_template)

    def build_prompt(self, prompt: Optional[str] = None) -> ChatPromptTemplate:
        """Build the prompt. If no prompt is provided, use the default prompt."""
        messages = []

        if self.system_template:
            messages.append(SystemMessagePromptTemplate(prompt=self.system_template))  # type: ignore

        # Build the prompt
        if prompt:
            p = PromptTemplate(input_variables=["input"], template=prompt)
            messages.append(HumanMessagePromptTemplate(prompt=p))
        else:
            messages.append(HumanMessagePromptTemplate(prompt=self.prompt_template))  # type: ignore

        chat_prompt = ChatPromptTemplate.from_messages(messages)

        return chat_prompt

    def generate(self, input: str, prompt: Optional[str] = None, **kwargs) -> str:
        """Generate text."""

        chat_prompt = self.build_prompt(prompt)
        # Run the prompt
        chain = LLMChain(llm=self.chat, prompt=chat_prompt)
        output = chain.run(input=input, **kwargs)

        return output
