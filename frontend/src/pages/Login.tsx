import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoginRequest } from '../types';

const Login: React.FC = () => {
  const { login, isAuthenticated, loading } = useAuth();
  const [formData, setFormData] = useState<LoginRequest>({
    username: '',
    password: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.username || !formData.password) return;

    setIsSubmitting(true);
    const success = await login(formData);
    setIsSubmitting(false);

    if (success) {
      // Navigation handled by AuthContext
    }
  };

  const handleDemoLogin = (role: 'therapist' | 'student') => {
    const credentials = {
      username: role === 'therapist' ? 'demo.therapist@example.com' : 'demo.student@example.com',
      password: 'demo123'
    };
    setFormData(credentials);
    login(credentials);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Therapy Assistant Agent
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in to your account
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="username" className="sr-only">
                Email or Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Email or Username"
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Password"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isSubmitting || !formData.username || !formData.password}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
        </form>

        {/* Demo Login Section */}
        <div className="mt-8 border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Demo Accounts</h3>
          <div className="space-y-2">
            <button
              onClick={() => handleDemoLogin('therapist')}
              className="w-full text-left px-4 py-2 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition"
            >
              <div className="font-medium text-blue-900">Licensed Therapist</div>
              <div className="text-sm text-blue-700">Access all RAG features</div>
            </button>
            <button
              onClick={() => handleDemoLogin('student')}
              className="w-full text-left px-4 py-2 bg-green-50 border border-green-200 rounded hover:bg-green-100 transition"
            >
              <div className="font-medium text-green-900">Student</div>
              <div className="text-sm text-green-700">Limited access for learning</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;