import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface LicensedRouteProps {
  children: React.ReactNode;
}

const LicensedRoute: React.FC<LicensedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLicensedProfessional, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isLicensedProfessional) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Access Restricted
          </h1>
          <p className="text-gray-600 mb-6">
            This feature is only available to licensed mental health professionals.
          </p>
          <Navigate to="/" replace />
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default LicensedRoute;