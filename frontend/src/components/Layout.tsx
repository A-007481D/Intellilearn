import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  BookOpen, MessageSquare, Brain, BarChart2, LogOut,
  Menu, ShieldCheck
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

  return (
    <div className="min-h-screen bg-[#000000] flex">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-[#000000] border-r border-[#222] flex flex-col transition-transform duration-300 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}>
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-[#222]">
          <div className="flex items-center gap-3">
            <Brain size={20} className="text-white" />
            <span className="text-white font-semibold tracking-tight">IntelliLearn</span>
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
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-[#111] text-white'
                    : 'text-[#A1A1AA] hover:text-white hover:bg-[#0A0A0A]'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
          {user?.role === 'ADMIN' && (
            <NavLink
              to="/admin"
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors mt-4 ${
                  isActive
                    ? 'bg-[#111] text-white'
                    : 'text-[#A1A1AA] hover:text-white hover:bg-[#0A0A0A]'
                }`
              }
            >
              <ShieldCheck size={16} />
              Admin Panel
            </NavLink>
          )}
        </nav>

        {/* User footer */}
        <div className="p-4 border-t border-[#222]">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded bg-[#111] border border-[#333] flex items-center justify-center text-white text-xs font-semibold">
              {user?.email?.[0]?.toUpperCase() || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{user?.email}</p>
              <p className="text-[#A1A1AA] text-xs">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={() => { logout(); }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-[#333] text-[#A1A1AA] hover:text-white hover:bg-[#111] transition-colors text-sm font-medium"
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/80 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-[#000]/90 backdrop-blur-md border-b border-[#222] px-4 h-16 flex items-center gap-4 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-[#A1A1AA] hover:text-white"
          >
            <Menu size={20} />
          </button>
          <span className="text-white font-semibold text-sm tracking-tight">IntelliLearn</span>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 md:p-10 max-w-6xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
