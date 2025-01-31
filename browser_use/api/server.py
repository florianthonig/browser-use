from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import socketio
import logging
from typing import Optional

from .config import Settings
from .websocket.manager import SocketManager
from .schemas.events import ConnectionStatus

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Create FastAPI app
app = FastAPI(title="Browser-Use Agent API")

# Create SocketIO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:8080'],  # Frontend URL
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

# Merge FastAPI and SocketIO apps
main_app = FastAPI()
main_app.mount("/socket.io", socket_app)  # Standard Socket.IO path
main_app.mount("/", app)  # Regular FastAPI endpoints

async def verify_rest_api_key(x_api_key: str = Header(...)):
    """Verify REST API key for HTTP endpoints."""
    if x_api_key != settings.REST_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    # Setup CORS for HTTP endpoints
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['http://localhost:8080'],  # Frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Update SocketIO CORS settings
    sio.cors_allowed_origins = ['http://localhost:8080']  # Frontend URL

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")
    logger.info(f"Full environ: {environ}")
    logger.info(f"Query string: {environ.get('QUERY_STRING', 'no query string')}")
    logger.info(f"Headers: {environ.get('headers', 'no headers')}")
    
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
        logger.exception("Full error:")  # This will log the full stack trace
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