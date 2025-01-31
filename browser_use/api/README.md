# Browser-Use Agent API Server

WebSocket-based API server for the Browser-Use Agent, providing real-time communication and task management capabilities.

## Features

- Real-time bidirectional communication using Socket.IO
- JWT authentication
- Automatic reconnection handling
- Task and step management
- Human interaction support
- Event-driven architecture

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from browser_use.api.server import api
import uvicorn

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
```

## Authentication

The API uses JWT (JSON Web Token) for authentication. To generate a token:

```python
from browser_use.api.auth import create_access_token
from browser_use.api.config import Settings

settings = Settings()
token = await create_access_token(
    data={"sub": "username", "is_agent": False},
    settings=settings
)
```

## WebSocket Events

### Server -> Client Events

1. Task Update:
```python
{
    "type": "task_update",
    "task": {
        "task_id": "abc123",
        "description": "Task description",
        "current_goal": "Task goal",
        "details": ["Detail 1", "Detail 2"],
        "notes": ["Note 1"],
        "steps": [...],
        "scratchpad_path": "path/to/scratchpad.md",
        "max_retries": 3
    }
}
```

2. Step Update:
```python
{
    "type": "step_update",
    "task_id": "abc123",
    "step_index": 0,
    "step": {
        "description": "Step description",
        "reasoning": "Step reasoning",
        "status": "in-progress",
        "retry_count": 0
    }
}
```

3. Human Input Request:
```python
{
    "type": "human_input_needed",
    "task_id": "abc123",
    "step_index": 2,
    "prompt": "Please verify this information",
    "options": ["Yes", "No", "Skip"]
}
```

### Client -> Server Commands

1. Add Task:
```python
{
    "type": "add_task",
    "description": "Task description",
    "goal": "Optional goal"
}
```

2. Modify Task:
```python
{
    "type": "modify_task",
    "task_id": "abc123",
    "description": "New description",
    "goal": "New goal"
}
```

3. Human Input:
```python
{
    "type": "human_input",
    "task_id": "abc123",
    "step_index": 2,
    "input": "User input"
}
```

4. Control Commands:
```python
{"type": "pause"}
{"type": "resume"}
{"type": "stop"}
```

## Configuration

Configuration is handled through environment variables or a .env file:

```env
# JWT Settings
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# CORS Settings
CORS_ORIGINS=["http://localhost:3000"]

# Socket.IO Settings
SOCKETIO_PING_TIMEOUT=5
SOCKETIO_PING_INTERVAL=25
SOCKETIO_MAX_HTTP_BUFFER_SIZE=1000000

# Agent Settings
AGENT_MAX_RETRIES=3
AGENT_SCRATCHPAD_DIR=scratchpads
```

## WebSocket Manager

The `SocketManager` class handles WebSocket connections and session management:

```python
from browser_use.api.websocket.manager import SocketManager

# Initialize manager
socket_manager = SocketManager(sio)

# Set session data
await socket_manager.set_session_data(sid, {"user": user})

# Broadcast event
await socket_manager.broadcast_agent_event("task_update", task_data)

# Send to specific agent
await socket_manager.send_to_agent("command", command_data)
```

## Task Management

Tasks are managed through the TaskManager class:

```python
from browser_use.agent.task_manager import TaskManager

# Initialize manager
task_manager = TaskManager(llm, scratchpad_dir="scratchpads")

# Create task
task = await task_manager.create_task(
    description="Task description",
    goal="Task goal"
)

# Update step status
await task_manager.update_step_status(
    step_index=0,
    new_status=StepStatus.IN_PROGRESS
)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

The project uses ruff for linting:

```bash
ruff check .
ruff format .
```

## Security Considerations

1. JWT Token Security:
   - Use strong secret keys
   - Set appropriate token expiration
   - Rotate keys periodically

2. WebSocket Security:
   - Validate all incoming messages
   - Implement rate limiting
   - Use secure WebSocket (wss://) in production

3. Error Handling:
   - Never expose internal errors to clients
   - Log all errors appropriately
   - Implement proper error recovery

## License

MIT 