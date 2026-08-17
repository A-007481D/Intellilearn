import React, { useEffect, useState, useRef } from 'react';
import { apiGet, apiUpload, apiDelete, apiPatch } from '../lib/api';
import { getUser } from '../lib/auth';
import { Upload, FileText, Trash2, Edit2, Loader2, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Document {
  id: string;
  title: string;
  status: 'UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED';
  file_size_bytes: number;
  created_at: string;
}

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const user = getUser();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const fetchDocs = async () => {
    try {
      const data = await apiGet<Document[]>('/knowledge/documents/');
      setDocuments(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
    const interval = setInterval(() => {
      setDocuments(docs => {
        if (docs.some(d => d.status === 'PROCESSING')) {
          fetchDocs();
        }
        return docs;
      });
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', e.target.files[0]);
      await apiUpload('/knowledge/documents/', formData);
      await fetchDocs();
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await apiDelete(`/knowledge/documents/${id}/`);
      setDocuments(docs => docs.filter(d => d.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleRename = async (id: string) => {
    if (!editTitle) return;
    try {
      await apiPatch(`/knowledge/documents/${id}/`, { title: editTitle });
      setDocuments(docs => docs.map(d => d.id === id ? { ...d, title: editTitle } : d));
      setEditingId(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReprocess = async (id: string) => {
    try {
      await apiPatch(`/knowledge/documents/${id}/`, { status: 'UPLOADED' });
      fetchDocs();
    } catch (e) {
      console.error(e);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'READY': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'PROCESSING': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'FAILED': return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      default: return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  const totalSize = documents.reduce((acc, d) => acc + d.file_size_bytes, 0);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Documents</h1>
          <p className="text-slate-400 text-sm mt-1">Manage your knowledge base files</p>
        </div>
        <div className="flex items-center gap-4 bg-white/5 border border-white/10 rounded-xl px-4 py-2">
          <div className="text-sm">
            <span className="text-slate-400">Docs: </span>
            <span className="text-white font-medium">{documents.length} / {user?.max_documents}</span>
          </div>
          <div className="w-px h-4 bg-white/20"></div>
          <div className="text-sm">
            <span className="text-slate-400">Storage: </span>
            <span className="text-white font-medium">
              {(totalSize / (1024 * 1024)).toFixed(1)} / {(user?.max_storage_bytes || 0) / (1024 * 1024)} MB
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-white/20 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer hover:border-indigo-500/50 hover:bg-white/5 transition-all group min-h-[200px]"
        >
          <input type="file" className="hidden" ref={fileInputRef} onChange={handleUpload} accept=".txt,.md,.pdf,.csv" />
          {uploading ? (
            <Loader2 size={32} className="animate-spin text-indigo-400 mb-3" />
          ) : (
            <Upload size={32} className="text-slate-500 group-hover:text-indigo-400 mb-3 transition-colors" />
          )}
          <h3 className="text-white font-medium mb-1">{uploading ? 'Uploading...' : 'Upload Document'}</h3>
          <p className="text-slate-500 text-sm">PDF, TXT, MD up to 10MB</p>
        </div>

        {loading ? null : documents.map(doc => (
          <div key={doc.id} className="bg-white/5 border border-white/10 rounded-2xl p-5 flex flex-col hover:bg-white/[0.07] transition-all group">
            <div className="flex justify-between items-start mb-4">
              <div
                className={`px-2.5 py-1 rounded-md text-xs font-medium border flex items-center gap-1.5 ${getStatusColor(doc.status)}`}
              >
                {doc.status === 'PROCESSING' && <Loader2 size={12} className="animate-spin" />}
                {doc.status === 'READY' && <CheckCircle2 size={12} />}
                {doc.status === 'FAILED' && <AlertCircle size={12} />}
                {doc.status}
              </div>
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                {doc.status === 'FAILED' && (
                  <button onClick={() => handleReprocess(doc.id)} className="text-slate-400 hover:text-white p-1" title="Reprocess">
                    <RefreshCw size={16} />
                  </button>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); setEditingId(doc.id); setEditTitle(doc.title); }}
                  className="text-slate-400 hover:text-indigo-400 p-1"
                >
                  <Edit2 size={16} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(doc.id); }}
                  className="text-slate-400 hover:text-rose-400 p-1"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>

            <div className="flex-1">
              {editingId === doc.id ? (
                <input
                  autoFocus
                  className="w-full bg-[#111113] border border-indigo-500/50 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  onBlur={() => handleRename(doc.id)}
                  onKeyDown={e => e.key === 'Enter' && handleRename(doc.id)}
                />
              ) : (
                <h3
                  className="text-white font-medium line-clamp-2 cursor-pointer hover:text-indigo-400 transition-colors"
                  onClick={() => { if (doc.status === 'READY') navigate(`/chat?doc=${doc.id}`) }}
                >
                  {doc.title}
                </h3>
              )}
            </div>

            <div className="flex items-center gap-2 mt-4 text-xs text-slate-500">
              <FileText size={14} />
              <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
              <span>•</span>
              <span>{new Date(doc.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
