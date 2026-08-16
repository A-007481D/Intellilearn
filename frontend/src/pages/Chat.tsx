import React, { useState, useEffect, useRef } from 'react';
import { apiGet, apiPost, apiDelete } from '../lib/api';
import { Send, MessageSquare, Trash2, Loader2, Bot, User, BookOpen } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

interface Message {
  id: string;
  role: 'USER' | 'ASSISTANT';
  content: string;
  citations?: { id: string; content: string }[];
}

export default function Chat() {
  const [searchParams] = useSearchParams();
  const initialDoc = searchParams.get('doc');
  
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConv, setActiveConv] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [docs, setDocs] = useState<{id: string, title: string}[]>([]);
  const [selectedDoc, setSelectedDoc] = useState(initialDoc || '');
  const [level, setLevel] = useState('Standard');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiGet<Conversation[]>('/knowledge/conversations/').then(setConversations).catch(console.error);
    apiGet<any[]>('/knowledge/documents/').then(res => setDocs(res.filter(d => d.status === 'READY'))).catch(console.error);
  }, []);

  useEffect(() => {
    if (activeConv) {
      apiGet<{messages: Message[]}>(`/knowledge/conversations/${activeConv}/`)
        .then(res => setMessages(res.messages))
        .catch(console.error);
    } else {
      setMessages([]);
    }
  }, [activeConv]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { id: 'temp', role: 'USER', content: userMsg }]);
    setLoading(true);

    try {
      const res = await apiPost<any>('/knowledge/chat/', {
        question: userMsg,
        document_id: selectedDoc || undefined,
        conversation_id: activeConv || undefined,
        level: level.toLowerCase()
      });
      
      if (!activeConv) {
        setActiveConv(res.conversation_id);
        apiGet<Conversation[]>('/knowledge/conversations/').then(setConversations);
      }
      
      setMessages(prev => [...prev.filter(m => m.id !== 'temp'), {
        id: res.id || Date.now().toString(),
        role: 'USER',
        content: userMsg
      }, {
        id: (Date.now() + 1).toString(),
        role: 'ASSISTANT',
        content: res.answer,
        citations: res.citations
      }]);
    } catch (e) {
      console.error(e);
      setMessages(prev => prev.filter(m => m.id !== 'temp'));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConv = async (id: string) => {
    try {
      await apiDelete(`/knowledge/conversations/${id}/`);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeConv === id) setActiveConv(null);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 bg-white/5 border border-white/10 rounded-2xl flex flex-col overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <button
            onClick={() => setActiveConv(null)}
            className="w-full py-2 bg-indigo-500/20 text-indigo-300 rounded-lg text-sm font-medium hover:bg-indigo-500/30 transition-colors"
          >
            + New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {conversations.map(c => (
            <div
              key={c.id}
              onClick={() => setActiveConv(c.id)}
              className={`flex items-center justify-between p-3 rounded-xl cursor-pointer group transition-all ${
                activeConv === c.id ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <MessageSquare size={16} className="flex-shrink-0" />
                <span className="text-sm truncate">{c.title}</span>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); handleDeleteConv(c.id); }}
                className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 transition-opacity"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat */}
      <div className="flex-1 bg-white/5 border border-white/10 rounded-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
          <div className="flex items-center gap-4">
            <select
              value={selectedDoc}
              onChange={e => setSelectedDoc(e.target.value)}
              className="bg-[#111113] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Documents</option>
              {docs.map(d => <option key={d.id} value={d.id}>{d.title}</option>)}
            </select>
            <select
              value={level}
              onChange={e => setLevel(e.target.value)}
              className="bg-[#111113] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              <option>Simple</option>
              <option>Standard</option>
              <option>Expert</option>
            </select>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
              <Bot size={48} className="mb-4 text-indigo-400" />
              <h2 className="text-xl font-semibold text-white mb-2">How can I help you learn?</h2>
              <p className="text-slate-400 max-w-sm">Ask a question about your documents, and I'll find the answer with citations.</p>
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`flex gap-4 ${m.role === 'USER' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  m.role === 'USER' ? 'bg-indigo-600' : 'bg-slate-700'
                }`}>
                  {m.role === 'USER' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
                </div>
                <div className={`max-w-[75%] rounded-2xl p-4 ${
                  m.role === 'USER' 
                    ? 'bg-indigo-600/20 text-indigo-100 border border-indigo-500/30 rounded-tr-sm' 
                    : 'bg-white/10 text-slate-200 border border-white/5 rounded-tl-sm'
                }`}>
                  <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                  
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/10 space-y-2">
                      <p className="text-xs font-medium text-slate-400 flex items-center gap-1">
                        <BookOpen size={12} /> Sources
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {m.citations.map((cit, idx) => (
                          <div key={idx} className="bg-black/20 rounded px-2 py-1 text-xs text-slate-300 border border-white/5" title={cit.content}>
                            [{idx + 1}]
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
              <div className="bg-white/10 border border-white/5 rounded-2xl rounded-tl-sm p-4 flex items-center gap-2 text-slate-400">
                <Loader2 size={16} className="animate-spin" /> Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/10 bg-white/[0.02]">
          <div className="relative">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask anything..."
              className="w-full bg-[#111113] border border-white/10 rounded-xl pl-4 pr-12 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 resize-none"
              rows={1}
              style={{ minHeight: '50px', maxHeight: '150px' }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
