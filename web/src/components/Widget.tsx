import { motion } from 'framer-motion';
import { cn } from '../lib/utils';
import { Settings, X } from 'lucide-react';

export interface WidgetProps {
    id: string;
    title: string;
    onDelete?: () => void;
    className?: string; // For grid-col-span, etc.
    children?: React.ReactNode;
    isEditMode?: boolean;
}

export function Widget({ title, className, children, onDelete, isEditMode }: WidgetProps) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className={cn(
                "group relative flex flex-col overflow-hidden",
                "bg-white/80 backdrop-blur-xl border border-black/5 rounded-2xl", // Reduced radius
                // Edit Mode: Hover effects + Drag cursor
                isEditMode && "hover:bg-white/90 hover:border-black/10 hover:shadow-[0_20px_50px_rgba(0,0,0,0.1)] transition-all duration-500 cursor-move",
                !isEditMode && "shadow-[0_8px_30px_rgb(0,0,0,0.04)]",
                className
            )}
        >
            {/* Edit Controls (Only visible in Edit Mode) */}
            {isEditMode && (
                <div className="absolute top-0 right-0 p-3 flex justify-end items-center opacity-0 group-hover:opacity-100 transition-opacity z-20">
                    <div className="flex gap-1">
                        <button className="p-1.5 rounded-full bg-black/5 hover:bg-black/10 text-black/50 hover:text-black transition-colors pointer-events-auto">
                            <Settings className="w-3 h-3" />
                        </button>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onDelete?.();
                            }}
                            className="p-1.5 rounded-full bg-red-500/10 hover:bg-red-500/20 text-red-500/50 hover:text-red-500 transition-colors pointer-events-auto"
                        >
                            <X className="w-3 h-3" />
                        </button>
                    </div>
                </div>
            )}

            {/* Label (Visible on hover in Edit Mode) */}
            {isEditMode && (
                <div className="absolute top-0 left-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                    <span className="text-xs font-bold text-[#4a4e4d]/60 uppercase tracking-wider bg-white/50 px-2 py-1 rounded-lg backdrop-blur-sm">
                        {title}
                    </span>
                </div>
            )}


            {/* Content Area */}
            {/* Disable pointer events in Edit Mode so the drag works everywhere */}
            <div className={cn(
                "flex-1 p-4 flex flex-col relative z-0",
                isEditMode ? "pointer-events-none select-none" : ""
            )}>
                {children}
            </div>
        </motion.div>
    );
}


