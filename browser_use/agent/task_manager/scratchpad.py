import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from .views import Task, Step, StepStatus


class ScratchpadManager:
    def __init__(self, base_dir: str = "scratchpads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def generate_scratchpad_path(self, task_name: str) -> str:
        """Generate a unique scratchpad filename."""
        session_id = uuid.uuid4().hex[:4]
        task_id = uuid.uuid4().hex[:6]
        filename = f"sess_{session_id}_task_{task_name}_{task_id}.md"
        return str(self.base_dir / filename)

    def create_scratchpad(self, task: Task) -> None:
        """Create a new scratchpad file for the task."""
        content = self._generate_markdown(task)
        with open(task.scratchpad_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def update_scratchpad(self, task: Task) -> None:
        """Update the existing scratchpad with current task state."""
        content = self._generate_markdown(task)
        with open(task.scratchpad_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_markdown(self, task: Task) -> str:
        """Generate markdown content for the scratchpad."""
        lines = [
            f"# Task: {task.description}",
            f"Current Goal: {task.current_goal}\n",
            "## Details",
        ]
        
        # Add details
        for detail in task.details:
            lines.append(f"- {detail}")
        lines.append("")
        
        # Add notes
        lines.append("## Notes")
        for note in task.notes:
            lines.append(f"- {note}")
        lines.append("")
        
        # Add task history
        lines.append("## Task History")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"- [{timestamp}] Task initiated: {task.description}")
        lines.append("")
        
        # Add steps
        lines.append("## Steps")
        for i, step in enumerate(task.steps, 1):
            lines.extend([
                f"### Step {i}: {step.description}",
                f"Reasoning: {step.reasoning}",
                f"Status: {step.status.value}"
            ])
            if step.failure_details:
                lines.append(f"Failure Details: {step.failure_details}")
            lines.append("")
        
        return "\n".join(lines)

    def read_task(self, scratchpad_path: str) -> Task:
        """Read task from scratchpad file (to be implemented)."""
        # This will be implemented when needed for task merging
        raise NotImplementedError 