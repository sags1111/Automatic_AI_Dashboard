from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """
    Abstract base class for all database adapters.
    Every database adapter must implement these methods.
    """

    @abstractmethod
    def connect(self):
        """Establish connection to the database."""
        pass

    @abstractmethod
    def extract_schema(self):
        """Extract schema metadata from the database."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close the database connection."""
        pass