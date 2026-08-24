from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Listing:
    """
    Représente une annonce provenant d'une marketplace.
    """

    id: str
    title: str
    price: float
    url: str
    marketplace: str

    image_url: Optional[str] = None
    seller_name: Optional[str] = None
    description: Optional[str] = None


class Marketplace(ABC):
    """
    Interface commune à toutes les marketplaces.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom de la marketplace."""
        pass

    @abstractmethod
    def search(self, query: str) -> list[Listing]:
        """Recherche des annonces."""
        pass
