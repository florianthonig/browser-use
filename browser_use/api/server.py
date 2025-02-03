from fastapi import FastAPI, Depends, HTTPException, Header, Cookie
from fastapi.middleware.cors import CORSMiddleware
import socketio
import logging
from typing import Optional
from pydantic import BaseModel
import sqlite3
import os
import uvicorn
from multiprocessing import Process

from .config import Settings
from .websocket.manager import SocketManager
from .schemas.events import ConnectionStatus, AddTaskCommand
from browser_use.agent.enhanced_agent import EnhancedAgent
from langchain_google_genai import ChatGoogleGenerativeAI

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Create FastAPI app for REST API
rest_app = FastAPI(title="Browser-Use Agent REST API")

# Create FastAPI app for WebSocket
ws_app = FastAPI(title="Browser-Use Agent WebSocket API")

# Create SocketIO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.cors_origins,
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    always_connect=True
)

# Create SocketIO app
socket_app = socketio.ASGIApp(sio)

# Create socket manager
socket_manager = SocketManager(sio)

# Create agent instance (will be initialized via REST endpoint)
agent: Optional[EnhancedAgent] = None

class InitializeAgentRequest(BaseModel):
    """Request model for agent initialization."""
    gemini_api_key: str

# Mount Socket.IO to WebSocket app
ws_app.mount("/", socket_app)

# Add CORS middleware to REST app
rest_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_rest_api_key(x_api_key: str = Header(...)):
    """Verify REST API key for HTTP endpoints."""
    if x_api_key != settings.REST_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@rest_app.post("/initialize")
async def initialize_agent(
    request: InitializeAgentRequest,
    api_key: str = Depends(verify_rest_api_key)
):
    """Initialize the agent with the provided Gemini API key."""
    global agent
    
    try:
        # Initialize LLM with Gemini model
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            convert_system_message_to_human=True,
            temperature=0.7,
            top_p=1,
            top_k=40,
            google_api_key=request.gemini_api_key
        )
        
        # Initialize agent
        agent = EnhancedAgent(
            task="Initial task",  # This will be updated when tasks are added
            llm=llm,
            scratchpad_dir=settings.agent_scratchpad_dir,
            max_retries=settings.agent_max_retries
        )
        
        logger.info("Agent initialized successfully with Gemini model")
        return {"status": "success", "message": "Agent initialized successfully"}
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}")
        logger.exception("Full error:")
        raise HTTPException(status_code=500, detail=str(e))

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")
    
    try:
        # Get auth data from Socket.IO handshake
        query_string = environ.get('QUERY_STRING', '')
        logger.info(f"Parsing query string: {query_string}")
        
        if 'auth=' not in query_string:
            raise ValueError("No auth parameter in query string")
        
        # Extract auth parameter value
        auth_param = [param for param in query_string.split('&') if param.startswith('auth=')]
        if not auth_param:
            raise ValueError("No auth parameter found")
            
        auth = auth_param[0].split('auth=')[1]
        logger.info(f"Extracted auth: {auth[:8]}...")  # Log first 8 chars for security
        
        if not auth:
            raise ValueError("No API key provided")
        
        if auth != settings.WS_API_KEY:
            raise ValueError("Invalid API key")
        
        logger.info(f"Client {sid} authenticated successfully")
        # Send connection success event
        await sio.emit('status', 
                      ConnectionStatus(status="connected", message="Successfully connected").dict(),
                      room=sid)
        
    except Exception as e:
        logger.error(f"Authentication failed for client {sid}: {str(e)}")
        logger.exception("Full error:")
        await sio.emit('status', 
                      ConnectionStatus(status="error", message=str(e)).dict(),
                      room=sid)
        await sio.disconnect(sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")
    await socket_manager.remove_session(sid)

@sio.event
async def add_task(sid, data):
    """Handle task creation event."""
    logger.info(f"Received add_task event from {sid}: {data}")
    try:
        # Validate the task data
        command = AddTaskCommand(**data)
        
        # Get the agent session
        if not socket_manager.is_agent_connected():
            raise ValueError("No agent is currently connected")
        
        # Check if agent instance exists
        if agent is None:
            raise ValueError("Agent instance not initialized")
            
        # Add task using existing method
        task = await agent.add_new_task(
            new_task=command.description,
            goal=command.goal or "Complete the new task while considering previous context"
        )
        
        # Send acknowledgment back to client
        await sio.emit('status', 
                      ConnectionStatus(status="success", message="Task added successfully").dict(),
                      room=sid)
                      
    except Exception as e:
        logger.error(f"Error adding task: {str(e)}")
        await sio.emit('status',
                      ConnectionStatus(status="error", message=f"Failed to add task: {str(e)}").dict(),
                      room=sid)

def run_rest_server():
    """Run the REST API server."""
    uvicorn.run(rest_app, host="0.0.0.0", port=int(os.getenv('REST_PORT', 8000)))

def run_ws_server():
    """Run the WebSocket server."""
    uvicorn.run(ws_app, host="0.0.0.0", port=int(os.getenv('WS_PORT', 8001)))

if __name__ == "__main__":
    # Start both servers in separate processes
    rest_process = Process(target=run_rest_server)
    ws_process = Process(target=run_ws_server)
    
    rest_process.start()
    ws_process.start()
    
    rest_process.join()
    ws_process.join()
else:
    # For production deployment, export the apps separately
    rest_api = rest_app
    ws_api = ws_app 