import sqlite3
from pathlib import Path

from models.offer import Offer


class Database:

    def __init__(self, db_name: str = "fleet.db"):

        self.db_path = Path(db_name)

        self.connection = sqlite3.connect(self.db_path)

        self.create_tables()

    def create_tables(self):

        cursor = self.connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            provider TEXT,
            brand TEXT,
            model TEXT,
            trim TEXT,
            fuel_type TEXT,

            monthly_fee INTEGER,
            duration INTEGER,
            mileage INTEGER,

            url TEXT
        )
        """)

        self.connection.commit()

    def save_offer(self, offer: Offer):

        cursor = self.connection.cursor()

        cursor.execute("""
        INSERT INTO offers(
            provider,
            brand,
            model,
            trim,
            fuel_type,
            monthly_fee,
            duration,
            mileage,
            url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            offer.provider,
            offer.brand,
            offer.model,
            offer.trim,
            offer.fuel_type,
            offer.monthly_fee,
            offer.duration,
            offer.mileage,
            offer.url,
        ))

        self.connection.commit()

    def close(self):
        self.connection.close()