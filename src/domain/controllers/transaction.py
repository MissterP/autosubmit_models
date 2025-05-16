from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Transaction(Generic[T], ABC):
    """Abstract base class for all transactions."""

    @abstractmethod
    async def execute(self) -> T:
        """Execute the transaction."""

        raise NotImplementedError(
            "Subclasses must implement the execute method of the Transaction class."
        )
