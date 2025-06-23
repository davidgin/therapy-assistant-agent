import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import LicensedRoute from './components/LicensedRoute';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import DiagnosticAssistant from './pages/DiagnosticAssistant';
import TreatmentPlanning from './pages/TreatmentPlanning';
import CaseAnalysis from './pages/CaseAnalysis';

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          } />
          <Route path="/diagnostic" element={
            <LicensedRoute>
              <Layout>
                <DiagnosticAssistant />
              </Layout>
            </LicensedRoute>
          } />
          <Route path="/treatment" element={
            <LicensedRoute>
              <Layout>
                <TreatmentPlanning />
              </Layout>
            </LicensedRoute>
          } />
          <Route path="/case-analysis" element={
            <LicensedRoute>
              <Layout>
                <CaseAnalysis />
              </Layout>
            </LicensedRoute>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster position="top-right" />
      </div>
    </AuthProvider>
  );
}

export default App;