from typing import Optional, Tuple
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .views import Task
from .scratchpad import ScratchpadManager


class TaskMerger:
    def __init__(self, llm: BaseChatModel, scratchpad_manager: ScratchpadManager):
        self.llm = llm
        self.scratchpad_manager = scratchpad_manager

    async def can_merge_tasks(self, current_task: Task, new_task_description: str) -> Tuple[bool, str]:
        """
        Ask the LLM if the new task can be merged with the current task.
        Returns (can_merge, reasoning)
        """
        prompt = self._create_merge_evaluation_prompt(current_task, new_task_description)
        response = await self.llm.ainvoke([
            SystemMessage(content="""You are a task evaluation AI. Your job is to determine if two tasks can be merged.
            Respond with either 'MERGE: <reasoning>' or 'NO_MERGE: <reasoning>'."""),
            HumanMessage(content=prompt)
        ])
        
        if isinstance(response, AIMessage):
            result = response.content
            if isinstance(result, str):
                result = result.strip()
                can_merge = result.startswith("MERGE:")
                reasoning = result.split(":", 1)[1].strip()
                return can_merge, reasoning
        
        return False, "Failed to parse LLM response"

    async def merge_tasks(self, current_task: Task, new_task_description: str, merge_reasoning: str) -> Task:
        """
        Create a new merged task combining the current task and new task.
        Uses the LLM to generate the merged task description and update steps.
        """
        prompt = self._create_merge_prompt(current_task, new_task_description, merge_reasoning)
        response = await self.llm.ainvoke([
            SystemMessage(content="""You are a task merging AI. Create a new task that combines the two tasks effectively.
            Include updated steps that encompass both tasks' goals."""),
            HumanMessage(content=prompt)
        ])
        
        # Parse LLM response and create new task (to be implemented)
        # This will create a new Task object with merged details and steps
        raise NotImplementedError

    def _create_merge_evaluation_prompt(self, current_task: Task, new_task_description: str) -> str:
        return f"""Current Task:
Description: {current_task.description}
Current Goal: {current_task.current_goal}
Current Steps: {[step.description for step in current_task.steps]}

New Task:
{new_task_description}

Can these tasks be merged into a single coherent task? Consider:
1. Are the goals compatible?
2. Would merging create a logical workflow?
3. Would the merged task be too complex?

Respond with MERGE or NO_MERGE followed by your reasoning."""

    def _create_merge_prompt(self, current_task: Task, new_task_description: str, merge_reasoning: str) -> str:
        return f"""Current Task:
{current_task.description}

New Task:
{new_task_description}

Merge Reasoning:
{merge_reasoning}

Create a new merged task that combines both tasks effectively.
Include:
1. New task description
2. Updated goal
3. Combined set of steps
4. Any important details or notes

Format your response as:
TASK: <task description>
GOAL: <goal>
DETAILS:
- <detail1>
- <detail2>
NOTES:
- <note1>
- <note2>
STEPS:
1. <step1>
   REASONING: <reasoning1>
2. <step2>
   REASONING: <reasoning2>
...""" 