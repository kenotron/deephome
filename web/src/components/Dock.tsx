import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, Mic } from 'lucide-react';

export interface DockProps {
    onSubmit?: (val: string) => void;
}

export function Dock({ onSubmit }: DockProps) {
    const [input, setInput] = useState('');

    const handleSubmit = () => {
        if (!input.trim()) return;
        onSubmit?.(input);
        setInput('');
    };

    return (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl px-4">
            <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="relative group pointer-events-auto"
            >
                <div className="absolute -inset-0.5 bg-gradient-to-r from-pink-500/20 via-purple-500/20 to-blue-500/20 rounded-full blur opacity-75 group-hover:opacity-100 transition duration-1000"></div>
                <div className="relative flex items-center bg-white/60 backdrop-blur-2xl border border-black/5 rounded-[2rem] p-2 shadow-[0_20px_50px_rgba(0,0,0,0.1)]">

                    <button className="p-3 rounded-2xl hover:bg-black/5 transition-all text-[#dda15e] active:scale-95">
                        <Sparkles className="w-6 h-6" />
                    </button>

                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask family agent, automate tasks, find apps..."
                        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                        className="flex-1 bg-transparent border-none outline-none text-[#4a4e4d] placeholder-[#4a4e4d]/30 px-4 text-base font-medium"
                    />

                    <div className="flex items-center gap-1">
                        <button className="p-3 rounded-xl hover:bg-black/5 transition-all text-[#4a4e4d]/40 hover:text-[#4a4e4d]">
                            <Mic className="w-5 h-5" />
                        </button>
                        <button
                            onClick={handleSubmit}
                            className="p-3 bg-[#dda15e] text-white rounded-xl shadow-lg hover:shadow-xl transition-all active:scale-95 ml-1"
                        >
                            <ArrowRight className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
