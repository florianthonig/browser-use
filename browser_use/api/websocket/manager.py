import logging
from typing import Dict, Any, Optional
import socketio
from datetime import datetime

logger = logging.getLogger(__name__)


class SocketManager:
    """Manages Socket.IO sessions and state."""
    
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.agent_sid: Optional[str] = None  # Only one agent session for now
    
    async def set_session_data(self, sid: str, data: Dict[str, Any]) -> None:
        """Store session data for a client."""
        if sid not in self.sessions:
            self.sessions[sid] = {}
        self.sessions[sid].update(data)
        self.sessions[sid]["last_active"] = datetime.utcnow()
    
    async def get_session_data(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get session data for a client."""
        return self.sessions.get(sid)
    
    async def remove_session(self, sid: str) -> None:
        """Remove a client session."""
        if sid in self.sessions:
            del self.sessions[sid]
            if self.agent_sid == sid:
                self.agent_sid = None
    
    async def set_agent_session(self, sid: str) -> None:
        """Set the active agent session."""
        if self.agent_sid and self.agent_sid != sid:
            # Disconnect previous agent session
            try:
                await self.sio.disconnect(self.agent_sid)
            except Exception as e:
                logger.error(f"Error disconnecting previous agent session: {str(e)}")
        self.agent_sid = sid
    
    async def broadcast_agent_event(self, event: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to all connected clients except the agent."""
        for sid in self.sessions:
            if sid != self.agent_sid:
                try:
                    await self.sio.emit(event, data, room=sid)
                except Exception as e:
                    logger.error(f"Error broadcasting to {sid}: {str(e)}")
    
    async def send_to_agent(self, event: str, data: Dict[str, Any]) -> bool:
        """Send an event to the agent session."""
        if not self.agent_sid:
            logger.error("No agent session available")
            return False
        
        try:
            await self.sio.emit(event, data, room=self.agent_sid)
            return True
        except Exception as e:
            logger.error(f"Error sending to agent: {str(e)}")
            return False
    
    def is_agent_connected(self) -> bool:
        """Check if an agent session is currently connected."""
        return self.agent_sid is not None and self.agent_sid in self.sessions 