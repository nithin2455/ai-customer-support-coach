import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Bot, UserCheck, Shield, BarChart3, User, LogOut, Cpu } from 'lucide-react';
import { fetchConfiguredModel } from '../services/api';

export default function Header({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();
  const role = user?.role || 'customer';
  const [modelName, setModelName] = useState('gemini-3.5-flash');

  useEffect(() => {
    fetchConfiguredModel().then(setModelName);
  }, []);

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-2.5 flex flex-wrap items-center justify-between shadow-xs z-10 shrink-0 font-sans">
      {/* Brand & Portal Label */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 bg-indigo-600 text-white rounded-lg flex items-center justify-center shadow-xs">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-slate-900 leading-tight">
            AI Support Coach
          </h1>
          <p className="text-[11px] text-slate-500">
            Customer Support Intelligence Platform
          </p>
        </div>
      </div>

      {/* Role-Protected Navigation (Only shown for Staff roles) */}
      {role !== 'customer' && (
        <nav className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
          <button
            onClick={() => setActiveTab('agent')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'agent'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5 text-indigo-600" />
            <span>Workspace</span>
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'analytics'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-indigo-600" />
            <span>Analytics</span>
          </button>

          {role === 'admin' && (
            <button
              onClick={() => setActiveTab('admin')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                activeTab === 'admin'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-indigo-600" />
              <span>Operations Admin</span>
            </button>
          )}
        </nav>
      )}

      {/* User Status & Logout */}
      <div className="flex items-center space-x-3 text-xs">
        <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium text-[11px]" title="Active Configured LLM Model">
          <Cpu className="w-3.5 h-3.5 text-indigo-600" />
          Model: Gemini {modelName}
        </span>

        <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium text-[11px]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          System Operational
        </span>

        {user && (
          <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
            <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
              {user.name?.charAt(0) || 'U'}
            </div>
            <div className="hidden md:block text-left">
              <p className="text-xs font-semibold text-slate-800 leading-tight">{user.name}</p>
              <p className="text-[10px] text-slate-400 capitalize">
                {role === 'customer' ? `${user.tier || 'Standard'} Customer` : role === 'agent' ? 'Support Agent' : 'System Admin'}
              </p>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
