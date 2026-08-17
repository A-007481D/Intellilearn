import React, { useEffect, useState } from 'react';
import { apiGet, apiPatch, apiPost } from '../lib/api';
import { Users, Send, CheckCircle2, AlertCircle } from 'lucide-react';

interface User {
  id: string;
  email: string;
  role: string;
  max_documents: number;
  max_storage_bytes: number;
}

export default function Admin() {
  const [users, setUsers] = useState<User[]>([]);
  const [expandedUser, setExpandedUser] = useState<string | null>(null);
  
  // Bulk notify
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [notifStatus, setNotifStatus] = useState<'idle'|'sending'|'success'|'error'>('idle');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const data = await apiGet<User[]>('/auth/admin/users/');
      setUsers(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpdateQuota = async (id: string, maxDocs: number, maxStorage: number) => {
    try {
      await apiPatch(`/auth/admin/users/${id}/`, {
        max_documents: maxDocs,
        max_storage_bytes: maxStorage
      });
      fetchUsers();
      setExpandedUser(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendNotification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedUsers.size === 0) return;
    setNotifStatus('sending');
    try {
      await apiPost('/auth/admin/notify/', {
        user_ids: Array.from(selectedUsers),
        subject,
        message
      });
      setNotifStatus('success');
      setSubject('');
      setMessage('');
      setSelectedUsers(new Set());
      setTimeout(() => setNotifStatus('idle'), 3000);
    } catch (e) {
      setNotifStatus('error');
      setTimeout(() => setNotifStatus('idle'), 3000);
    }
  };

  const toggleUserSelection = (id: string) => {
    const newSet = new Set(selectedUsers);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedUsers(newSet);
  };

  const toggleAll = () => {
    if (selectedUsers.size === users.length) setSelectedUsers(new Set());
    else setSelectedUsers(new Set(users.map(u => u.id)));
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex items-center gap-3">
        <Users className="text-amber-400" size={28} />
        <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Users Table */}
        <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-white/10 bg-white/[0.02]">
            <h2 className="text-lg font-semibold text-white">User Management</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-400">
              <thead className="bg-white/5 text-slate-300">
                <tr>
                  <th className="p-4 w-10">
                    <input type="checkbox" checked={selectedUsers.size === users.length && users.length > 0} onChange={toggleAll} className="accent-amber-500" />
                  </th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Role</th>
                  <th className="p-4">Docs Quota</th>
                  <th className="p-4">Storage (MB)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {users.map(u => (
                  <React.Fragment key={u.id}>
                    <tr className="hover:bg-white/5 cursor-pointer transition-colors" onClick={() => setExpandedUser(expandedUser === u.id ? null : u.id)}>
                      <td className="p-4" onClick={e => e.stopPropagation()}>
                        <input type="checkbox" checked={selectedUsers.has(u.id)} onChange={() => toggleUserSelection(u.id)} className="accent-amber-500" />
                      </td>
                      <td className="p-4 text-white font-medium">{u.email}</td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${u.role === 'ADMIN' ? 'bg-amber-500/20 text-amber-400' : 'bg-white/10'}`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="p-4">{u.max_documents}</td>
                      <td className="p-4">{(u.max_storage_bytes / (1024*1024)).toFixed(0)}</td>
                    </tr>
                    {expandedUser === u.id && (
                      <tr className="bg-white/[0.02]">
                        <td colSpan={5} className="p-4">
                          <form 
                            onSubmit={(e) => {
                              e.preventDefault();
                              const fd = new FormData(e.target as HTMLFormElement);
                              handleUpdateQuota(u.id, Number(fd.get('docs')), Number(fd.get('storage')) * 1024 * 1024);
                            }}
                            className="flex items-end gap-4 bg-[#111113] p-4 rounded-xl border border-white/5"
                          >
                            <div>
                              <label className="block text-xs text-slate-500 mb-1">Max Docs</label>
                              <input name="docs" type="number" defaultValue={u.max_documents} className="w-24 bg-white/5 border border-white/10 rounded px-2 py-1 text-white text-sm outline-none focus:border-amber-500" />
                            </div>
                            <div>
                              <label className="block text-xs text-slate-500 mb-1">Max Storage (MB)</label>
                              <input name="storage" type="number" defaultValue={(u.max_storage_bytes / (1024*1024)).toFixed(0)} className="w-24 bg-white/5 border border-white/10 rounded px-2 py-1 text-white text-sm outline-none focus:border-amber-500" />
                            </div>
                            <button type="submit" className="px-4 py-1.5 bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 rounded text-sm font-medium transition-colors">
                              Save Quotas
                            </button>
                          </form>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Bulk Notify */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 h-fit">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Send size={18} className="text-amber-400" /> Notify Users
          </h2>
          <form onSubmit={handleSendNotification} className="space-y-4">
            <div className="text-sm text-slate-400 mb-2">
              Selected: <span className="text-white font-medium">{selectedUsers.size}</span> users
            </div>
            <div>
              <input 
                required 
                value={subject} 
                onChange={e => setSubject(e.target.value)} 
                placeholder="Subject" 
                className="w-full bg-[#111113] border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:border-amber-500 outline-none" 
              />
            </div>
            <div>
              <textarea 
                required 
                value={message} 
                onChange={e => setMessage(e.target.value)} 
                placeholder="Message body..." 
                rows={4}
                className="w-full bg-[#111113] border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:border-amber-500 outline-none resize-none" 
              />
            </div>
            <button 
              type="submit" 
              disabled={selectedUsers.size === 0 || notifStatus === 'sending'}
              className="w-full py-2.5 bg-amber-600 text-white rounded-xl font-medium hover:bg-amber-500 disabled:opacity-50 transition-colors flex justify-center items-center gap-2"
            >
              {notifStatus === 'success' && <CheckCircle2 size={16} />}
              {notifStatus === 'error' && <AlertCircle size={16} />}
              {notifStatus === 'idle' && 'Send Notification'}
              {notifStatus === 'sending' && 'Sending...'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
