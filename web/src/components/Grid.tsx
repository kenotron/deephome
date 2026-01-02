import { useEffect, useRef } from 'react';
import { Widget } from './Widget';
import { DynamicWidget } from './DynamicWidget';
import 'gridstack/dist/gridstack.min.css';
import { GridStack } from 'gridstack';
import { useRxCollection } from 'rxdb-hooks';

interface GridProps {
    widgets: any[];
    isEditMode: boolean;
}

export function Grid({ widgets, isEditMode }: GridProps) {
    const gridRef = useRef<GridStack | null>(null);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const refs = useRef<{ [key: string]: HTMLDivElement | null }>({});
    const collection = useRxCollection('widgets');

    // Handle Edit Mode Toggle
    useEffect(() => {
        if (gridRef.current) {
            gridRef.current.setStatic(!isEditMode);
        }
    }, [isEditMode]);

    useEffect(() => {
        if (!wrapperRef.current) return;

        // Initialize GridStack only once
        if (!gridRef.current) {
            const grid = GridStack.init({
                margin: 10,
                cellHeight: 180,
                float: true,
                column: 6,
                columnOpts: { breakpoints: [{ w: 768, c: 1 }] },
                animate: true,
                resizable: { handles: 'se' }, // Explicitly enable south-east resize
                staticGrid: !isEditMode, // Initial state
            }, wrapperRef.current);

            gridRef.current = grid;

            // --- Persistence Listener ---
            grid.on('change', (_event: Event, items: any[]) => {
                if (!collection) return;

                items.forEach(async (item) => {
                    const widgetId = item.id;
                    if (!widgetId) return;

                    // Update RxDB with new layout
                    try {
                        const doc = await collection.findOne(widgetId).exec();
                        if (doc) {
                            await doc.patch({
                                dimensions: {
                                    w: item.w,
                                    h: item.h
                                },
                                // We might need to extend schema for x,y if we want absolute positioning persistence
                                // For now, we assume standard auto-flow or check if schema has x,y
                                x: item.x,
                                y: item.y
                            });
                        }
                    } catch (err) {
                        console.error("Failed to save layout:", err);
                    }
                });
            });
        }

        const grid = gridRef.current;

        // --- Diffing & Reconciliation ---

        // 1. Remove orphaned widgets
        grid.engine.nodes.forEach(node => {
            if (!widgets.find(w => w.id === node.id)) {
                if (node.el) grid.removeWidget(node.el);
            }
        });

        // 2. Add or Update widgets
        // We use a small timeout to let React render the portals/refs first
        requestAnimationFrame(() => {
            widgets.forEach(widget => {
                const el = refs.current[widget.id];
                if (el) {
                    // Check if already in grid
                    const existingItem = grid.getGridItems().find(item => item === el);

                    if (!existingItem) {
                        // Add new widget
                        grid.makeWidget(el);
                    } else {
                        // Update widget options (optional, mostly handled by GridStack for moves)
                        // But if data changed externally (like w/h), we update it here
                        // Note: deeply updating x/y here might fight the user's drag, so be careful.
                        // We only update if verify it's a remote change or initial load sync.
                    }
                }
            });
            grid.batchUpdate(false);
            // grid.commit(); // Not needed
        });

    }, [widgets, collection]); // Depend on widgets to trigger diffing

    const handleDelete = async (id: string) => {
        if (!collection) return;
        try {
            const doc = await collection.findOne(id).exec();
            if (doc) {
                await doc.remove();
                // GridStack removal is handled by the useEffect diffing
            }
        } catch (err) {
            console.error("Failed to delete widget:", err);
        }
    };

    return (
        <div className="w-full min-h-screen p-8 pt-24 pb-32">
            <style>
                {`
                    .grid-stack-item-content {
                        z-index: 1 !important;
                        background: rgba(255, 255, 255, 0.7);
                        backdrop-filter: blur(20px);
                        border: 1px solid rgba(0, 0, 0, 0.05);
                        border-radius: 1.5rem; /* rounded-3xl */
                        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
                    }
                    /* Only show resize handles in edit mode (when not static) */
                    .grid-stack-static .ui-resizable-handle {
                        display: none !important;
                    }
                    .ui-resizable-handle {
                        z-index: 20 !important;
                        opacity: 0 !important;
                        background: var(--terracotta, #bc6c4b) !important;
                        border-radius: 50% !important;
                        width: 14px !important;
                        height: 14px !important;
                        right: 12px !important;
                        bottom: 12px !important;
                        transition: opacity 0.2s;
                    }
                    .grid-stack-item:hover .ui-resizable-handle {
                        opacity: ${isEditMode ? '0.8' : '0'} !important;
                    }
                `}
            </style>
            <div className={`grid-stack shadow-none ${!isEditMode ? 'grid-stack-static' : ''}`} ref={wrapperRef}>
                {widgets.map((widget) => (
                    <div
                        key={widget.id}
                        ref={el => { refs.current[widget.id] = el; }}
                        className="grid-stack-item rounded-3xl"
                        gs-id={widget.id}
                        gs-w={widget.dimensions?.w || 2}
                        gs-h={widget.dimensions?.h || 2}
                        gs-x={widget.x}
                        gs-y={widget.y}
                    >
                        <div className="grid-stack-item-content h-full w-full relative group">
                            <Widget
                                id={widget.id}
                                title={widget.title}
                                onDelete={() => handleDelete(widget.id)}
                                className={`h-full w-full pointer-events-auto ${isEditMode ? 'cursor-move' : ''}`}
                                isEditMode={isEditMode}
                            >
                                {widget.url ? (
                                    <iframe
                                        src={`http://localhost:8000${widget.url}`}
                                        className={`w-full h-full border-0 ${isEditMode ? 'pointer-events-none' : 'pointer-events-auto'}`}
                                        title={widget.title}
                                    />
                                ) : widget.code ? (
                                    <DynamicWidget code={widget.code} />
                                ) : (
                                    widget.content
                                )}
                            </Widget>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
