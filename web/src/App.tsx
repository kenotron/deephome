import { useState, useEffect } from 'react';
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
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const [isEditMode, setIsEditMode] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [lastManifest, setLastManifest] = useState<any>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const { result: widgets } = useRxData(
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
                activeMsg.thoughts = [...(activeMsg.thoughts || []), payload];
                break;
              case 'response':
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
    setViewMode('agent');
    handleSendMessage(prompt);
  };

  const handleConfirmWidget = async () => {
    if (lastManifest && db) {
      console.log("Confirming widget deployment:", lastManifest.id);
      try {
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
          createdAt: Date.now()
        });
        console.log("Widget inserted successfully");
        // Reset state and switch mode
        setLastManifest(null);
        setIsComplete(false);
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
          <div className="absolute inset-0 z-0 overflow-y-auto">
            <Grid widgets={widgets || []} isEditMode={isEditMode} />
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
          <AgentConsole
            isGenerating={isGenerating}
            isComplete={isComplete}
            messages={messages}
            onSendMessage={handleSendMessage}
            onConfirm={handleConfirmWidget}
            // Passing code as previewUrl prop temporarily or we need to update AgentConsole to accept code
            // Updating AgentConsole next.
            previewUrl={lastManifest?.url}
            previewCode={lastManifest?.code}
            onClose={() => setViewMode('dashboard')}
          />
        </div>
      )}

    </main>
  );
}

export default App;
