from loguru import logger

from database.database import engine

logger.info("Fleet Intelligence Platform")

with engine.connect():
    logger.success("Database connected")

logger.success("Ready.")
