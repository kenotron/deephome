import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { AgentConsole } from './components/AgentConsole';
import { Grid } from './components/Grid';
import { Dock } from './components/Dock';
import { Header } from './components/Header';
import type { AgentMessage } from './types';
import { useRxData, Provider } from 'rxdb-hooks';

// App View Modes
type ViewMode = 'dashboard' | 'agent';

function App() {
  // Database Initialization
  const [db, setDb] = useState<any>(null);

  useEffect(() => {
    const setupDB = async () => {
      const _db = await import('./db').then(m => m.initDB());
      setDb(_db);
    };
    setupDB();
  }, []);

  if (!db) return <div className="flex items-center justify-center h-screen text-white/20">Loading Database...</div>;

  return (
    <Provider db={db}>
      <AppContent db={db} />
    </Provider>
  );
}

function AppContent({ db }: { db: any }) {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const [isEditMode, setIsEditMode] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [lastManifest, setLastManifest] = useState<any>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const { result: widgets, isFetching } = useRxData(
    'widgets',
    collection => collection.find().sort({ createdAt: 'desc' })
  );


  const handleSendMessage = async (prompt: string) => {
    console.log("Submitting prompt:", prompt);
    setIsGenerating(true);
    setIsComplete(false);
    setLastManifest(null);

    // Ensure session ID exists
    let sessionId = currentSessionId;
    if (!sessionId) {
      sessionId = Date.now().toString();
      setCurrentSessionId(sessionId);
    }

    // Create initial user message and placeholder assistant message
    const userMsg: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: prompt,
      timestamp: Date.now()
    };

    const assistantMsgId = (Date.now() + 1).toString();
    const assistantMsg: AgentMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      thoughts: [],
      toolCalls: [],
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);

    try {
      console.log("Connecting to Web Backend (FastAPI)...");
      const evtSource = new EventSource(`http://localhost:8000/agent/query?prompt=${encodeURIComponent(prompt)}&session_id=${sessionId}`);

      evtSource.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          const { type, payload } = parsed;

          setMessages(prev => {
            const index = prev.findIndex(m => m.id === assistantMsgId);
            if (index === -1) return prev;

            // Create a swallow copy of the message to update
            const activeMsg = { ...prev[index] };

            switch (type) {
              case 'log':
              case 'status':
                // Debug logs - ignore them (don't show as reasoning)
                console.log('[Agent Log]', payload);
                break;
              case 'reasoning':
                // Real reasoning/thinking content from the model
                activeMsg.thoughts = [...(activeMsg.thoughts || []), payload];
                break;
              case 'chunk':
              case 'response': // Keep 'response' for backward compatibility
                activeMsg.content = (activeMsg.content || '') + payload;
                break;
              case 'tool_call':
                const toolData = JSON.parse(payload);
                const newToolCall = {
                  id: Date.now().toString(),
                  name: toolData.name,
                  args: toolData.args,
                  status: 'running' as const
                };
                activeMsg.toolCalls = [...(activeMsg.toolCalls || []), newToolCall];
                break;
              case 'manifest':
                // Done
                setIsComplete(true);
                setIsGenerating(false);
                const manifest = JSON.parse(payload);
                setLastManifest(manifest);
                evtSource.close();
                break;
              case 'done':
                setIsGenerating(false);
                evtSource.close();
                break;
              case 'error':
                activeMsg.content = (activeMsg.content || '') + `\n\n[ERROR]: ${payload}`;
                setIsGenerating(false);
                evtSource.close();
                break;
            }

            // Return new array with updated message
            const newHistory = [...prev];
            newHistory[index] = activeMsg;
            return newHistory;
          });

        } catch (e) {
          console.error("Parse error", e);
        }
      };

      evtSource.onerror = (err) => {
        console.error("SSE Error:", err);
        setIsGenerating(false);
        evtSource.close();
      };

    } catch (e) {
      console.error("Agent failed:", e);
      setIsGenerating(false);
    }
  };

  const handleDockSubmit = (prompt: string) => {
    // Canvas chat = NEW widget session
    const newSessionId = Date.now().toString();
    setCurrentSessionId(newSessionId);
    console.log("Starting NEW widget session:", newSessionId);

    // Clear previous state for fresh start
    setMessages([]);
    setLastManifest(null);
    setIsComplete(false);

    // Update URL to widget creation
    navigate('/widget/new');

    setViewMode('agent');
    handleSendMessage(prompt);
  };

  const handleEditWidget = async (widgetId: string) => {
    // Find the widget
    const widgetDoc = widgets?.find((w: any) => w.id === widgetId);
    if (!widgetDoc) {
      console.warn("Widget not found for editing:", widgetId);
      return;
    }

    const widget = widgetDoc as any; // Cast to any to access schema properties safely

    // Restore the session ID - the backend SESSION_STORE will have the full conversation history
    const sessionId = widget.sessionId || Date.now().toString();
    setCurrentSessionId(sessionId);

    // Update URL to widget editing
    navigate(`/widget/${widgetId}`);

    // Switch to agent view
    setViewMode('agent');

    // Set up preview with existing widget
    // CRITICAL FIX: Destructure/copy properties to ensure we have a PLAIN object
    // RxDB returns Proxy objects that cannot be structured cloned or frozen easily by some state managers
    setLastManifest({
      id: widget.id,
      title: widget.title,
      code: widget.code,
      url: widget.url,
      dimensions: {
        w: widget.dimensions?.w || 2,
        h: widget.dimensions?.h || 2
      }
    });

    // Start with empty messages - the backend session has the real history
    // When the user sends a message, the agent will have full context from SESSION_STORE
    setMessages([]);

    // Fetch existing history
    try {
      const res = await fetch(`http://localhost:8000/agent/history/${sessionId}`);
      if (res.ok) {
        const history = await res.json();
        // Transform history if needed to match AgentMessage
        const formattedHistory = history.map((msg: any, i: number) => ({
          id: `hist-${i}`,
          role: msg.role,
          content: msg.content,
          toolCalls: msg.tool_calls ? msg.tool_calls.map((tc: any) => ({
            id: tc.payload ? JSON.parse(tc.payload).id : 'unknown',
            name: tc.payload ? JSON.parse(tc.payload).name : 'unknown',
            args: tc.payload ? JSON.parse(tc.payload).args : {},
            status: 'completed',
            result: 'Executed'
          })) : [],
          timestamp: Date.now() // Timestamps might not be in the store yet
        }));
        setMessages(formattedHistory);
      }
    } catch (e) {
      console.error("Failed to fetch history:", e);
    }

    setIsComplete(true); // Mark as complete since we have a widget to show
    setIsGenerating(false);
  };

  const handleConfirmWidget = async () => {
    if (lastManifest && db) {
      console.log("Confirming widget deployment:", lastManifest.id);
      try {
        // Check if widget already exists (editing case)
        const existingWidget = await db.widgets.findOne(lastManifest.id).exec();

        if (existingWidget) {
          // Update existing widget
          await existingWidget.patch({
            title: lastManifest.title || existingWidget.title,
            code: lastManifest.code || existingWidget.code,
            url: lastManifest.url || existingWidget.url,
            dimensions: lastManifest.dimensions || existingWidget.dimensions,
            sessionId: currentSessionId || existingWidget.sessionId,
            projectPath: (lastManifest as any).projectPath || existingWidget.projectPath
          });
          console.log("Widget updated successfully");
        } else {
          // Insert new widget
          await db.widgets.insert({
            id: lastManifest.id || `gen-${Date.now()}`,
            title: lastManifest.title || "Generated Widget",
            code: lastManifest.code,
            url: lastManifest.url,
            dimensions: {
              w: lastManifest.dimensions?.w || 2,
              h: lastManifest.dimensions?.h || 2
            },
            x: 0,
            y: 0,
            sessionId: currentSessionId || null,
            projectPath: (lastManifest as any).projectPath || null,
            createdAt: Date.now()
          });
          console.log("Widget inserted successfully");
        }

        // Reset state and switch mode
        setLastManifest(null);
        setIsComplete(false);
        navigate('/');
        setViewMode('dashboard');
      } catch (e) {
        console.error("Failed to save widget:", e);
        alert("Error: Failed to save widget. Check console.");
      }
    } else {
      console.warn("handleConfirmWidget called without manifest or db", { lastManifest, db: !!db });
    }
  };

  return (
    <main className="h-screen w-full overflow-hidden relative">

      {/* Dashboard View */}
      {viewMode === 'dashboard' && (
        <>
          {/* Grid Container */}
          <div className="absolute inset-0 z-0 overflow-y-auto p-4">
            {isFetching ? (
              <div className="flex h-full items-center justify-center opacity-20">
                <div className="animate-spin h-8 w-8 border-4 border-[var(--warm-charcoal)] border-t-transparent rounded-full"></div>
              </div>
            ) : (
              <Grid
                widgets={widgets}
                isEditMode={isEditMode}
                onEditWidget={handleEditWidget}
              />
            )}
          </div>

          {/* HUD Layer - Explicit high z-index container */}
          <div className="absolute inset-0 z-50 pointer-events-none">
            <Header isEditMode={isEditMode} onToggleEditMode={() => setIsEditMode(!isEditMode)} />
            <Dock onSubmit={handleDockSubmit} />
          </div>
        </>
      )}

      {/* Agent/Chat View */}
      {viewMode === 'agent' && (
        <div className="absolute inset-0 z-10 animate-in fade-in slide-in-from-bottom-10 duration-300">
          <ErrorBoundary
            label="Agent Interface Error"
            wrapperClassName="h-full w-full bg-[#fefae0] flex items-center justify-center"
            fallback={
              <div className="h-full w-full bg-[#fefae0] flex flex-col items-center justify-center text-[var(--warm-charcoal)]">
                <div className="p-8 bg-white/50 backdrop-blur-sm rounded-2xl border border-black/5 flex flex-col items-center">
                  <AlertTriangle className="w-12 h-12 text-[var(--terracotta)] mb-4" />
                  <h2 className="text-xl font-bold mb-2">Agent Interface Crashed</h2>
                  <p className="text-sm opacity-60 mb-6 text-center max-w-sm">
                    Something went wrong while rendering the chat interface.
                    This might be due to a malformed message or component error.
                  </p>
                  <button
                    onClick={() => window.location.reload()}
                    className="bg-[var(--warm-charcoal)] text-[#fefae0] px-6 py-2 rounded-full text-sm font-medium hover:opacity-90 transition-opacity"
                  >
                    Reload Application
                  </button>
                </div>
              </div>
            }
          >
            <AgentConsole
              isGenerating={isGenerating}
              isComplete={isComplete}
              messages={messages}
              onSendMessage={handleSendMessage}
              onConfirm={handleConfirmWidget}
              previewUrl={lastManifest?.url}
              previewCode={lastManifest?.code}
              isEditingExisting={lastManifest && widgets?.some((w: any) => w.id === lastManifest.id)}
              onClose={() => {
                navigate('/');
                setViewMode('dashboard');
              }}
              dimensions={lastManifest?.dimensions}
            />
          </ErrorBoundary>
        </div>
      )}

    </main>
  );
}

export default App;
