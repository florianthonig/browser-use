from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any, Type, Callable
import asyncio

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from browser_use.agent.service import Agent
from browser_use.agent.task_manager import TaskManager, Task, Step, StepStatus
from browser_use.agent.views import AgentOutput, AgentStepInfo, ActionResult
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserState
from browser_use.controller.service import Controller
from browser_use.agent.prompts import SystemPrompt

logger = logging.getLogger(__name__)


class EnhancedAgent(Agent):
    """
    Enhanced version of the Agent class that supports dynamic task modification
    and step tracking using the TaskManager.
    """
    
    def __init__(
        self,
        task: str,
        llm: BaseChatModel,
        browser: Browser | None = None,
        browser_context: BrowserContext | None = None,
        controller: Controller = Controller(),
        use_vision: bool = True,
        scratchpad_dir: str = "scratchpads",
        max_retries: int = 3,
        system_prompt_class: Type[SystemPrompt] = SystemPrompt,
        **kwargs
    ):
        # Remove max_retries from kwargs as it's handled by TaskManager
        kwargs_without_retries = {k: v for k, v in kwargs.items() if k != 'max_retries'}
        
        super().__init__(
            task=task,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            use_vision=use_vision,
            system_prompt_class=system_prompt_class,
            **kwargs_without_retries
        )
        
        # Initialize TaskManager
        self.task_manager = TaskManager(
            llm=llm,
            scratchpad_dir=scratchpad_dir,
            max_retries=max_retries
        )
        
        # Create initial task
        asyncio.create_task(self._initialize_task(task))

    async def _initialize_task(self, task_description: str) -> None:
        """Initialize the first task."""
        await self.task_manager.create_task(
            description=task_description,
            goal="Complete the given task successfully",
            details=[]
        )

    async def add_new_task(self, new_task: str, goal: str = "Complete the new task while considering previous context") -> Task:
        """
        Add a new task, potentially merging it with the current task.
        This overrides the parent class's add_new_task method.
        """
        # Pause current execution
        self.pause()
        
        # Add new task through task manager
        task = await self.task_manager.add_task(
            description=new_task,
            goal=goal
        )
        
        # Update message manager with new task
        self.message_manager.add_new_task(new_task)
        
        # Resume execution
        self.resume()
        
        return task

    async def step(self, step_info: Optional[AgentStepInfo] = None) -> None:
        """
        Execute one step of the task with enhanced task and step tracking.
        """
        current_task = self.task_manager.get_current_task()
        if not current_task:
            logger.error("No active task found")
            return

        try:
            # Get current step
            current_step_index = next(
                (i for i, step in enumerate(current_task.steps) 
                 if step.status in [StepStatus.OPEN, StepStatus.FAILED]),
                None
            )
            
            if current_step_index is None:
                logger.info("All steps completed")
                return
            
            # Update step status to in-progress
            await self.task_manager.update_step_status(
                current_step_index,
                StepStatus.IN_PROGRESS
            )
            
            # Execute the step using parent's implementation
            await super().step(step_info)
            
            # Update step status based on result
            if self._last_result:
                last_error = next((r.error for r in self._last_result if r.error), None)
                if last_error:
                    await self.task_manager.update_step_status(
                        current_step_index,
                        StepStatus.FAILED,
                        failure_details=last_error
                    )
                else:
                    await self.task_manager.update_step_status(
                        current_step_index,
                        StepStatus.COMPLETED
                    )
            
        except Exception as e:
            logger.error(f"Error in step execution: {str(e)}")
            if current_step_index is not None:
                await self.task_manager.update_step_status(
                    current_step_index,
                    StepStatus.FAILED,
                    failure_details=str(e)
                )
            raise

    def get_current_task(self) -> Optional[Task]:
        """Get the current task if one exists."""
        return self.task_manager.get_current_task()

    def get_step(self, step_index: int) -> Optional[Step]:
        """Get a specific step from the current task."""
        return self.task_manager.get_step(step_index) 