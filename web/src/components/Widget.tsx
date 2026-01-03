import { motion } from 'framer-motion';
import { cn } from '../lib/utils';
import { Pencil, X } from 'lucide-react';

export interface WidgetProps {
    id: string;
    title: string;
    onDelete?: () => void;
    onEdit?: () => void;
    className?: string; // For grid-col-span, etc.
    children?: React.ReactNode;
    isEditMode?: boolean;
}

export function Widget({ title, className, children, onDelete, onEdit, isEditMode }: WidgetProps) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className={cn(
                "group relative flex flex-col overflow-hidden",
                "rounded-2xl", // Just rounded corners, no border/background
                isEditMode && "cursor-move",
                className
            )}
        >
            {/* Edit Controls (Only visible in Edit Mode) */}
            {isEditMode && (
                <div className="absolute top-0 right-0 p-3 flex justify-end items-center opacity-0 group-hover:opacity-100 transition-opacity z-20">
                    <div className="flex gap-1.5 bg-white/90 backdrop-blur-sm rounded-full p-1 shadow-lg border border-black/5">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit?.();
                            }}
                            className="p-2 rounded-full bg-[var(--sage-green)]/10 hover:bg-[var(--sage-green)]/20 text-[var(--sage-green)] transition-all hover:scale-110 pointer-events-auto"
                            title="Edit Widget"
                        >
                            <Pencil className="w-4 h-4" />
                        </button>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onDelete?.();
                            }}
                            className="p-2 rounded-full bg-red-500/10 hover:bg-red-500/20 text-red-500 transition-all hover:scale-110 pointer-events-auto"
                            title="Delete Widget"
                        >
                            <X className="w-4 h-4" />
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


