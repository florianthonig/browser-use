from typing import List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .views import Step, StepStatus, Task


class StepManager:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def generate_steps(self, task_description: str, goal: str) -> List[Step]:
        """Generate steps for a task using the LLM."""
        prompt = self._create_step_generation_prompt(task_description, goal)
        response = await self.llm.ainvoke([
            SystemMessage(content="""You are a task planning AI. Break down the task into logical steps.
            Each step should be clear and actionable."""),
            HumanMessage(content=prompt)
        ])
        
        if isinstance(response, AIMessage) and isinstance(response.content, str):
            return self._parse_steps_from_llm_response(response.content)
        return []

    def update_step_status(self, step: Step, new_status: StepStatus, 
                          failure_details: Optional[str] = None) -> Step:
        """Update the status of a step and handle retries if needed."""
        step.status = new_status
        
        if new_status == StepStatus.FAILED:
            step.failure_details = failure_details
            step.retry_count += 1
        
        return step

    def _create_step_generation_prompt(self, task_description: str, goal: str) -> str:
        return f"""Task Description: {task_description}
Goal: {goal}

Break this task down into clear, logical steps. For each step:
1. Provide a clear description
2. Explain the reasoning behind it

Format your response as:
STEP: <step description>
REASONING: <step reasoning>

STEP: <step description>
REASONING: <step reasoning>
...
"""

    def _parse_steps_from_llm_response(self, response: str) -> List[Step]:
        """Parse the LLM response into Step objects."""
        steps = []
        current_description = None
        current_reasoning = None
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('STEP:'):
                # Save previous step if exists
                if current_description and current_reasoning:
                    steps.append(Step(
                        description=current_description,
                        reasoning=current_reasoning
                    ))
                current_description = line[5:].strip()
                current_reasoning = None
            elif line.startswith('REASONING:'):
                current_reasoning = line[10:].strip()
        
        # Add the last step
        if current_description and current_reasoning:
            steps.append(Step(
                description=current_description,
                reasoning=current_reasoning
            ))
        
        return steps 