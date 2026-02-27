import React, { useState, useRef, useEffect } from 'react';
import { sendMessage, ChatMessage } from '../services/chat';
import './Console.css'; // we'll create basic styles

interface ConsoleProps {
  onLogout: () => void;
}

export const Console: React.FC<ConsoleProps> = ({ onLogout }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'Navi-G8 ready. How can I help?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    // Add a placeholder assistant message that will be updated
    const assistantMessageId = Date.now().toString();
    setMessages(prev => [
      ...prev,
      { role: 'assistant', content: '', id: assistantMessageId }
    ]);

    abortControllerRef.current = new AbortController();

    await sendMessage(
      input,
      {
        onChunk: (chunk) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + chunk }
                : msg
            )
          );
        },
        onComplete: () => {
          setIsLoading(false);
          abortControllerRef.current = null;
        },
        onError: (err) => {
          setError(err.message);
          // Remove the placeholder or mark as error
          setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
          setIsLoading(false);
          abortControllerRef.current = null;
        },
      },
      undefined, // use default model
      abortControllerRef.current.signal
    );
  };

  const handleStop = () => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="console">
      <div className="console-header">
        <span className="title">Navi-G8</span>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </div>

      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <span className="role">{msg.role === 'user' ? '>' : 'Nav'}</span>
            <span className="content">{msg.content || (isLoading && msg.role === 'assistant' ? '▊' : '')}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {error && <div className="error">{error}</div>}

      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={isLoading}
          rows={2}
        />
        {isLoading ? (
          <button onClick={handleStop} className="stop-btn">Stop</button>
        ) : (
          <button onClick={handleSend} disabled={!input.trim()}>Send</button>
        )}
      </div>
    </div>
  );
};