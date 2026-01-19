import { useState, useCallback } from 'react';
import type { AgentMessage } from '../../../types';
import { useSSE } from '../../../core/hooks/useSSE';

export interface UseAgentSessionProps {
    initialSessionId?: string | null;
}

export function useAgentSession({ initialSessionId }: UseAgentSessionProps = {}) {
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(initialSessionId || null);
    const [messages, setMessages] = useState<AgentMessage[]>([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [isComplete, setIsComplete] = useState(false);
    const [lastPreview, setLastPreview] = useState<any>(null);

    // 1. Persistent Event Channel
    useSSE({
        url: currentSessionId ? `http://localhost:8000/agent/events/${currentSessionId}` : '',
        enabled: !!currentSessionId,
        onMessage: (event) => {
            const { type, payload } = event;
            switch (type) {
                case 'preview':
                    console.log("[EventStream] Received preview:", payload);
                    setLastPreview(payload);
                    break;
                case 'status':
                    console.log("[EventStream] Status:", payload);
                    break;
                case 'error':
                    console.error("[EventStream] Error:", payload);
                    break;
            }
        }
    });

    const loadHistory = useCallback(async (sessionId: string) => {
        try {
            const res = await fetch(`http://localhost:8000/agent/history/${sessionId}`);
            if (res.ok) {
                const history = await res.json();
                const formattedHistory = history.map((msg: any, i: number) => ({
                    id: `hist-${i}`,
                    role: msg.role,
                    content: msg.content,
                    toolCalls: msg.tool_calls ? msg.tool_calls.map((tc: any) => ({
                        id: tc.payload ? JSON.parse(tc.payload).id : 'unknown',
                        name: tc.payload ? JSON.parse(tc.payload).name : 'unknown',
                        args: tc.payload ? JSON.parse(tc.payload).args : {},
                        status: 'completed',
                        result: 'Executed'
                    })) : [],
                    timestamp: Date.now()
                }));
                setMessages(formattedHistory);
            }
        } catch (e) {
            console.error("Failed to fetch history:", e);
        }
    }, []);

    const startSession = useCallback((sessionId: string) => {
        setCurrentSessionId(sessionId);
        setMessages([]);
        setLastPreview(null);
        setIsComplete(false);
    }, []);

    const sendMessage = useCallback(async (prompt: string) => {
        console.log("Submitting prompt:", prompt);
        setIsGenerating(true);
        setIsComplete(false);
        setLastPreview(null);

        let sessionId = currentSessionId;
        if (!sessionId) {
            sessionId = Date.now().toString();
            setCurrentSessionId(sessionId);
        }

        const userMsg: AgentMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: prompt,
            timestamp: Date.now()
        };

        const assistantMsgId = (Date.now() + 1).toString();
        const assistantMsg: AgentMessage = {
            id: assistantMsgId,
            role: 'assistant',
            content: '',
            thoughts: [],
            toolCalls: [],
            timestamp: Date.now()
        };

        setMessages(prev => [...prev, userMsg, assistantMsg]);

        try {
            const evtSource = new EventSource(`http://localhost:8000/agent/query?prompt=${encodeURIComponent(prompt)}&session_id=${sessionId}`);

            evtSource.onmessage = (event) => {
                try {
                    const parsed = JSON.parse(event.data);
                    const { type, payload } = parsed;

                    setMessages(prev => {
                        const index = prev.findIndex(m => m.id === assistantMsgId);
                        if (index === -1) return prev;
                        const activeMsg = { ...prev[index] };

                        switch (type) {
                            case 'log':
                            case 'status':
                                console.log('[Agent Log]', payload);
                                break;
                            case 'reasoning':
                                activeMsg.thoughts = [...(activeMsg.thoughts || [])];
                                if (activeMsg.thoughts.length === 0) {
                                    activeMsg.thoughts.push(payload);
                                } else {
                                    const lastIdx = activeMsg.thoughts.length - 1;
                                    activeMsg.thoughts[lastIdx] = activeMsg.thoughts[lastIdx] + payload;
                                }
                                break;
                            case 'chunk':
                            case 'response':
                                activeMsg.content = (activeMsg.content || '') + payload;
                                break;
                            case 'tool_call':
                                const toolData = JSON.parse(payload);
                                activeMsg.toolCalls = [...(activeMsg.toolCalls || []), {
                                    id: Date.now().toString(),
                                    name: toolData.name,
                                    args: toolData.args,
                                    status: 'running' as const
                                }];
                                break;
                            case 'done':
                                setIsGenerating(false);
                                setIsComplete(true);
                                evtSource.close();
                                break;
                            case 'error':
                                activeMsg.content = (activeMsg.content || '') + `\n\n[ERROR]: ${payload}`;
                                setIsGenerating(false);
                                evtSource.close();
                                break;
                        }
                        const newHistory = [...prev];
                        newHistory[index] = activeMsg;
                        return newHistory;
                    });

                } catch (e) {
                    console.error("Parse error", e);
                }
            };

            evtSource.onerror = (err) => {
                console.error("SSE Error:", err);
                setIsGenerating(false);
                evtSource.close();
            };

        } catch (e) {
            console.error("Agent failed:", e);
            setIsGenerating(false);
        }
    }, [currentSessionId]);

    return {
        currentSessionId,
        messages,
        setMessages,
        isGenerating,
        isComplete,
        setIsComplete,
        lastPreview,
        setLastPreview,
        actions: {
            sendMessage,
            startSession,
            loadHistory
        }
    };
}
