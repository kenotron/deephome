import { useEffect, useRef, useState } from 'react';

type EventHandler = (event: any) => void;

interface UseEventStreamOptions {
    url: string;
    onMessage: EventHandler;
    onOpen?: () => void;
    onError?: (error: Event) => void;
    enabled?: boolean;
}

export function useSSE({ url, onMessage, onOpen, onError, enabled = true }: UseEventStreamOptions) {
    const eventSourceRef = useRef<EventSource | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        if (!enabled) {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
                setIsConnected(false);
            }
            return;
        }

        // Avoid duplicate connection if URL hasn't changed
        if (eventSourceRef.current?.url === url && eventSourceRef.current.readyState !== EventSource.CLOSED) {
            return;
        }

        const connect = () => {
            console.log(`[EventStream] Connecting to ${url}...`);
            const es = new EventSource(url);
            eventSourceRef.current = es;

            es.onopen = () => {
                console.log(`[EventStream] Connected to ${url}`);
                setIsConnected(true);
                onOpen?.();
            };

            es.onmessage = (event) => {
                try {
                    const parsed = JSON.parse(event.data);
                    onMessage(parsed);
                } catch (e) {
                    console.error('[EventStream] Parse error:', e);
                }
            };

            es.onerror = (e) => {
                console.error('[EventStream] Error:', e);
                setIsConnected(false);
                onError?.(e);

                // Native EventSource sometimes auto-reconnects, but if it closes:
                if (es.readyState === EventSource.CLOSED) {
                    // Retry logic could go here, or let browser handle native reconnection if it wasn't fatal
                    // For now we rely on browser.
                }
            };
        };

        connect();

        return () => {
            if (eventSourceRef.current) {
                console.log('[EventStream] Closing connection');
                eventSourceRef.current.close();
                eventSourceRef.current = null;
                setIsConnected(false);
            }
        };
    }, [url, enabled]);

    return { isConnected };
}
