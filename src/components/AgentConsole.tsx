import { useRef, useEffect, useState } from 'react';
import { X, Check, Loader2, Sparkles, Bot, Terminal, ChevronRight, ChevronDown } from 'lucide-react';
import type { AgentMessage, ToolCall } from '../types';
import { ChatInput } from './ChatInput';
import { Streamdown } from 'streamdown';
import { DynamicWidget } from './DynamicWidget';

export interface AgentConsoleProps {
    isOpen?: boolean; // Kept for compat, but unused in new layout ideally
    onClose?: () => void;
    messages: AgentMessage[];
    isGenerating: boolean;
    isComplete: boolean;
    onConfirm: () => void;
    onSendMessage: (message: string) => void;
    previewUrl?: string;
    previewCode?: string;
}

const ToolCallItem = ({ tool }: { tool: ToolCall }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    return (
        <div className="bg-black/40 rounded border border-white/10 overflow-hidden text-xs my-2">
            <div
                className="flex items-center gap-2 p-2 cursor-pointer hover:bg-white/5 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <Terminal className="w-3 h-3 text-purple-400" />
                <span className="font-mono text-purple-300">Run: {tool.name}</span>
                {tool.status === 'running' && <Loader2 className="w-3 h-3 animate-spin ml-auto text-white/50" />}
                {tool.status === 'completed' && <Check className="w-3 h-3 ml-auto text-green-500" />}
                {tool.status === 'failed' && <X className="w-3 h-3 ml-auto text-red-500" />}
            </div>
            {isExpanded && (
                <div className="p-2 border-t border-white/10 bg-black/50 font-mono text-white/60 whitespace-pre-wrap break-all">
                    <div>Args: {JSON.stringify(tool.args, null, 2)}</div>
                    {tool.result && <div className="mt-2 text-green-400/80">Result: {tool.result}</div>}
                </div>
            )}
        </div>
    );
};

const ThoughtProcess = ({ thoughts }: { thoughts: string[] }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    if (!thoughts.length) return null;

    return (
        <div className="my-2 border-l-2 border-yellow-500/30 pl-3">
            <div
                className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity mb-1"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                {isExpanded ? <ChevronDown className="w-3 h-3 text-yellow-500/50" /> : <ChevronRight className="w-3 h-3 text-yellow-500/50" />}
                <span className="text-xs font-mono text-yellow-500/50 uppercase tracking-wider">Reasoning</span>
            </div>
            {isExpanded && (
                <div className="text-sm text-yellow-100/60 space-y-1 font-serif italic">
                    {thoughts.map((t, i) => (
                        <p key={i}>{t}</p>
                    ))}
                </div>
            )}
        </div>
    );
};

