import { useEffect, useRef } from 'react';
import { Widget } from './Widget';
import { DynamicWidget } from '../../preview';
import 'gridstack/dist/gridstack.min.css';
import { GridStack } from 'gridstack';
import { useRxCollection } from 'rxdb-hooks';

interface GridProps {
    widgets: any[];
    isEditMode: boolean;
    onEditWidget?: (widgetId: string) => void;
}

export function Grid({ widgets, isEditMode, onEditWidget }: GridProps) {
    const gridRef = useRef<GridStack | null>(null);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const refs = useRef<{ [key: string]: HTMLDivElement | null }>({});
    const collection = useRxCollection('widgets');

    const isInteracting = useRef(false);

    // Handle Edit Mode Toggle
    useEffect(() => {
        if (gridRef.current) {
            gridRef.current.setStatic(!isEditMode);
        }
    }, [isEditMode]);

    // Initialize GridStack
    useEffect(() => {
        if (!wrapperRef.current) return;

        // Initialize GridStack
        // We use a clean initialization pattern to avoid duplicates in strict mode
        if (!gridRef.current) {
            const grid = GridStack.init({
                margin: 10,
                cellHeight: 180,
                float: true,
                column: 6,
                columnOpts: { breakpoints: [{ w: 768, c: 1 }] },
                animate: true,
                resizable: { handles: 'se' },
                staticGrid: !isEditMode,
            }, wrapperRef.current);

            gridRef.current = grid;

            // Interaction Guards
            grid.on('dragstart resizestart', () => {
                isInteracting.current = true;
            });
            grid.on('dragstop resizestop', () => {
                // Small delay to let the final change event fire/process before we resume syncing
                setTimeout(() => {
                    isInteracting.current = false;
                }, 500);
            });

            // --- Persistence Listener ---
            grid.on('change', (_event: Event, items: any[]) => {
                if (!collection) return;

                items.forEach(async (item) => {
                    const widgetId = item.id;
                    if (!widgetId) return;

                    // GridStack sometimes returns undefined or null for coordinates if they are 0?
                    // Ensure we have valid numbers
                    const updates = {
                        dimensions: {
                            w: item.w ?? 2,
                            h: item.h ?? 2
                        },
                        x: item.x ?? 0,
                        y: item.y ?? 0
                    };

                    try {
                        const doc = await collection.findOne(widgetId).exec();
                        if (doc) {
                            // Only patch if actually changed to reduce DB noise
                            const currentDoc = doc as any;
                            if (currentDoc.x !== updates.x || currentDoc.y !== updates.y ||
                                currentDoc.dimensions?.w !== updates.dimensions.w ||
                                currentDoc.dimensions?.h !== updates.dimensions.h) {

                                await doc.patch(updates);
                            }
                        }
                    } catch (err) {
                        console.error("Failed to save layout:", err);
                    }
                });
            });
        }

        // Cleanup function
        return () => {
            if (gridRef.current) {
                gridRef.current.destroy(false); // false = don't remove DOM elements
                gridRef.current = null;
            }
        };
    }, [collection]); // Re-init if collection changes (rare) or mount/unmount


    // Sync Widgets with GridStack
    useEffect(() => {
        const grid = gridRef.current;
        if (!grid) return;

        // 1. Remove orphaned widgets
        grid.engine.nodes.forEach(node => {
            if (!widgets.find(w => w.id === node.id)) {
                if (node.el) grid.removeWidget(node.el);
            }
        });

        // Skip updates if user is interacting to avoid fighting
        if (isInteracting.current) return;

        // 2. Add or Update widgets
        // Defer slightly to ensure React has committed the DOM elements
        requestAnimationFrame(() => {
            widgets.forEach(widget => {
                const el = refs.current[widget.id];
                if (el) {
                    // Check if already in grid
                    const existingItem = grid.getGridItems().find(item => item === el);

                    if (!existingItem) {
                        // Add new widget
                        // Vital: Pass options explicitly to makeWidget
                        const options = {
                            id: widget.id,
                            w: widget.dimensions?.w || 2,
                            h: widget.dimensions?.h || 2,
                            x: widget.x ?? 0, // Ensure 0 is passed not undefined
                            y: widget.y ?? 0,
                            autoPosition: (widget.x === undefined || widget.y === undefined) // Only auto if really missing
                        };
                        grid.makeWidget(el, options);
                    } else {
                        // Widget exists - Update state to match DB
                        // Since we guard against isInteracting, we can safely enforce DB state here
                        // This fixes the "Refresh" bug where GridStack initializes with defaults
                        const node = grid.engine.nodes.find(n => n.id === widget.id);
                        if (node) {
                            if (node.x !== widget.x || node.y !== widget.y ||
                                node.w !== (widget.dimensions?.w || 2) ||
                                node.h !== (widget.dimensions?.h || 2)) {

                                // Special check for the "Default Reset" bug
                                // If Grid thinks it is 0,0 but DB has real coords, we MUST force it
                                const isResetBug = (node.x === 0 && node.y === 0) && (widget.x !== 0 || widget.y !== 0);
                                if (isResetBug) {
                                    // console.warn(`[Grid] Detected 0,0 reset bug for ${widget.id}. Forcing update to ${widget.x},${widget.y}`);
                                }

                                grid.update(el, {
                                    x: widget.x,
                                    y: widget.y,
                                    w: widget.dimensions?.w,
                                    h: widget.dimensions?.h
                                });
                            }
                        }
                    }
                }
            });
        });

    }, [widgets]);

    const handleDelete = async (id: string) => {
        if (!collection) return;
        try {
            const doc = await collection.findOne(id).exec();
            if (doc) {
                await doc.remove();
            }
        } catch (err) {
            console.error("Failed to delete widget:", err);
        }
    };

    return (
        <div className="w-full min-h-screen pt-24 pb-32">
            <style>
                {`
                    .grid-stack-item-content {
                        z-index: 1 !important;
                    }
                    /* Only show resize handles in edit mode (when not static) */
                    .grid-stack-static .ui-resizable-handle {
                        display: none !important;
                    }
                    /* Modern resize handle - visible corner grip */
                    .ui-resizable-handle {
                        z-index: 20 !important;
                        width: 24px !important;
                        height: 24px !important;
                        right: 0px !important;
                        bottom: 0px !important;
                        background: none !important;
                        border: none !important;
                        cursor: nwse-resize !important;
                        pointer-events: auto !important;
                    }
                    /* Six-dot grip pattern */
                    .ui-resizable-handle::before {
                        content: '';
                        position: absolute;
                        right: 4px;
                        bottom: 4px;
                        width: 16px;
                        height: 16px;
                        background-image:
                            radial-gradient(circle, rgba(0, 0, 0, 0.3) 1.5px, transparent 1.5px),
                            radial-gradient(circle, rgba(0, 0, 0, 0.3) 1.5px, transparent 1.5px),
                            radial-gradient(circle, rgba(0, 0, 0, 0.3) 1.5px, transparent 1.5px),
                            radial-gradient(circle, rgba(0, 0, 0, 0.3) 1.5px, transparent 1.5px),
                            radial-gradient(circle, rgba(0, 0, 0, 0.3) 1.5px, transparent 1.5px),
                            radial-gradient(circle, rgba(0, 0, 0, 0.3) 1.5px, transparent 1.5px);
                        background-size: 6px 6px;
                        background-position: 0px 0px, 6px 0px, 0px 6px, 6px 6px, 0px 12px, 6px 12px;
                        background-repeat: no-repeat;
                        opacity: 0;
                        transition: all 0.2s ease;
                    }
                    .grid-stack-static .ui-resizable-handle::before {
                        display: none;
                    }
                    /* Show on hover in edit mode AND when strictly resizing */
                    .grid-stack:not(.grid-stack-static) .grid-stack-item:hover .ui-resizable-handle::before,
                    .grid-stack:not(.grid-stack-static) .grid-stack-item.ui-resizable-resizing .ui-resizable-handle::before {
                        opacity: 0.6;
                    }
                     .grid-stack:not(.grid-stack-static) .grid-stack-item.ui-resizable-resizing .ui-resizable-handle::before {
                        opacity: 1 !important;
                     }
                `}
            </style>
            <div className={`grid-stack shadow-none ${!isEditMode ? 'grid-stack-static' : ''}`} ref={wrapperRef}>
                {widgets.map((widget) => (
                    <div
                        key={widget.id}
                        ref={el => { refs.current[widget.id] = el; }}
                        className="grid-stack-item rounded-2xl"
                        data-gs-id={widget.id}
                        data-gs-w={widget.dimensions?.w || 2}
                        data-gs-h={widget.dimensions?.h || 2}
                        data-gs-x={widget.x ?? 0}
                        data-gs-y={widget.y ?? 0}
                    >
                        <div className="grid-stack-item-content h-full w-full relative group">
                            <Widget
                                id={widget.id}
                                title={widget.title}
                                onDelete={() => handleDelete(widget.id)}
                                onEdit={() => onEditWidget?.(widget.id)}
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
