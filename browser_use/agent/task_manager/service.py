import uuid
from typing import Optional, List
from langchain_core.language_models.chat_models import BaseChatModel

from .views import Task, Step, StepStatus
from .scratchpad import ScratchpadManager
from .merger import TaskMerger
from .step import StepManager


class TaskManager:
    def __init__(
        self,
        llm: BaseChatModel,
        scratchpad_dir: str = "scratchpads",
        max_retries: int = 3
    ):
        self.llm = llm
        self.max_retries = max_retries
        self.current_task: Optional[Task] = None
        
        # Initialize components
        self.scratchpad_manager = ScratchpadManager(scratchpad_dir)
        self.task_merger = TaskMerger(llm, self.scratchpad_manager)
        self.step_manager = StepManager(llm)

    async def create_task(self, description: str, goal: str, details: Optional[List[str]] = None) -> Task:
        """Create a new task and generate its initial steps."""
        task_id = str(uuid.uuid4())
        scratchpad_path = self.scratchpad_manager.generate_scratchpad_path(
            task_name=description.lower().replace(" ", "_")[:30]
        )
        
        # Generate steps using LLM
        steps = await self.step_manager.generate_steps(description, goal)
        
        # Create task
        task = Task(
            task_id=task_id,
            description=description,
            current_goal=goal,
            details=details if details is not None else [],
            notes=[],
            steps=steps,
            scratchpad_path=scratchpad_path,
            max_retries=self.max_retries
        )
        
        # Create scratchpad
        self.scratchpad_manager.create_scratchpad(task)
        
        self.current_task = task
        return task

    async def add_task(self, description: str, goal: str, details: Optional[List[str]] = None) -> Task:
        """Add a new task, potentially merging with the current task."""
        if not self.current_task:
            return await self.create_task(description, goal, details)
        
        # Try to merge with current task
        can_merge, reasoning = await self.task_merger.can_merge_tasks(
            self.current_task, description
        )
        
        if can_merge:
            # Merge tasks
            merged_task = await self.task_merger.merge_tasks(
                self.current_task, description, reasoning
            )
            self.current_task = merged_task
            self.scratchpad_manager.create_scratchpad(merged_task)
            return merged_task
        else:
            # Save current task's progress and create new task
            # (Progress saving will be implemented when needed)
            return await self.create_task(description, goal, details)

    async def update_step_status(
        self,
        step_index: int,
        new_status: StepStatus,
        failure_details: Optional[str] = None
    ) -> Task:
        """Update the status of a step and handle any necessary state changes."""
        if not self.current_task or step_index >= len(self.current_task.steps):
            raise ValueError("Invalid step index")
        
        step = self.current_task.steps[step_index]
        updated_step = self.step_manager.update_step_status(
            step, new_status, failure_details
        )
        
        self.current_task.steps[step_index] = updated_step
        self.scratchpad_manager.update_scratchpad(self.current_task)
        
        return self.current_task

    def get_current_task(self) -> Optional[Task]:
        """Get the current task if one exists."""
        return self.current_task

    def get_step(self, step_index: int) -> Optional[Step]:
        """Get a specific step from the current task."""
        if not self.current_task or step_index >= len(self.current_task.steps):
            return None
        return self.current_task.steps[step_index] 