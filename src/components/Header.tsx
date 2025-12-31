import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

export function Header() {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => {
            setTime(new Date());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const formatDate = (date: Date) => {
        return date.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' });
    };

    return (
        <header className="fixed top-0 left-0 right-0 z-40 px-8 py-6 flex items-center justify-between pointer-events-none">
            {/* Branding */}
            <div className="flex items-center gap-3 pointer-events-auto">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#dda15e] to-[#bc6c4b] flex items-center justify-center shadow-lg transform -rotate-2">
                    <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-[#4a4e4d] tracking-tight leading-none">DeepHome</h1>
                    <span className="text-[10px] font-bold text-[#bc6c4b] uppercase tracking-[0.2em]">FAMILY OS</span>
                </div>
            </div>

            {/* Clock */}
            <div className="flex flex-col items-end pointer-events-auto">
                <div className="text-4xl font-black text-[#4a4e4d] tracking-tighter leading-none tabular-nums">
                    {formatTime(time)}
                </div>
                <div className="text-[11px] font-bold text-[#a3b18a] uppercase tracking-widest mt-1">
                    {formatDate(time)}
                </div>
            </div>
        </header>
    );
}
