import { io, Socket } from 'socket.io-client';

// Event Types
export enum EventType {
    TASK_UPDATE = 'task_update',
    STEP_UPDATE = 'step_update',
    HUMAN_INPUT_NEEDED = 'human_input_needed',
    ERROR = 'error',
    STATUS = 'status'
}

// Command Types
export enum CommandType {
    ADD_TASK = 'add_task',
    MODIFY_TASK = 'modify_task',
    PAUSE = 'pause',
    RESUME = 'resume',
    STOP = 'stop',
    HUMAN_INPUT = 'human_input'
}

// Event Interfaces
export interface ConnectionStatus {
    status: string;
    message: string;
}

export interface Task {
    task_id: string;
    description: string;
    current_goal: string;
    details: string[];
    notes: string[];
    steps: Step[];
    scratchpad_path: string;
    max_retries: number;
}

export interface Step {
    description: string;
    reasoning: string;
    status: 'open' | 'in-progress' | 'completed' | 'failed' | 'human';
    failure_details?: string;
    retry_count: number;
}

export interface TaskEvent {
    type: EventType.TASK_UPDATE;
    task: Task;
}

export interface StepEvent {
    type: EventType.STEP_UPDATE;
    task_id: string;
    step_index: number;
    step: Step;
}

export interface HumanInputEvent {
    type: EventType.HUMAN_INPUT_NEEDED;
    task_id: string;
    step_index: number;
    prompt: string;
    options?: string[];
}

export interface ErrorEvent {
    type: EventType.ERROR;
    message: string;
    details?: Record<string, any>;
}

// Command Interfaces
export interface AddTaskCommand {
    type: CommandType.ADD_TASK;
    description: string;
    goal?: string;
}

export interface ModifyTaskCommand {
    type: CommandType.MODIFY_TASK;
    task_id: string;
    description?: string;
    goal?: string;
}

export interface HumanInputCommand {
    type: CommandType.HUMAN_INPUT;
    task_id: string;
    step_index: number;
    input: string;
}

export interface ControlCommand {
    type: CommandType.PAUSE | CommandType.RESUME | CommandType.STOP;
}

export type AgentEvent = TaskEvent | StepEvent | HumanInputEvent | ErrorEvent;
export type AgentCommand = AddTaskCommand | ModifyTaskCommand | HumanInputCommand | ControlCommand;

export class AgentClient {
    private socket: Socket;
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;
    private reconnectDelay: number = 1000; // Start with 1 second

    constructor(
        private url: string,
        private token: string,
        private onEvent?: (event: AgentEvent) => void,
        private onConnectionStatus?: (status: ConnectionStatus) => void,
        private onError?: (error: Error) => void
    ) {
        this.socket = this.createSocket();
    }

    private createSocket(): Socket {
        const socket = io(this.url, {
            auth: {
                token: this.token
            },
            reconnection: true,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: this.reconnectDelay,
            reconnectionDelayMax: 5000
        });

        // Setup event handlers
        socket.on('connect', () => {
            this.reconnectAttempts = 0;
            this.onConnectionStatus?.({
                status: 'connected',
                message: 'Connected to agent'
            });
        });

        socket.on('disconnect', (reason) => {
            this.onConnectionStatus?.({
                status: 'disconnected',
                message: `Disconnected: ${reason}`
            });
        });

        socket.on('connect_error', (error) => {
            this.reconnectAttempts++;
            this.onError?.(error);
            
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                socket.disconnect();
                this.onConnectionStatus?.({
                    status: 'failed',
                    message: 'Failed to connect after maximum attempts'
                });
            }
        });

        // Handle agent events
        socket.on('status', (status: ConnectionStatus) => {
            this.onConnectionStatus?.(status);
        });

        socket.on('event', (event: AgentEvent) => {
            this.onEvent?.(event);
        });

        return socket;
    }

    public isConnected(): boolean {
        return this.socket.connected;
    }

    public connect(): void {
        if (!this.socket.connected) {
            this.socket.connect();
        }
    }

    public disconnect(): void {
        this.socket.disconnect();
    }

    public async sendCommand(command: AgentCommand): Promise<void> {
        if (!this.socket.connected) {
            throw new Error('Not connected to agent');
        }

        return new Promise((resolve, reject) => {
            this.socket.emit('command', command, (response: { error?: string }) => {
                if (response.error) {
                    reject(new Error(response.error));
                } else {
                    resolve();
                }
            });
        });
    }

    public async addTask(description: string, goal?: string): Promise<void> {
        return this.sendCommand({
            type: CommandType.ADD_TASK,
            description,
            goal
        });
    }

    public async modifyTask(taskId: string, description?: string, goal?: string): Promise<void> {
        return this.sendCommand({
            type: CommandType.MODIFY_TASK,
            task_id: taskId,
            description,
            goal
        });
    }

    public async sendHumanInput(taskId: string, stepIndex: number, input: string): Promise<void> {
        return this.sendCommand({
            type: CommandType.HUMAN_INPUT,
            task_id: taskId,
            step_index: stepIndex,
            input
        });
    }

    public async pause(): Promise<void> {
        return this.sendCommand({ type: CommandType.PAUSE });
    }

    public async resume(): Promise<void> {
        return this.sendCommand({ type: CommandType.RESUME });
    }

    public async stop(): Promise<void> {
        return this.sendCommand({ type: CommandType.STOP });
    }
} 