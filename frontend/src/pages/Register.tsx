import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Brain, Mail, Lock, Loader2, AlertCircle, User } from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('STUDENT');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.email?.[0] || 'Registration failed');
      navigate('/login');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-0 right-1/2 translate-x-1/2 w-[800px] h-[400px] bg-purple-900/30 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-indigo-900/20 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        <div className="flex flex-col items-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mb-4 shadow-2xl shadow-purple-500/40">
            <Brain size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Join IntelliLearn</h1>
          <p className="text-slate-400 mt-1">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white/5 border border-white/10 backdrop-blur-xl rounded-3xl p-8 space-y-5">
          {error && (
            <div className="flex items-center gap-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl px-4 py-3 text-sm">
              <AlertCircle size={16} className="shrink-0" />
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-slate-300 text-sm font-medium">Email</label>
            <div className="relative">
              <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-purple-500/50 focus:bg-white/10 transition-all"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-slate-300 text-sm font-medium">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-purple-500/50 focus:bg-white/10 transition-all"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-slate-300 text-sm font-medium">Confirm</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:border-purple-500/50 focus:bg-white/10 transition-all"
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-slate-300 text-sm font-medium">Role</label>
            <div className="relative">
              <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <select
                value={role}
                onChange={e => setRole(e.target.value)}
                className="w-full bg-[#111113] border border-white/10 rounded-xl pl-10 pr-4 py-3 text-white focus:outline-none focus:border-purple-500/50 transition-all appearance-none"
              >
                <option value="STUDENT">Student</option>
                <option value="TEACHER">Teacher</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold hover:from-purple-500 hover:to-indigo-500 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-purple-500/30"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : null}
            Create Account
          </button>

          <p className="text-center text-slate-500 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-purple-400 hover:text-purple-300 font-medium">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
