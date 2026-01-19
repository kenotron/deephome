import { useState } from 'react';
import { AgentConsole } from '../modules/agent';
import type { AgentMessage } from '../types';

export function TestAgentPage() {
    const [messages, setMessages] = useState<AgentMessage[]>([]);
    const [isGenerating, setIsGenerating] = useState(false);

    // Mock Agent Logic
    const handleSendMessage = (text: string) => {
        const userMsg: AgentMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: text,
            timestamp: Date.now()
        };
        setMessages(prev => [...prev, userMsg]);
        setIsGenerating(true);

        // Simulate response
        setTimeout(() => {
            const assistantMsg: AgentMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "This is a mock response from the Integration Test page. I am isolated from the backend.",
                thoughts: ["Thinking about integration tests...", "Verifying UI state..."],
                toolCalls: [],
                timestamp: Date.now()
            };
            setMessages(prev => [...prev, assistantMsg]);
            setIsGenerating(false);
        }, 1000);
    };

    return (
        <div className="h-screen w-full">
            <AgentConsole
                messages={messages}
                isGenerating={isGenerating}
                isComplete={false}
                onConfirm={() => alert("Deploy clicked (Mock)")}
                onSendMessage={handleSendMessage}
                onClose={() => console.log("Close clicked")}
            />
        </div>
    );
}