export function AgentConsole(props: AgentConsoleProps) {
    const { messages, isGenerating, isComplete, onConfirm, onSendMessage, previewUrl, previewCode } = props;
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div className="flex w-full h-full overflow-hidden bg-[#0f0f0f]">

            {/* LEFT COLUMN: Chat Interface */}
            <div className="w-[450px] flex-shrink-0 flex flex-col border-r border-white/5 bg-[#111]">
                {/* Header */}
                <div className="p-4 border-b border-white/5 flex items-center justify-between bg-[#111]">
                    <div className="flex items-center gap-2 text-purple-400">
                        <button
                            onClick={props.onClose}
                            className="p-1 hover:bg-white/10 rounded-full transition-colors mr-1"
                            title="Back to Dashboard"
                        >
                            <X className="w-5 h-5 text-white/50 hover:text-white" />
                        </button>
                        <Bot className="w-5 h-5" />
                        <span className="font-bold text-sm text-white/90">Deephome AI</span>
                    </div>
                    {isGenerating && <span className="text-xs text-white/30 font-mono animate-pulse">GENERATING...</span>}
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-white/10 hover:scrollbar-thumb-white/20" ref={scrollRef}>
                    {messages.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-center opacity-30 mt-20">
                            <Sparkles className="w-12 h-12 mb-4 text-purple-500" />
                            <h3 className="text-lg font-medium">How can I help you?</h3>
                            <p className="text-sm max-w-xs mt-2">I can generate widgets, research topics, or answer questions.</p>
                        </div>
                    )}

                    {messages.map((msg) => (
                        <div key={msg.id} className={`flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                            <div className={`flex items-center gap-2 mb-1 opacity-50 text-[10px] font-mono uppercase tracking-widest ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                <span>{msg.role}</span>
                                <span className="text-white/20">|</span>
                                <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>

                            <div className={`max-w-[95%] ${msg.role === 'user' ? 'flex justify-end' : 'w-full'}`}>
                                {msg.role === 'user' ? (
                                    <div className="bg-[#2a2a2a] text-white px-4 py-3 rounded-2xl rounded-tr-sm shadow-sm border border-white/5 text-sm leading-relaxed">
                                        {msg.content}
                                    </div>
                                ) : (
                                    <div className="w-full space-y-2">
                                        {msg.thoughts && <ThoughtProcess thoughts={msg.thoughts} />}

                                        {msg.toolCalls?.map(tool => (
                                            <ToolCallItem key={tool.id} tool={tool} />
                                        ))}

                                        {msg.content && (
                                            <div className="text-gray-300 text-sm leading-relaxed pl-1 max-w-none">
                                                <Streamdown>{msg.content}</Streamdown>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {isGenerating && (
                        <div className="flex items-center gap-2 pl-2 opacity-50 py-2">
                            <Loader2 className="w-4 h-4 animate-spin text-purple-500" />
                            <span className="text-xs text-purple-400">Thinking...</span>
                        </div>
                    )}

                    {/* Padding for bottom input */}
                    <div className="h-4" />
                </div>

                {/* Input Area */}
                <div className="p-4 bg-[#111] border-t border-white/5">
                    <ChatInput onSubmit={onSendMessage} className="max-w-full px-0" />
                </div>
            </div>

            {/* RIGHT COLUMN: Preview / Widget Area */}
            <div className="flex-1 flex flex-col bg-[#050505] relative shadow-[inset_10px_0_30px_rgba(0,0,0,0.5)]">

                {/* Preview Header */}
                <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#0a0a0a]">
                    <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]"></div>
                        <span className="text-xs font-mono text-white/50 tracking-widest">LIVE PREVIEW</span>
                    </div>

                    {isComplete && (previewUrl || previewCode) && (
                        <div className="flex items-center gap-3">
                            <button onClick={onConfirm} className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white px-4 py-1.5 rounded-full text-xs font-medium transition-colors shadow-lg shadow-purple-900/20">
                                <Check className="w-3 h-3" />
                                Deploy Widget
                            </button>
                        </div>
                    )}
                </div>

                {/* Preview Content */}
                <div className="flex-1 overflow-hidden relative flex items-center justify-center p-8 text-white">
                    {previewCode ? (
                        <div className="w-full h-full relative group">
                            {/* Wrapper to constrain layout */}
                            <div className="w-full h-full bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl ring-1 ring-white/5">
                                <DynamicWidget code={previewCode} />
                            </div>
                        </div>
                    ) : previewUrl ? (
                        <div className="w-full h-full bg-white rounded-lg shadow-2xl overflow-hidden ring-1 ring-white/10 animate-in fade-in zoom-in-95 duration-500">
                            <iframe
                                src={`http://localhost:8000${previewUrl}`}
                                className="w-full h-full border-0"
                                title="Generated Widget"
                            />
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center text-white/10 space-y-4">
                            <div className="w-24 h-24 rounded-full border-2 border-dashed border-white/10 flex items-center justify-center">
                                <Terminal className="w-10 h-10" />
                            </div>
                            <p className="font-mono text-sm max-w-md text-center">
                                No active preview. Generate a widget to see it here.
                            </p>
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
}
