import { useState, useEffect } from 'react';
import { LayoutGrid, Check } from 'lucide-react';

interface HeaderProps {
    isEditMode?: boolean;
    onToggleEditMode?: () => void;
}

export function Header({ isEditMode, onToggleEditMode }: HeaderProps) {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => {
            setTime(new Date());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    };

    return (
        <header className="fixed top-0 left-0 right-0 z-40 px-8 py-6 flex items-center justify-between pointer-events-none">
            {/* Left: Time & Status */}
            <div className="flex items-center gap-3 pointer-events-auto text-[#4a4e4d]">
                <div className="text-xl font-medium tracking-tight leading-none tabular-nums">
                    {formatTime(time)}
                </div>
                <div className="w-1 h-1 rounded-full bg-[#4a4e4d]/50" />
                <div className="text-xl font-medium tracking-tight leading-none opacity-80">
                    Focus Mode On
                </div>
            </div>

            {/* Right: Controls & User */}
            <div className="flex items-center gap-4 pointer-events-auto">
                {/* Mode Toggle */}
                <button
                    onClick={onToggleEditMode}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full font-bold text-xs uppercase tracking-wider transition-all shadow-sm ${isEditMode
                        ? 'bg-[var(--terracotta)] text-white hover:bg-[#a65d40] shadow-md ring-2 ring-[var(--terracotta)]/20'
                        : 'bg-white/50 text-[#4a4e4d]/70 hover:bg-white/80 hover:text-[#4a4e4d] border border-black/5'
                        }`}
                >
                    {isEditMode ? <Check className="w-4 h-4" /> : <LayoutGrid className="w-4 h-4" />}
                    {isEditMode ? 'Done' : 'Edit Layout'}
                </button>

                {/* User Avatar */}
                <div className="w-10 h-10 rounded-full bg-gray-200 overflow-hidden border-2 border-white shadow-sm hover:scale-105 transition-transform cursor-pointer">
                    <img
                        src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix"
                        alt="User"
                        className="w-full h-full object-cover"
                    />
                </div>
            </div>
        </header>
    );
}
