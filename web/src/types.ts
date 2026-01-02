export interface AgentMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content?: string;
    thoughts?: string[]; // Internal monologue/reasoning
    toolCalls?: ToolCall[];
    timestamp: number;
}

export interface ToolCall {
    id: string;
    name: string;
    args: any;
    status: 'running' | 'completed' | 'failed';
    result?: string;
}

export interface WidgetManifest {
    id: string;
    title: string;
    url: string;
    dimensions: {
        w: number;
        h: number;
    };
    code?: string;
}
