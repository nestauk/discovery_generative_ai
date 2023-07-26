import logging
import string

from typing import Dict
from typing import List

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


logger = logging.getLogger(__name__)


class ActivityGenerator:
    """Generate tokens using OpenAI's API.

    TODO:
    - Streaming
    - Async calls
    - Parse more than one messages

    """

    @classmethod
    def generate(
        cls,
        messages: List[Dict],
        message_kwargs: Dict,
        temperature: float = 0.0,
        **openai_kwargs,
    ) -> Dict:
        """Generate text using OpenAI's API."""
        messages = [cls.prepare_message(message, **message_kwargs) for message in messages]

        response = cls._call(messages=messages, temperature=temperature, **openai_kwargs)

        return response  # type: ignore

    @classmethod
    def prepare_message(cls, message: Dict, **kwargs) -> Dict:
        """Process a message and fill in any placeholders."""
        placeholders = cls._extract_placeholders(message["content"])

        if len(placeholders) > 0:
            message["content"] = message["content"].format(**kwargs)

        if isinstance(message, dict):
            return message
        else:
            raise ValueError("Message must be a dictionary.")

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
        formatter = string.Formatter()
        return [field_name for _, field_name, _, _ in formatter.parse(s) if field_name is not None]
