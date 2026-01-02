import { motion } from 'framer-motion';
import { cn } from '../lib/utils';
import { Settings, X } from 'lucide-react';

export interface WidgetProps {
    id: string;
    title: string;
    onDelete?: () => void;
    className?: string; // For grid-col-span, etc.
    children?: React.ReactNode;
}

export function Widget({ title, className, children, onDelete }: WidgetProps) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className={cn(
                "group relative flex flex-col overflow-hidden",
                "bg-white/80 backdrop-blur-xl border border-black/5 rounded-[2.5rem]",
                "hover:bg-white/90 hover:border-black/10 transition-all duration-500",
                "shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_20px_50px_rgba(0,0,0,0.1)]",
                className
            )}
        >
            {/* Drag Handle & Header (visible on hover) */}
            <div className="absolute top-0 left-0 right-0 p-3 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity z-10 bg-gradient-to-b from-black/50 to-transparent">
                {/* Visual drag handle area (left/center) */}
                <div className="absolute inset-0 z-0 cursor-move" />

                <span className="text-xs font-medium text-white/60 ml-1 relative z-10 pointer-events-none">{title}</span>
                <div className="flex gap-1 relative z-20">
                    <button className="p-1.5 rounded-full hover:bg-white/10 text-white/50 hover:text-white transition-colors">
                        <Settings className="w-3 h-3" />
                    </button>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete?.();
                        }}
                        className="p-1.5 rounded-full hover:bg-red-500/20 text-white/50 hover:text-red-400 transition-colors"
                    >
                        <X className="w-3 h-3" />
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 p-4 flex flex-col relative z-0">
                {children}
            </div>
        </motion.div>
    );
}
