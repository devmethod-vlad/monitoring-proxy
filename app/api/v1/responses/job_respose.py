import uuid
from dataclasses import dataclass


@dataclass
class JobResponse:
    """Ответ задачи"""

    job_id: uuid.UUID | str
