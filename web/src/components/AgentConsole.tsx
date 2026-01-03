import { useRef, useEffect, useState } from 'react';
import { X, Check, Loader2, Sparkles, Bot, Terminal, ChevronRight, ChevronDown } from 'lucide-react';
import type { AgentMessage, ToolCall } from '../types';
import { ChatInput } from './ChatInput';
import { Streamdown } from 'streamdown';
import { DynamicWidget } from './DynamicWidget';

export interface AgentConsoleProps {
    isOpen?: boolean;
    onClose?: () => void;
    messages: AgentMessage[];
    isGenerating: boolean;
    isComplete: boolean;
    onConfirm: () => void;
    onSendMessage: (message: string) => void;
    previewUrl?: string;
    previewCode?: string;
    isEditingExisting?: boolean;
    dimensions?: { w: number; h: number };
}

// ... existing components ...

export function AgentConsole(props: AgentConsoleProps) {
    const { messages, isGenerating, isComplete, onConfirm, onSendMessage, previewUrl, previewCode, isEditingExisting, dimensions } = props;
    const scrollRef = useRef<HTMLDivElement>(null);

    // ... useEffect ...

    // Calculate dimensions for preview
    // Base unit approx: w=250px (mobile/desktop avg), h=180px (from Grid.tsx)
    // We add margin compensation.
    // If no dimensions provided, default to full or 2x2.
    const previewStyle = dimensions ? {
        width: `${dimensions.w * 280}px`, // Slightly larger than typical minimal col
        height: `${dimensions.h * 180 + (dimensions.h - 1) * 10}px`,
        maxWidth: '100%',
        maxHeight: '100%',
    } : { width: '100%', height: '100%' };

    return (
        <div className="flex w-full h-full overflow-hidden bg-[#fefae0]">
            {/* Left Column code unchanged ... */}
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
                        {dimensions && (
                            <span className="text-[10px] bg-black/5 px-2 py-0.5 rounded text-[#4a4e4d]/40 ml-2">
                                {dimensions.w}x{dimensions.h} grid units
                            </span>
                        )}
                    </div>

                    {isComplete && (previewUrl || previewCode) && (
                        <div className="flex items-center gap-3">
                            <button onClick={onConfirm} className="flex items-center gap-2 bg-[var(--terracotta)] hover:bg-[#a65d40] text-white px-4 py-1.5 rounded-full text-xs font-medium transition-colors shadow-lg shadow-[var(--terracotta)]/20">
                                <Check className="w-3 h-3" />
                                {isEditingExisting ? 'Update Widget' : 'Deploy Widget'}
                            </button>
                        </div>
                    )}
                </div>

                {/* Preview Content */}
                <div className="flex-1 overflow-auto relative flex items-center justify-center p-8 text-[#4a4e4d]">
                    {previewUrl ? (
                        <div style={previewStyle} className="bg-white rounded-lg shadow-sm overflow-hidden ring-1 ring-black/5 animate-in fade-in zoom-in-95 duration-500 transition-all">
                            <iframe
                                src={`http://localhost:8000${previewUrl}`}
                                className="w-full h-full border-0"
                                title="Generated Widget"
                            />
                        </div>
                    ) : previewCode ? (
                        <div style={previewStyle} className="relative group transition-all">
                            {/* Wrapper to constrain layout */}
                            <div className="w-full h-full bg-white/60 backdrop-blur-xl border border-white/40 rounded-3xl overflow-hidden shadow-sm ring-1 ring-black/5 flex flex-col">
                                <DynamicWidget code={previewCode} />
                            </div>
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
