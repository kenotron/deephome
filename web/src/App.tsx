import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { ErrorBoundary } from './core/ui/ErrorBoundary';
import { AgentConsole } from './modules/agent';
import { Grid, Dock, Header } from './modules/dashboard';
import { TestAgentPage } from './pages/TestAgentPage';
import { useRxData, Provider } from 'rxdb-hooks';
import { useAgentSession } from './modules/agent/hooks/useAgentSession';

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

  // Hook-based Agent State
  const {
    currentSessionId,
    messages,
    isGenerating,
    isComplete,
    setIsComplete,
    lastPreview,
    setLastPreview,
    actions: { sendMessage, startSession, loadHistory, setMessages }
  } = useAgentSession();

  const { result: widgets, isFetching } = useRxData(
    'widgets',
    collection => collection.find().sort({ createdAt: 'desc' })
  );

  const handleDockSubmit = (prompt: string) => {
    // Canvas chat = NEW widget session
    const newSessionId = Date.now().toString();
    startSession(newSessionId);
    console.log("Starting NEW widget session:", newSessionId);

    // Update URL to widget creation
    navigate('/widget/new');

    setViewMode('agent');
    sendMessage(prompt);
  };

  const handleEditWidget = async (widgetId: string) => {
    // Find the widget
    const widgetDoc = widgets?.find((w: any) => w.id === widgetId);
    if (!widgetDoc) {
      console.warn("Widget not found for editing:", widgetId);
      return;
    }

    const widget = widgetDoc as any; // Cast to any to access schema properties safely

    // Restore the session ID
    const sessionId = widget.sessionId || Date.now().toString();
    startSession(sessionId);

    // Update URL to widget editing
    navigate(`/widget/${widgetId}`);

    // Switch to agent view
    setViewMode('agent');

    // Set up preview with existing widget
    setLastPreview({
      id: widget.id,
      title: widget.title,
      code: widget.code,
      url: widget.url,
      dimensions: {
        w: widget.dimensions?.w || 2,
        h: widget.dimensions?.h || 2
      }
    });

    // Load history
    loadHistory(sessionId);

    setIsComplete(true); // Mark as complete since we have a widget to show
  };

  const handleConfirmWidget = async () => {
    if (lastPreview && db) {
      console.log("Confirming widget deployment:", lastPreview.id);
      try {
        // Check if widget already exists (editing case)
        const existingWidget = await db.widgets.findOne(lastPreview.id).exec();

        if (existingWidget) {
          // Update existing widget
          await existingWidget.patch({
            title: lastPreview.title || existingWidget.title,
            code: lastPreview.code || existingWidget.code,
            url: lastPreview.url || existingWidget.url,
            dimensions: lastPreview.dimensions || existingWidget.dimensions,
            sessionId: currentSessionId || existingWidget.sessionId,
            projectPath: (lastPreview as any).projectPath || existingWidget.projectPath
          });
          console.log("Widget updated successfully");
        } else {
          // Insert new widget
          await db.widgets.insert({
            id: lastPreview.id || `gen-${Date.now()}`,
            title: lastPreview.title || "Generated Widget",
            code: lastPreview.code,
            url: lastPreview.url,
            dimensions: {
              w: lastPreview.dimensions?.w || 2,
              h: lastPreview.dimensions?.h || 2
            },
            x: 0,
            y: 0,
            sessionId: currentSessionId || null,
            projectPath: (lastPreview as any).projectPath || null,
            createdAt: Date.now()
          });
          console.log("Widget inserted successfully");
        }

        // Reset state and switch mode
        setLastPreview(null);
        setIsComplete(false);
        navigate('/');
        setViewMode('dashboard');
      } catch (e) {
        console.error("Failed to save widget:", e);
        alert("Error: Failed to save widget. Check console.");
      }
    } else {
      console.warn("handleConfirmWidget called without manifest or db", { lastPreview, db: !!db });
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

      {/* Test Route - Hacky manual routing for now or we could use React Router properly in future */}
      {window.location.pathname === '/test/agent' && (
        <TestAgentPage />
      )}

      {/* Agent/Chat View */}
      {viewMode === 'agent' && window.location.pathname !== '/test/agent' && (
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
              onSendMessage={sendMessage}
              onConfirm={handleConfirmWidget}
              previewUrl={lastPreview?.url}
              previewCode={lastPreview?.code}
              isEditingExisting={lastPreview && widgets?.some((w: any) => w.id === lastPreview.id)}
              onClose={() => {
                navigate('/');
                setViewMode('dashboard');
              }}
              dimensions={lastPreview?.dimensions}
            />
          </ErrorBoundary>
        </div>
      )}

    </main>
  );
}

export default App;
