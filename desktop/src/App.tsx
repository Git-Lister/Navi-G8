// desktop/src/App.tsx

import React, { useState, useEffect, useRef } from 'react';
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import GraphView from './components/GraphView';
import './App.css';

// ─── Components ──────────────────────────────────────────────────────

const FieldState: React.FC<{ state: any }> = ({ state }) => (
  <div className="field-state">
    <h3>🧭 Field State</h3>
    <div>Coherence: {state.coherence?.toFixed(2) || '—'}</div>
    <div>Trajectories: {state.trajectories || 0}</div>
    <div>Flags: {state.flags || 0}</div>
    <div>Streams: {state.streams || 0}</div>
  </div>
);

const Terminal: React.FC<{
  onSend: (msg: string) => void;
  messages: { role: string; content: string }[];
}> = ({ onSend, messages }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="terminal">
      <div className="terminal-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`terminal-msg ${msg.role}`}>
            {msg.role === 'user' ? '> ' : '💡 '}
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="terminal-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && input.trim()) {
              onSend(input);
              setInput('');
            }
          }}
          placeholder="Type your perturbation..."
          className="terminal-input"
        />
        <button onClick={() => { onSend(input); setInput(''); }} className="terminal-send">
          Send
        </button>
      </div>
    </div>
  );
};

// ─── Main App ────────────────────────────────────────────────────────

function App() {
  const [fieldState, setFieldState] = useState<Record<string, any>>({});
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [isReady, setIsReady] = useState(false);
  const backendStarted = useRef(false);

  // ─── Fetch graph data from backend ────────────────────────────────
  const fetchGraphData = async () => {
    try {
      const response = await invoke('get_state');
      console.log('📊 Graph data fetched:', response);
      // Parse the response if needed
    } catch (err) {
      console.error('❌ Failed to fetch graph data:', err);
    }
  };

  useEffect(() => {
    const init = async () => {
      if (backendStarted.current) return;
      backendStarted.current = true;

      try {
        await invoke('start_backend');
        setIsReady(true);
        console.log('✅ Backend started successfully');

        // ─── Fetch initial graph data ──────────────────────────────
        await fetchGraphData();
      } catch (err) {
        console.error('❌ Failed to start backend:', err);
        setIsReady(false);
      }
    };
    init();

    // ─── Listen for backend events ──────────────────────────────────
    const unlisten = listen('field_event', (event) => {
      try {
        const data = JSON.parse(event.payload as string);
        console.log('📨 Field event:', data);

        if (data.type === 'state') {
          setFieldState(data);
          // If the state includes nodes and edges, update them
          if (data.nodes && data.edges) {
            setNodes(data.nodes);
            setEdges(data.edges);
          }
        } else if (data.type === 'response') {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: data.insight },
            ...(data.action ? [{ role: 'assistant', content: `⚡ ${data.action}` }] : []),
          ]);
        } else if (data.type === 'error') {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: `⚠️ ${data.message}` },
          ]);
        }
      } catch (err) {
        console.error('Failed to parse event:', err);
      }
    });

    return () => { unlisten.then(fn => fn()); };
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    setMessages((prev) => [...prev, { role: 'user', content: text.trim() }]);
    try {
      await invoke('send_query', { query: text.trim() });
      // After sending a query, refresh graph data
      await fetchGraphData();
    } catch (err) {
      console.error('Failed to send query:', err);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `⚠️ Error: ${err}` },
      ]);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Navi-G8</h1>
        <span className="coherence">
          Coherence: {fieldState.coherence?.toFixed(2) || '—'}
          {!isReady && ' ⏳'}
        </span>
      </header>
      <div className="main">
        <aside className="sidebar">
          <FieldState state={fieldState} />
        </aside>
        <main className="content">
          <div className="graph-container">
            <GraphView
              nodes={nodes}
              edges={edges}
              onNodeClick={(nodeId) => {
                console.log('Node clicked:', nodeId);
                // TODO: Show node details in inspector
              }}
            />
          </div>
          <Terminal messages={messages} onSend={sendMessage} />
        </main>
      </div>
    </div>
  );
}

export default App;