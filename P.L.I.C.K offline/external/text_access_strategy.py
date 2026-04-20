"""Abstract interface for accessing and replacing selected text in external apps."""
from abc import ABC, abstractmethod


class TextAccessStrategy(ABC):
    @abstractmethod
    def get_selected_text(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def replace_selection(self, replacement: str) -> bool:
        """Return True if replacement succeeded (non-destructive), False to indicate fallback needed."""
        raise NotImplementedError
