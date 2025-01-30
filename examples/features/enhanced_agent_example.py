import asyncio
import logging
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI

from browser_use.agent.enhanced_agent import EnhancedAgent
from browser_use.controller.service import Controller

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the model
llm = ChatOpenAI(
    model='gpt-4',
    temperature=0.0,
)

# Initialize the controller
controller = Controller()

# Initial task
initial_task = "Search for information about AI agents and summarize the main concepts"

async def main():
    # Create the enhanced agent
    agent = EnhancedAgent(
        task=initial_task,
        llm=llm,
        controller=controller,
        use_vision=True,
        scratchpad_dir="example_scratchpads"
    )
    
    # Start the initial task
    logger.info(f"Starting initial task: {initial_task}")
    await agent.run(max_steps=10)
    
    # Add a new related task
    new_task = "Find specific examples of AI agents being used in real-world applications"
    logger.info(f"Adding new task: {new_task}")
    
    # Add the new task with a specific goal
    task = await agent.add_new_task(
        new_task,
        goal="Find practical applications that demonstrate the concepts from the previous task"
    )
    
    # Continue execution with the new/merged task
    logger.info(f"Continuing with {'merged' if task else 'new'} task")
    await agent.run(max_steps=10)
    
    # Get the current task status
    current_task = agent.get_current_task()
    if current_task:
        logger.info(f"Task Status:")
        logger.info(f"Description: {current_task.description}")
        logger.info(f"Goal: {current_task.current_goal}")
        logger.info("Steps:")
        for i, step in enumerate(current_task.steps, 1):
            logger.info(f"  {i}. {step.description} - Status: {step.status}")
            if step.failure_details:
                logger.info(f"     Failure: {step.failure_details}")

if __name__ == '__main__':
    asyncio.run(main()) 