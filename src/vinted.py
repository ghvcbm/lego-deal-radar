from .marketplace import Marketplace, Listing


class VintedMarketplace(Marketplace):

    @property
    def name(self) -> str:
        return "vinted"

    def search(self, query: str) -> list[Listing]:
        # TODO: implémenter la recherche Vinted
        return []
