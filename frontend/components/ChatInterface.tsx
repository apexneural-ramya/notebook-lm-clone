'use client';

import { useState, useRef, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { chatAPI } from '@/lib/api-client';
import { Send, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Citation from './Citation';

export default function ChatInterface() {
  const { sources, messages, setMessages, addMessage, isLoading, setLoading, currentSessionId, setSessionId } = useStore();
  const [query, setQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!query.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: query,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setQuery('');
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(query, currentSessionId || undefined);
      
      if (response.status && response.data) {
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content: response.data.response,
          sources: response.data.sources,
          timestamp: new Date(),
        };
        addMessage(assistantMessage);
      }
    } catch (error: any) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: `Error: ${error.response?.data?.detail || 'Failed to generate response'}`,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setSessionId(null);
  };

  if (sources.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-400">
          <p className="text-lg mb-2">Add a source in the "Add Sources" tab to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="font-semibold">Chat</h2>
        {messages.length > 0 && (
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-3 py-1 text-sm text-gray-400 hover:text-foreground transition-colors"
          >
            <Trash2 size={16} />
            Reset
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <p>Ask a question about your sources</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`p-4 rounded-lg ${
                message.role === 'user'
                  ? 'bg-primary/20 ml-auto max-w-[80%]'
                  : 'bg-secondary-light max-w-[80%]'
              }`}
            >
              <div className="font-semibold mb-2 text-sm">
                {message.role === 'user' ? 'You' : 'Assistant'}
              </div>
              <div className="prose prose-invert max-w-none">
                <ReactMarkdown
                  components={{
                    // Custom renderer for citations [1], [2], etc.
                    text: ({ node, ...props }: any) => {
                      const text = String(props.children);
                      // Check if text contains citations
                      if (text.match(/\[\d+\]/) && message.sources) {
                        const parts = text.split(/(\[\d+\])/g);
                        return (
                          <>
                            {parts.map((part, idx) => {
                              const citationMatch = part.match(/\[(\d+)\]/);
                              if (citationMatch) {
                                const citationNum = parseInt(citationMatch[1]);
                                const source = message.sources?.[citationNum - 1];
                                if (source) {
                                  return <Citation key={idx} source={source} number={citationNum} />;
                                }
                              }
                              return <span key={idx}>{part}</span>;
                            })}
                          </>
                        );
                      }
                      // Extract only HTML-compatible props
                      const { ref, ...spanProps } = props;
                      return <span {...spanProps}>{props.children}</span>;
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <div className="text-xs text-gray-400 mb-2">Sources:</div>
                  <div className="flex flex-wrap gap-2">
                    {message.sources.map((source: any, idx: number) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-accent-dark rounded text-xs"
                      >
                        {source.source_file}
                        {source.page_number && ` (Page ${source.page_number})`}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div className="p-4 bg-secondary-light rounded-lg max-w-[80%]">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <span className="text-gray-400">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me anything about your sources..."
            className="flex-1 px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!query.trim() || isLoading}
            className="px-6 py-2 bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

