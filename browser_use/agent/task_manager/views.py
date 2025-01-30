from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class StepStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    HUMAN = "human"


class Step(BaseModel):
    description: str
    reasoning: str
    status: StepStatus = StepStatus.OPEN
    failure_details: Optional[str] = None
    retry_count: int = 0


class Task(BaseModel):
    task_id: str
    description: str
    current_goal: str
    details: List[str]
    notes: List[str]
    steps: List[Step]
    scratchpad_path: str
    max_retries: int = 3 