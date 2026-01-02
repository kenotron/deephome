import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, Mic } from 'lucide-react';

export interface ChatInputProps {
    onSubmit?: (val: string) => void;
    className?: string;
}

export function ChatInput({ onSubmit, className }: ChatInputProps) {
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSubmit = () => {
        if (!input.trim()) return;
        onSubmit?.(input);
        setInput('');

        // Reset height
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [input]);

    return (
        <div className={`w-full max-w-4xl mx-auto px-4 ${className}`}>
            <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="relative group"
            >
                <div className="absolute -inset-0.5 bg-gradient-to-r from-[var(--terracotta)]/20 via-[var(--mustard)]/20 to-[var(--sage-green)]/20 rounded-2xl blur opacity-75 group-hover:opacity-100 transition duration-1000"></div>
                <div className="relative flex flex-col bg-white/80 border border-black/5 rounded-2xl p-2 shadow-sm ring-1 ring-black/5">

                    <div className="flex items-start gap-2">
                        <div className="pt-2 pl-2">
                            <Sparkles className="w-5 h-5 text-[var(--terracotta)]" />
                        </div>

                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Describe the widget you want to build..."
                            onKeyDown={handleKeyDown}
                            rows={1}
                            className="flex-1 bg-transparent border-none outline-none text-[#4a4e4d] placeholder-[#4a4e4d]/30 px-3 py-2 text-base font-medium resize-none max-h-[200px] overflow-y-auto"
                        />

                        <div className="flex items-center gap-1 pt-1 pr-1">
                            <button className="p-2 rounded-lg hover:bg-black/5 transition-colors text-[#4a4e4d]/50 hover:text-[#4a4e4d]" disabled>
                                <Mic className="w-5 h-5" />
                            </button>
                            <button
                                className={`p-2 rounded-lg transition-colors ml-1 ${input.trim() ? 'bg-[var(--terracotta)] hover:bg-[#a65d40] text-white shadow-md' : 'bg-black/5 text-black/20 cursor-not-allowed'}`}
                                onClick={handleSubmit}
                                disabled={!input.trim()}
                            >
                                <ArrowRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    <div className="px-4 pb-2 pt-1 flex justify-between items-center text-[10px] text-[#4a4e4d]/40 font-mono">
                        <span>Deephome Agent</span>
                        <span>Return to send, Shift+Return for new line</span>
                    </div>

                </div>
            </motion.div>
        </div>
    );
}
