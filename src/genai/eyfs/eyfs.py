import logging
import string

from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import openai

from openai.error import APIConnectionError
from openai.error import APIError
from openai.error import RateLimitError
from openai.error import ServiceUnavailableError
from openai.error import Timeout
from tenacity import before_sleep_log
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from genai import MessageTemplate


logger = logging.getLogger(__name__)


class ActivityGenerator:
    """Generate tokens using OpenAI's API.

    TODO:
    - Streaming

    """

    @classmethod
    def generate(
        cls,
        messages: List[Union[str, Dict]],
        message_kwargs: Optional[Dict] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.0,
        **openai_kwargs,
    ) -> Union[Dict, str]:
        """Generate text using OpenAI's API.

        More details on the API and messages: https://platform.openai.com/docs/guides/gpt/chat-completions-api

        Args:
            messages
                A list of messages to send to the API. They can be:
                - dictionaries
                - str (JSON file path)
                - instances of classes that inherit from BasePromptTemplate

            message_kwargs
                A dictionary of keyword arguments to pass to the messages.

            model
                The OpenAI model to use.

            temperature
                The sampling temperature.

            openai_kwargs
                Keyword arguments to pass to the OpenAI API.

        Returns:
            A dictionary containing the response from the API.

        """
        if not message_kwargs:
            message_kwargs = {}

        messages = [cls.prepare_message(message, **message_kwargs) for message in messages]

        response = cls._call(
            messages=messages,
            temperature=temperature,
            model=model,
            **openai_kwargs,
        )

        return response["choices"][0]["message"]["content"]

    @classmethod
    def prepare_message(cls, obj: Union[MessageTemplate, dict, str], **kwargs) -> Dict:
        """Process a message."""
        if not isinstance(obj, MessageTemplate):
            prompt = MessageTemplate.load(obj)
        else:
            prompt = obj

        prompt.format_message(**kwargs)

        return prompt.to_prompt()

    @staticmethod
    @retry(
        retry(
            reraise=True,
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=1, min=1, max=60),
            retry=(
                retry_if_exception_type(Timeout)
                | retry_if_exception_type(APIError)
                | retry_if_exception_type(APIConnectionError)
                | retry_if_exception_type(RateLimitError)
                | retry_if_exception_type(ServiceUnavailableError)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
    )
    def _call(
        messages: List[Dict],
        temperature: float = 0.0,
        **kwargs,
    ) -> Dict:
        response = openai.ChatCompletion.create(
            messages=messages,
            temperature=temperature,
            **kwargs,
        )

        return response  # type: ignore

    @staticmethod
    def _extract_placeholders(s: str) -> List[str]:
        """Extract placeholder variables that can be filled in an f-string."""
        formatter = string.Formatter()
        return [field_name for _, field_name, _, _ in formatter.parse(s) if field_name is not None]
