import json
import string

from abc import ABC
from abc import abstractmethod
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional
from typing import Union


@dataclass
class BasePromptTemplate(ABC):
    """Base template prompts flexibly."""

    initial_template: Dict[str, str] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Keep the initial template."""
        self.initial_template = self._initialize_template()

    @abstractmethod
    def _initialize_template(self) -> None:
        """To be implemented by child classes"""
        pass

    @abstractmethod
    def _from_dict(data: Dict) -> None:
        """Create a Template instance from a dictionary."""
        pass

    def format_message(self, **kwargs) -> None:
        """Process a message and fill in any placeholders."""
        placeholders = self._extract_placeholders(self.initial_template["content"])

        if placeholders:
            self.content = self.initial_template["content"].format(**kwargs)

    @classmethod
    def load(cls, obj: Union[Dict, str]) -> "BasePromptTemplate":
        """Load a Template instance from a JSON file or a dictionary."""
        if isinstance(obj, str):
            return cls._from_json(obj)
        elif isinstance(obj, Dict):
            return cls._from_dict(obj)
        else:
            raise TypeError(f"Expected a JSON file path or a dictionary, got {type(obj)}.")

    @staticmethod
    def _exclude_keys(d: dict, exclude: Optional[str] = None) -> dict:
        """Exclude keys from a dictionary."""
        if exclude:
            for item in exclude:
                d.pop(item, None)
            return d
        return d

    def to_prompt(self, exclude: Optional[str] = "initial_template") -> Dict:
        """Convert a Template instance to a JSON string."""
        d = asdict(self)
        return self._exclude_keys(d, exclude=exclude)

    @staticmethod
    def _extract_placeholders(s: str) -> List[str]:
        """Extract placeholder variables that can be filled in an f-string."""
        formatter = string.Formatter()
        return [field_name for _, field_name, _, _ in formatter.parse(s) if field_name is not None]

    @classmethod
    def _from_json(cls, json_path: str) -> "BasePromptTemplate":
        """Create a Template instance by providing a JSON path."""
        return cls._from_dict(cls._read_json(json_path))

    @staticmethod
    def _read_json(json_path: str) -> Dict:
        """Read a JSON file."""
        with open(json_path, "r") as f:
            return json.load(f)

    def to_json(self, path: str) -> None:
        """Convert a Template instance to a JSON string."""
        self._write_json(self.initial_template, path)

    def _write_json(self, data: Dict, path: str) -> None:
        """Write a JSON file."""
        with open(path, "w") as f:
            json.dump(data, f)


@dataclass
class MessageTemplate(BasePromptTemplate):
    """Create a template for a message prompt."""

    role: str
    content: str

    def _initialize_template(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }

    def _from_dict(data: Dict) -> "MessageTemplate":
        """Create a Template instance from a dictionary."""
        return MessageTemplate(**data)


@dataclass
class FunctionTemplate(BasePromptTemplate):
    """Create a template for an OpenAI function."""

    name: str
    description: str
    properties: Dict[str, str]

    def _initialize_template(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "properties": self.properties,
        }

    def _from_dict(data: Dict) -> "FunctionTemplate":
        """Create a Template instance from a dictionary."""
        return FunctionTemplate(**data)
