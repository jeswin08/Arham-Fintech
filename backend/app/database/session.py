from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_database_tables() -> None:
    from app.models.ingestion_job import IngestionJob
    from app.models.trade import Trade

    Base.metadata.create_all(bind=engine)
    columns = {
        column["name"]
        for column in inspect(engine).get_columns("ingestion_jobs")
    }
    with engine.begin() as connection:
        if "total_records_processed" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE ingestion_jobs "
                    "ADD COLUMN total_records_processed INTEGER NOT NULL DEFAULT 0"
                )
            )
        if "inserted_records" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE ingestion_jobs "
                    "ADD COLUMN inserted_records INTEGER NOT NULL DEFAULT 0"
                )
            )
        if "total_records_processed" not in columns or "inserted_records" not in columns:
            connection.execute(
                text(
                    "UPDATE ingestion_jobs "
                    "SET total_records_processed = total_records, "
                    "inserted_records = total_records "
                    "WHERE total_records_processed = 0 AND inserted_records = 0"
                )
            )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
