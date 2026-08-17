import React, { useEffect, useState, useRef } from 'react';
import { apiGet, apiUpload, apiDelete, apiPatch, apiPost } from '../lib/api';
import { getUser } from '../lib/auth';
import { Upload, FileText, Trash2, Edit2, Loader2, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Document {
  id: string;
  title: string;
  status: 'UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED';
  file_size_bytes: number;
  created_at: string;
  error_message?: string;
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
      const data = await apiGet<Document[]>('/documents/');
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
      await apiUpload('/documents/', formData);
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
      await apiDelete(`/documents/${id}/`);
      setDocuments(docs => docs.filter(d => d.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleRename = async (id: string) => {
    if (!editTitle) return;
    try {
      await apiPatch(`/documents/${id}/`, { title: editTitle });
      setDocuments(docs => docs.map(d => d.id === id ? { ...d, title: editTitle } : d));
      setEditingId(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReprocess = async (id: string) => {
    try {
      await apiPost(`/documents/${id}/reprocess/`);
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
          <h1 className="text-2xl font-semibold text-white tracking-tight">Documents</h1>
          <p className="text-[#A1A1AA] text-sm mt-1">Manage your knowledge base files</p>
        </div>
        <div className="flex items-center gap-4 bg-[#0A0A0A] border border-[#222] rounded-lg px-4 py-2">
          <div className="text-sm">
            <span className="text-[#A1A1AA]">Docs: </span>
            <span className="text-white font-medium">{documents.length} / {user?.max_documents}</span>
          </div>
          <div className="w-px h-4 bg-[#333]"></div>
          <div className="text-sm">
            <span className="text-[#A1A1AA]">Storage: </span>
            <span className="text-white font-medium">
              {(totalSize / (1024 * 1024)).toFixed(1)} / {(user?.max_storage_bytes || 0) / (1024 * 1024)} MB
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border border-dashed border-[#333] rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:border-[#666] hover:bg-[#0A0A0A] transition-colors group min-h-[180px]"
        >
          <input type="file" className="hidden" ref={fileInputRef} onChange={handleUpload} accept=".txt,.md,.pdf,.csv" />
          {uploading ? (
            <Loader2 size={24} className="animate-spin text-[#EDEDED] mb-3" />
          ) : (
            <Upload size={24} className="text-[#52525B] group-hover:text-[#EDEDED] mb-3 transition-colors" />
          )}
          <h3 className="text-[#EDEDED] font-medium text-sm mb-1">{uploading ? 'Uploading...' : 'Upload Document'}</h3>
          <p className="text-[#52525B] text-xs">PDF, TXT, MD up to 10MB</p>
        </div>

        {loading ? null : documents.map(doc => (
          <div key={doc.id} className="minimal-card p-5 flex flex-col hover:border-[#444] transition-colors group">
            <div className="flex justify-between items-start mb-4">
              <div
                className={`px-2 py-0.5 rounded text-[11px] font-medium border flex items-center gap-1 uppercase ${getStatusColor(doc.status)}`}
              >
                {doc.status === 'PROCESSING' && <Loader2 size={10} className="animate-spin" />}
                {doc.status === 'READY' && <CheckCircle2 size={10} />}
                {doc.status === 'FAILED' && <AlertCircle size={10} />}
                {doc.status}
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {doc.status === 'FAILED' && (
                  <button onClick={() => handleReprocess(doc.id)} className="text-[#52525B] hover:text-white p-1 rounded hover:bg-[#111]" title="Reprocess">
                    <RefreshCw size={14} />
                  </button>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); setEditingId(doc.id); setEditTitle(doc.title); }}
                  className="text-[#52525B] hover:text-white p-1 rounded hover:bg-[#111]"
                >
                  <Edit2 size={14} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(doc.id); }}
                  className="text-[#52525B] hover:text-red-400 p-1 rounded hover:bg-red-950/30"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>

            <div className="flex-1">
              {editingId === doc.id ? (
                <input
                  autoFocus
                  className="w-full bg-[#000] border border-[#555] rounded px-2 py-1 text-white text-sm focus:outline-none"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  onBlur={() => handleRename(doc.id)}
                  onKeyDown={e => e.key === 'Enter' && handleRename(doc.id)}
                />
              ) : (
                <h3
                  className="text-[#EDEDED] font-medium text-sm line-clamp-2 cursor-pointer hover:text-white transition-colors"
                  onClick={() => { if (doc.status === 'READY') navigate(`/chat?doc=${doc.id}`) }}
                >
                  {doc.title}
                </h3>
              )}
            </div>

            {doc.status === 'FAILED' && doc.error_message && (
              <div className="mt-3 p-2 bg-red-950/30 border border-red-900/50 rounded flex items-start gap-2 text-xs text-red-400">
                <AlertCircle size={12} className="shrink-0 mt-0.5" />
                <span className="leading-tight">{doc.error_message}</span>
              </div>
            )}

            <div className="flex items-center gap-2 mt-4 text-[11px] text-[#52525B]">
              <FileText size={12} />
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
