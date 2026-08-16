import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  BookOpen, MessageSquare, Brain, BarChart2, LogOut,
  Menu, X, ShieldCheck, Upload
} from 'lucide-react';
import { logout, getUser } from '../lib/auth';

const NAV_ITEMS = [
  { to: '/documents', label: 'Documents', icon: BookOpen },
  { to: '/chat', label: 'AI Chat', icon: MessageSquare },
  { to: '/quizzes', label: 'Quizzes', icon: Brain },
  { to: '/dashboard', label: 'Analytics', icon: BarChart2 },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const user = getUser();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0A0A0B] flex">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-white/5 backdrop-blur-xl border-r border-white/10 flex flex-col transition-transform duration-300 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}>
        {/* Logo */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center">
              <Brain size={18} className="text-white" />
            </div>
            <span className="text-white font-bold text-lg tracking-tight">IntelliLearn</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
          {user?.role === 'ADMIN' && (
            <NavLink
              to="/admin"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <ShieldCheck size={18} />
              Admin Panel
            </NavLink>
          )}
        </nav>

        {/* User footer */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
              {user?.email?.[0]?.toUpperCase() || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{user?.email}</p>
              <p className="text-slate-500 text-xs">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={() => { logout(); }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all text-sm"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-[#0A0A0B]/80 backdrop-blur-xl border-b border-white/10 px-4 py-3 flex items-center gap-4 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-slate-400 hover:text-white"
          >
            <Menu size={22} />
          </button>
          <span className="text-white font-semibold">IntelliLearn</span>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
