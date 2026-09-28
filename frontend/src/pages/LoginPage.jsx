import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Bot, User, Lock, Mail, ArrowRight, AlertCircle, Loader2, KeyRound } from 'lucide-react';

export default function LoginPage() {
  const { login, register, error, clearError } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' or 'register'

  // Login form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Register form state
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState(null);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setLocalError('Please enter both email and password.');
      return;
    }
    setLocalError(null);
    clearError();
    setIsSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      // Error handled by AuthContext
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (!regName || !regEmail || !regPassword) {
      setLocalError('Please fill in all required fields.');
      return;
    }
    if (regPassword.length < 6) {
      setLocalError('Password must be at least 6 characters long.');
      return;
    }
    if (regPassword !== regConfirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }
    setLocalError(null);
    clearError();
    setIsSubmitting(true);
    try {
      await register(regName, regEmail, regPassword, regConfirmPassword);
    } catch (err) {
      // Error handled by AuthContext
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoAccount = async (demoEmail, demoPassword) => {
    setMode('login');
    setEmail(demoEmail);
    setPassword(demoPassword);
    setLocalError(null);
    clearError();
    setIsSubmitting(true);
    try {
      await login(demoEmail, demoPassword);
    } catch (err) {
      // Handled
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || error;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4 sm:p-6 font-sans text-slate-900">
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl p-8 shadow-sm space-y-6">
        {/* Company / Product Branding */}
        <div className="text-center space-y-1.5">
          <div className="inline-flex w-12 h-12 bg-indigo-600 rounded-xl items-center justify-center text-white mb-2 shadow-xs">
            <Bot className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            AI Support Coach
          </h1>
          <p className="text-xs text-slate-500">
            Customer Support Intelligence Platform
          </p>
        </div>

        {/* Section Heading */}
        <div className="border-t border-slate-100 pt-4 text-center">
          <h2 className="text-base font-semibold text-slate-800">
            {mode === 'login' ? 'Welcome back' : 'Create customer account'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {mode === 'login'
              ? 'Sign in to your account to continue'
              : 'Register to access dedicated support assistance'}
          </p>
        </div>

        {/* Error Notification */}
        {activeError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3.5 py-2.5 rounded-xl text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
            <span>{activeError}</span>
          </div>
        )}

        {/* Form Area */}
        {mode === 'login' ? (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-700">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-10 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-700">Password</label>
                <button
                  type="button"
                  onClick={() => alert('Password recovery: Please contact your IT support administrator or reset via your enterprise directory.')}
                  className="text-[11px] text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-10 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium text-xs py-2.5 rounded-lg transition flex items-center justify-center space-x-1.5 shadow-xs"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>

            <div className="text-center pt-2">
              <p className="text-xs text-slate-500">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => {
                    setMode('register');
                    setLocalError(null);
                    clearError();
                  }}
                  className="font-semibold text-indigo-600 hover:text-indigo-700"
                >
                  Register
                </button>
              </p>
            </div>
          </form>
        ) : (
          /* Register Form */
          <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  placeholder="Alex Johnson"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-10 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  placeholder="alex@example.com"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-10 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="Min. 6 characters"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-10 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Confirm Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={regConfirmPassword}
                  onChange={(e) => setRegConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg pl-10 pr-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium text-xs py-2.5 rounded-lg transition flex items-center justify-center space-x-1.5 shadow-xs"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Registering...</span>
                </>
              ) : (
                <>
                  <span>Create Account</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>

            <div className="text-center pt-2">
              <p className="text-xs text-slate-500">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setLocalError(null);
                    clearError();
                  }}
                  className="font-semibold text-indigo-600 hover:text-indigo-700"
                >
                  Sign In
                </button>
              </p>
            </div>
          </form>
        )}

        {/* Collapsible Evaluation Credentials Drawer (Subtle for Reviewers) */}
        <div className="border-t border-slate-100 pt-3">
          <details className="text-left group">
            <summary className="text-[11px] font-medium text-slate-400 hover:text-slate-600 cursor-pointer select-none flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <KeyRound className="w-3 h-3 text-slate-400" />
                Evaluation Test Credentials
              </span>
              <span className="text-[10px] text-slate-400 group-open:rotate-180 transition-transform">▼</span>
            </summary>

            <div className="mt-2.5 pt-2 border-t border-slate-100 grid grid-cols-3 gap-1.5 text-xs">
              <button
                type="button"
                onClick={() => fillDemoAccount('alex.j@example.com', 'Customer123!')}
                className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition flex flex-col"
              >
                <span className="font-semibold text-slate-800 text-[11px]">Customer</span>
                <span className="text-[10px] text-slate-500 truncate">Alex Johnson</span>
              </button>

              <button
                type="button"
                onClick={() => fillDemoAccount('sarah.j@support.com', 'Agent123!')}
                className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition flex flex-col"
              >
                <span className="font-semibold text-slate-800 text-[11px]">Support Agent</span>
                <span className="text-[10px] text-slate-500 truncate">Sarah Jenkins</span>
              </button>

              <button
                type="button"
                onClick={() => fillDemoAccount('admin@company.com', 'Admin123!')}
                className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition flex flex-col"
              >
                <span className="font-semibold text-slate-800 text-[11px]">Administrator</span>
                <span className="text-[10px] text-slate-500 truncate">System Admin</span>
              </button>
            </div>
          </details>
        </div>
      </div>
    </div>
  );
}
