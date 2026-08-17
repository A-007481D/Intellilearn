import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Brain, Mail, Lock, Loader2, AlertCircle } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Invalid credentials');
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      // Fetch user profile
      const meRes = await fetch('http://localhost:8000/api/v1/auth/me/', {
        headers: { Authorization: `Bearer ${data.access}` },
      });
      const user = await meRes.json();
      localStorage.setItem('user', JSON.stringify(user));
      navigate('/documents');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#000000] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-10">
          <div className="w-12 h-12 rounded bg-[#111] border border-[#222] flex items-center justify-center mb-4">
            <Brain size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">IntelliLearn</h1>
          <p className="text-[#A1A1AA] mt-2 text-sm">Sign in to your learning space</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-[#0A0A0A] border border-[#222] rounded-xl p-8 space-y-6">
          {error && (
            <div className="flex items-center gap-3 bg-red-950/30 border border-red-900/50 text-red-400 rounded-lg px-4 py-3 text-sm">
              <AlertCircle size={16} className="shrink-0" />
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-[#EDEDED] text-sm font-medium">Email</label>
            <div className="relative">
              <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#52525B]" />
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full bg-[#000] border border-[#333] rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-[#52525B] focus:outline-none focus:border-[#666] transition-colors text-sm"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[#EDEDED] text-sm font-medium">Password</label>
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#52525B]" />
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full bg-[#000] border border-[#333] rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-[#52525B] focus:outline-none focus:border-[#666] transition-colors text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-white text-black font-medium hover:bg-gray-200 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 text-sm"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : null}
            Sign In
          </button>

          <p className="text-center text-[#A1A1AA] text-sm mt-4">
            No account?{' '}
            <Link to="/register" className="text-white hover:underline font-medium">Create one free</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
