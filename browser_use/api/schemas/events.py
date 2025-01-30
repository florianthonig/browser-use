from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from browser_use.agent.task_manager import Task, Step, StepStatus


class EventType(str, Enum):
    """Types of events that can be sent over WebSocket."""
    TASK_UPDATE = "task_update"
    STEP_UPDATE = "step_update"
    HUMAN_INPUT_NEEDED = "human_input_needed"
    ERROR = "error"
    STATUS = "status"


class CommandType(str, Enum):
    """Types of commands that can be received over WebSocket."""
    ADD_TASK = "add_task"
    MODIFY_TASK = "modify_task"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    HUMAN_INPUT = "human_input"


class ConnectionStatus(BaseModel):
    """Connection status event."""
    status: str
    message: str


class TaskEvent(BaseModel):
    """Task update event."""
    type: EventType = EventType.TASK_UPDATE
    task: Task


class StepEvent(BaseModel):
    """Step update event."""
    type: EventType = EventType.STEP_UPDATE
    task_id: str
    step_index: int
    step: Step


class HumanInputEvent(BaseModel):
    """Event requesting human input."""
    type: EventType = EventType.HUMAN_INPUT_NEEDED
    task_id: str
    step_index: int
    prompt: str
    options: Optional[List[str]] = None


class ErrorEvent(BaseModel):
    """Error event."""
    type: EventType = EventType.ERROR
    message: str
    details: Optional[Dict[str, Any]] = None


# Command Models (received from client)
class AddTaskCommand(BaseModel):
    """Command to add a new task."""
    type: CommandType = CommandType.ADD_TASK
    description: str
    goal: Optional[str] = None


class ModifyTaskCommand(BaseModel):
    """Command to modify an existing task."""
    type: CommandType = CommandType.MODIFY_TASK
    task_id: str
    description: Optional[str] = None
    goal: Optional[str] = None


class HumanInputCommand(BaseModel):
    """Command providing human input."""
    type: CommandType = CommandType.HUMAN_INPUT
    task_id: str
    step_index: int
    input: str


class ControlCommand(BaseModel):
    """Command to control agent execution."""
    type: CommandType 