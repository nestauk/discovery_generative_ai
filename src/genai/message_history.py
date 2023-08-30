from abc import ABC
from abc import abstractmethod
from typing import List

import tiktoken

from genai import MessageTemplate


class TokenCounter:
    def num_tokens_from_string(s: str, model_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(model_name)
        num_tokens = len(encoding.encode(s))
        return num_tokens

    @classmethod
    def num_tokens_from_messages(cls, messages, model_name):
        """Returns the number of tokens in a list of messages."""
        num_tokens = 0

        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 3
        tokens_per_name = 1
        for message in messages:
            num_tokens += tokens_per_message
            for k, v in message.items():
                num_tokens += cls.num_tokens_from_string(v, model_name)
                if k == "name":  # When role = function
                    num_tokens += tokens_per_name

        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens


class BaseMessageHistory(ABC):
    """Base class for message history."""

    @abstractmethod
    def add_message(self, message: MessageTemplate) -> None:
        pass

    @abstractmethod
    def get_messages(self) -> List[MessageTemplate]:
        pass

    @abstractmethod
    def clear_messages(self) -> None:
        pass


class InMemoryMessageHistory(BaseMessageHistory):
    """In-memory message history."""

    def __init__(self) -> None:
        self.messages = []

    def add_message(self, message: MessageTemplate) -> None:
        self.messages.append(message)

    def get_messages(self) -> List[dict]:
        # template.to_prompt() to get the dict and count tokens
        return self.messages

    def clear_messages(self) -> None:
        self.messages = []
