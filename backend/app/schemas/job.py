from datetime import datetime

from pydantic import BaseModel


class IngestionJobResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_records: int
    total_records_processed: int
    inserted_records: int
    error_message: str | None
