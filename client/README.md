# Browser-Use Agent API Client

A TypeScript client for interacting with the Browser-Use Agent WebSocket API. This client provides real-time communication with the agent, allowing dynamic task modification and control.

## Installation

```bash
npm install browser-use-client
```

## Quick Start

```typescript
import { AgentClient } from 'browser-use-client';

const client = new AgentClient(
    'ws://localhost:8000/ws',
    'your-jwt-token',
    (event) => console.log('Event received:', event),
    (status) => console.log('Connection status:', status),
    (error) => console.error('Error:', error)
);

// Add a new task
await client.addTask(
    'Search for information about WebSocket',
    'Learn about WebSocket communication'
);
```

## Authentication

The API uses JWT (JSON Web Token) authentication. You need to provide a valid JWT token when creating the client:

```typescript
const token = 'your-jwt-token'; // Get this from your authentication endpoint
const client = new AgentClient('ws://localhost:8000/ws', token);
```

## Events

The API uses a real-time event system to communicate agent state changes:

### Event Types

```typescript
enum EventType {
    TASK_UPDATE = 'task_update',
    STEP_UPDATE = 'step_update',
    HUMAN_INPUT_NEEDED = 'human_input_needed',
    ERROR = 'error',
    STATUS = 'status'
}
```

### Event Examples

1. Task Update Event:
```typescript
{
    type: 'task_update',
    task: {
        task_id: 'abc123',
        description: 'Search for information',
        current_goal: 'Find relevant data',
        details: ['Detail 1', 'Detail 2'],
        notes: ['Note 1'],
        steps: [/* Step objects */],
        scratchpad_path: 'path/to/scratchpad.md',
        max_retries: 3
    }
}
```

2. Step Update Event:
```typescript
{
    type: 'step_update',
    task_id: 'abc123',
    step_index: 0,
    step: {
        description: 'Navigate to website',
        reasoning: 'Need to access the homepage',
        status: 'in-progress',
        retry_count: 0
    }
}
```

3. Human Input Needed Event:
```typescript
{
    type: 'human_input_needed',
    task_id: 'abc123',
    step_index: 2,
    prompt: 'Please verify this information',
    options: ['Yes', 'No', 'Skip']
}
```

## Commands

The client provides several methods to control the agent:

### Task Management

```typescript
// Add a new task
await client.addTask(
    'Task description',
    'Optional goal'
);

// Modify an existing task
await client.modifyTask(
    'task-id',
    'New description',
    'New goal'
);

// Provide human input
await client.sendHumanInput(
    'task-id',
    stepIndex,
    'User input'
);
```

### Agent Control

```typescript
// Pause the agent
await client.pause();

// Resume the agent
await client.resume();

// Stop the agent
await client.stop();
```

## Connection Management

The client automatically handles connection management:

```typescript
// Check connection status
const isConnected = client.isConnected();

// Manual connection control
client.connect();
client.disconnect();
```

### Reconnection

The client automatically attempts to reconnect when the connection is lost:
- Maximum reconnection attempts: 5
- Initial delay: 1 second
- Maximum delay: 5 seconds
- Exponential backoff between attempts

## TypeScript Types

The client provides full TypeScript support with the following key types:

```typescript
interface Task {
    task_id: string;
    description: string;
    current_goal: string;
    details: string[];
    notes: string[];
    steps: Step[];
    scratchpad_path: string;
    max_retries: number;
}

interface Step {
    description: string;
    reasoning: string;
    status: 'open' | 'in-progress' | 'completed' | 'failed' | 'human';
    failure_details?: string;
    retry_count: number;
}

type AgentEvent = TaskEvent | StepEvent | HumanInputEvent | ErrorEvent;
type AgentCommand = AddTaskCommand | ModifyTaskCommand | HumanInputCommand | ControlCommand;
```

## Error Handling

The client provides comprehensive error handling:

```typescript
const client = new AgentClient(
    'ws://localhost:8000/ws',
    token,
    undefined,
    undefined,
    (error) => {
        console.error('Connection error:', error);
        // Handle error appropriately
    }
);

try {
    await client.addTask('Task description');
} catch (error) {
    console.error('Failed to add task:', error);
}
```

## Best Practices

1. Always handle connection status changes:
```typescript
const client = new AgentClient(
    'ws://localhost:8000/ws',
    token,
    undefined,
    (status) => {
        if (status.status === 'disconnected') {
            // Handle disconnection
        }
    }
);
```

2. Process events appropriately:
```typescript
const client = new AgentClient(
    'ws://localhost:8000/ws',
    token,
    (event) => {
        switch (event.type) {
            case EventType.TASK_UPDATE:
                // Update UI with new task state
                break;
            case EventType.HUMAN_INPUT_NEEDED:
                // Prompt user for input
                break;
            case EventType.ERROR:
                // Handle error
                break;
        }
    }
);
```

3. Clean up resources:
```typescript
// When done with the client
client.disconnect();
```

## Environment Variables

The server expects the following environment variables:

```env
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
CORS_ORIGINS=["http://localhost:3000"]
```

## Development

```bash
# Install dependencies
npm install

# Build the client
npm run build

# Run tests
npm test

# Run linting
npm run lint
```

## License

MIT 