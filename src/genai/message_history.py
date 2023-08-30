from abc import ABC
from abc import abstractmethod
from typing import List

import tiktoken

from genai import MessageTemplate


class TokenCounter:
    @staticmethod
    def _count_tokens_from_string(s: str, model_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(model_name)
        num_tokens = len(encoding.encode(s))
        return num_tokens

    @classmethod
    def _count_tokens_from_messages(cls, messages, model_name):
        """Returns the number of tokens in a list of messages."""
        num_tokens = 0

        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 3
        tokens_per_name = 1
        for message in messages:
            num_tokens += tokens_per_message
            for k, v in message.items():
                num_tokens += cls._count_tokens_from_string(v, model_name)
                if k == "name":  # When role = function
                    num_tokens += tokens_per_name

        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    @staticmethod
    def _forget_messages(num_tokens, max_tokens):
        if num_tokens > max_tokens:
            return True
        return False

    @classmethod
    def buffer(
        cls,
        messages,
        model_name="gpt-3.5-turbo",
        max_tokens=4096,
        keep_system_message=True,
    ):
        """Returns the number of tokens in a list of messages.

        TODO: Keep system message.

        """
        num_tokens = cls._count_tokens_from_messages(messages, model_name)
        print(num_tokens)
        if cls._forget_messages(num_tokens, max_tokens):
            messages.pop(0)
            cls.buffer(messages, model_name=model_name, max_tokens=max_tokens)

        return messages


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

    def get_messages(
        self,
        model_name="gpt-3.5-turbo",
        max_tokens=4096,
        keep_system_message=True,
    ) -> List[dict]:
        """Get all messages from history.

        Filter messages when the number of tokens exceeds max_tokens.

        """
        return TokenCounter.buffer(
            self.messages,
            model_name=model_name,
            max_tokens=max_tokens,
            keep_system_message=keep_system_message,
        )

    def clear_messages(self) -> None:
        self.messages = []
