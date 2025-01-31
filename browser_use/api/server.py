from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import socketio
import logging
from typing import Optional

from .config import Settings
from .websocket.manager import SocketManager
from .schemas.events import ConnectionStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Create FastAPI app
app = FastAPI(title="Browser-Use Agent API")

# Create SocketIO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[],  # Will be set from config
    logger=logger,
    engineio_logger=logger
)

# Create SocketIO app
socket_app = socketio.ASGIApp(sio)

# Create socket manager
socket_manager = SocketManager(sio)

# Merge FastAPI and SocketIO apps
main_app = FastAPI()
main_app.mount("/ws", socket_app)  # Socket.IO endpoints
main_app.mount("/", app)  # Regular FastAPI endpoints

async def verify_rest_api_key(x_api_key: str = Header(...)):
    """Verify REST API key for HTTP endpoints."""
    if x_api_key != settings.REST_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Update SocketIO CORS settings
    sio.cors_allowed_origins = settings.cors_origins

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")
    
    # Get API key from query parameters
    ws_api_key = environ.get('HTTP_X_API_KEY')
    
    try:
        # Verify API key
        if not ws_api_key:
            raise ValueError("No API key provided")
        
        if ws_api_key != settings.WS_API_KEY:
            raise ValueError("Invalid API key")
        
        # Send connection success event
        await sio.emit('status', 
                      ConnectionStatus(status="connected", message="Successfully connected").dict(),
                      room=sid)
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        # Disconnect client on authentication failure
        await sio.emit('status', 
                      ConnectionStatus(status="error", message=str(e)).dict(),
                      room=sid)
        await sio.disconnect(sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")
    await socket_manager.remove_session(sid)

# Add API key dependency to all routes
app.dependency_overrides[Depends] = verify_rest_api_key

# Export the main application
api = main_app 