from database.database import Database
from models.offer import Offer


class OfferRepository:

    def __init__(self):
        self.db = Database()

    def save_all(self, offers: list[Offer]):

        for offer in offers:
            self.db.save_offer(offer)

    def close(self):
        self.db.close()
        