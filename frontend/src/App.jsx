import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Header from './components/Header';
import AgentDashboard from './pages/AgentDashboard';
import CustomerView from './pages/CustomerView';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import AdminDashboard from './pages/AdminDashboard';
import LoginPage from './pages/LoginPage';
import { Loader2 } from 'lucide-react';

function AppContent() {
  const { user, isAuthenticated, isLoading, role } = useAuth();
  const [activeTab, setActiveTab] = useState('agent');

  // Synchronize default tab with authenticated role
  useEffect(() => {
    if (role === 'customer') {
      setActiveTab('customer');
    } else if (role === 'agent') {
      setActiveTab('agent');
    } else if (role === 'admin') {
      setActiveTab('admin');
    }
  }, [role]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center text-slate-600 text-xs font-sans space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <span className="font-medium text-slate-700">Connecting to AI Support Coach...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Strict route protection: Customers can ONLY ever see the Customer Support Portal
  if (role === 'customer') {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
        <Header activeTab="customer" setActiveTab={() => {}} />
        <main className="flex-1 flex flex-col overflow-hidden">
          <CustomerView />
        </main>
      </div>
    );
  }

  // Agent role cannot access Admin dashboard
  const currentTab = (role === 'agent' && activeTab === 'admin') ? 'agent' : activeTab;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Header activeTab={currentTab} setActiveTab={setActiveTab} />
      <main className="flex-1 flex flex-col overflow-hidden">
        {currentTab === 'agent' && <AgentDashboard />}
        {currentTab === 'analytics' && <AnalyticsDashboard />}
        {currentTab === 'admin' && role === 'admin' && <AdminDashboard />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
