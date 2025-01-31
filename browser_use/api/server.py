from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import socketio
import jwt
from datetime import datetime, timedelta
import logging
from typing import Optional

from .config import Settings
from .websocket.manager import SocketManager
from .auth import get_current_user, create_access_token
from .schemas.events import ConnectionStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    settings = Settings()
    
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
    
    # Get authentication token from query parameters
    auth_token = environ.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
    
    try:
        # Verify token
        if not auth_token:
            raise ValueError("No authentication token provided")
        
        user = await get_current_user(auth_token)
        if not user:
            raise ValueError("Invalid authentication token")
        
        # Store user info in session
        await socket_manager.set_session_data(sid, {"user": user})
        
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

# Export the main application
api = main_app 