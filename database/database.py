from sqlalchemy import create_engine

from config.settings import DATABASE_PATH

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    echo=False,
)
