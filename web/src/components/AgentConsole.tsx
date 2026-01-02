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
        <div className="bg-white/40 rounded-lg border border-black/5 overflow-hidden text-xs my-2 shadow-sm">
            <div
                className="flex items-center gap-2 p-2 cursor-pointer hover:bg-white/60 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <Terminal className="w-3 h-3 text-[var(--terracotta)]" />
                <span className="font-mono text-[#4a4e4d]/80">Run: {tool.name}</span>
                {tool.status === 'running' && <Loader2 className="w-3 h-3 animate-spin ml-auto text-[#4a4e4d]/50" />}
                {tool.status === 'completed' && <Check className="w-3 h-3 ml-auto text-[var(--sage-green)]" />}
                {tool.status === 'failed' && <X className="w-3 h-3 ml-auto text-red-500" />}
            </div>
            {isExpanded && (
                <div className="p-2 border-t border-black/5 bg-white/30 font-mono text-[#4a4e4d]/70 whitespace-pre-wrap break-all">
                    <div>Args: {JSON.stringify(tool.args, null, 2)}</div>
                    {tool.result && <div className="mt-2 text-[var(--sage-green)] font-semibold">Result: {tool.result}</div>}
                </div>
            )}
        </div>
    );
};

const ThoughtProcess = ({ thoughts }: { thoughts: string[] }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    if (!thoughts.length) return null;

    return (
        <div className="my-2 border-l-2 border-[var(--mustard)]/50 pl-3">
            <div
                className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity mb-1"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                {isExpanded ? <ChevronDown className="w-3 h-3 text-[var(--mustard)]" /> : <ChevronRight className="w-3 h-3 text-[var(--mustard)]" />}
                <span className="text-xs font-mono text-[var(--mustard)] uppercase tracking-wider">Reasoning</span>
            </div>
            {isExpanded && (
                <div className="text-sm text-[#4a4e4d]/60 space-y-1 font-serif italic">
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
        <div className="flex w-full h-full overflow-hidden bg-[#fefae0]">

            {/* LEFT COLUMN: Chat Interface */}
            <div className="w-[450px] flex-shrink-0 flex flex-col border-r border-black/5 bg-white/30 backdrop-blur-sm">
                {/* Header */}
                <div className="p-4 border-b border-black/5 flex items-center justify-between bg-white/40">
                    <div className="flex items-center gap-2 text-[var(--warm-charcoal)]">
                        <button
                            onClick={props.onClose}
                            className="p-1 hover:bg-black/5 rounded-full transition-colors mr-1"
                            title="Back to Dashboard"
                        >
                            <X className="w-5 h-5 text-[#4a4e4d]/50 hover:text-[#4a4e4d]" />
                        </button>
                        <Bot className="w-5 h-5 text-[var(--sage-green)]" />
                        <span className="font-bold text-sm">Deephome AI</span>
                    </div>
                    {isGenerating && <span className="text-xs text-[var(--terracotta)] font-mono animate-pulse">GENERATING...</span>}
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-black/5 hover:scrollbar-thumb-black/10" ref={scrollRef}>
                    {messages.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-center opacity-40 mt-20">
                            <Sparkles className="w-12 h-12 mb-4 text-[var(--mustard)]" />
                            <h3 className="text-lg font-medium text-[var(--warm-charcoal)]">How can I help you?</h3>
                            <p className="text-sm max-w-xs mt-2 text-[var(--warm-charcoal)]">I can generate widgets, research topics, or answer questions.</p>
                        </div>
                    )}

                    {messages.map((msg) => (
                        <div key={msg.id} className={`flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                            <div className={`flex items-center gap-2 mb-1 opacity-50 text-[10px] font-mono uppercase tracking-widest text-[#4a4e4d] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                <span>{msg.role}</span>
                                <span className="text-black/10">|</span>
                                <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>

                            <div className={`max-w-[95%] ${msg.role === 'user' ? 'flex justify-end' : 'w-full'}`}>
                                {msg.role === 'user' ? (
                                    <div className="bg-white/80 text-[var(--warm-charcoal)] px-4 py-3 rounded-2xl rounded-tr-sm shadow-sm border border-black/5 text-sm leading-relaxed">
                                        {msg.content}
                                    </div>
                                ) : (
                                    <div className="w-full space-y-2">
                                        {msg.thoughts && <ThoughtProcess thoughts={msg.thoughts} />}

                                        {msg.toolCalls?.map(tool => (
                                            <ToolCallItem key={tool.id} tool={tool} />
                                        ))}

                                        {msg.content && (
                                            <div className="text-[var(--warm-charcoal)] text-sm leading-relaxed pl-1 max-w-none prose prose-p:my-1 prose-headings:my-2 prose-code:text-[var(--terracotta)] prose-code:bg-black/5 prose-code:rounded prose-code:px-1 prose-code:before:content-none prose-code:after:content-none">
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
                            <Loader2 className="w-4 h-4 animate-spin text-[var(--terracotta)]" />
                            <span className="text-xs text-[var(--terracotta)]">Thinking...</span>
                        </div>
                    )}

                    {/* Padding for bottom input */}
                    <div className="h-4" />
                </div>

                {/* Input Area */}
                <div className="p-4 bg-white/40 border-t border-black/5">
                    <ChatInput onSubmit={onSendMessage} className="max-w-full px-0 shadow-sm border-black/5 bg-white/80 focus-within:ring-[var(--sage-green)] text-[var(--warm-charcoal)] placeholder:text-black/20" />
                </div>
            </div>

            {/* RIGHT COLUMN: Preview / Widget Area */}
            <div className="flex-1 flex flex-col bg-[#fefae0]/50 relative shadow-[inset_10px_0_30px_rgba(0,0,0,0.02)]">

                {/* Preview Header */}
                <div className="h-14 border-b border-black/5 flex items-center justify-between px-6 bg-white/30">
                    <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-[var(--sage-green)] shadow-[0_0_8px_rgba(163,177,138,0.4)]"></div>
                        <span className="text-xs font-mono text-[#4a4e4d]/50 tracking-widest">LIVE PREVIEW</span>
                    </div>

                    {isComplete && (previewUrl || previewCode) && (
                        <div className="flex items-center gap-3">
                            <button onClick={onConfirm} className="flex items-center gap-2 bg-[var(--terracotta)] hover:bg-[#a65d40] text-white px-4 py-1.5 rounded-full text-xs font-medium transition-colors shadow-lg shadow-[var(--terracotta)]/20">
                                <Check className="w-3 h-3" />
                                Deploy Widget
                            </button>
                        </div>
                    )}
                </div>

                {/* Preview Content */}
                <div className="flex-1 overflow-hidden relative flex items-center justify-center p-8 text-[#4a4e4d]">
                    {previewCode ? (
                        <div className="w-full h-full relative group">
                            {/* Wrapper to constrain layout */}
                            <div className="w-full h-full bg-white/60 backdrop-blur-xl border border-white/40 rounded-3xl overflow-hidden shadow-sm ring-1 ring-black/5">
                                <DynamicWidget code={previewCode} />
                            </div>
                        </div>
                    ) : previewUrl ? (
                        <div className="w-full h-full bg-white rounded-lg shadow-sm overflow-hidden ring-1 ring-black/5 animate-in fade-in zoom-in-95 duration-500">
                            <iframe
                                src={`http://localhost:8000${previewUrl}`}
                                className="w-full h-full border-0"
                                title="Generated Widget"
                            />
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center text-[#4a4e4d]/20 space-y-4">
                            <div className="w-24 h-24 rounded-full border-2 border-dashed border-[#4a4e4d]/10 flex items-center justify-center">
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
