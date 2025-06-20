import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { SyntheticCase, SystemStatus } from '../types';
import { apiClient } from '../services/api';

const Dashboard: React.FC = () => {
  const { user, isLicensedProfessional } = useAuth();
  const navigate = useNavigate();
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [syntheticCases, setSyntheticCases] = useState<SyntheticCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [statusResponse, casesResponse] = await Promise.all([
          apiClient.getSystemStatus(),
          apiClient.getSyntheticCases()
        ]);
        
        setSystemStatus(statusResponse);
        setSyntheticCases(casesResponse.cases?.slice(0, 6) || []);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner h-8 w-8"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name}!
        </h1>
        <p className="text-gray-600">
          Your therapy assistant dashboard
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* System Status */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">System Status</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Vector DB:</span>
              <span className={systemStatus?.services?.chromadb?.status === 'healthy' ? 'text-green-600' : 'text-red-600'}>
                {systemStatus?.services?.chromadb?.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Knowledge Base:</span>
              <span className="text-blue-600">
                {systemStatus?.services?.chromadb?.stats?.total_documents || 0} docs
              </span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Quick Actions</h3>
          <div className="space-y-3">
            <button 
              onClick={() => navigate('/diagnostic')}
              disabled={!isLicensedProfessional}
              className="btn-primary w-full"
            >
              Diagnostic Assistant
            </button>
            <button 
              onClick={() => navigate('/treatment')}
              disabled={!isLicensedProfessional}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 transition"
            >
              Treatment Planning
            </button>
            <button 
              onClick={() => navigate('/case-analysis')}
              disabled={!isLicensedProfessional}
              className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:opacity-50 transition"
            >
              Case Analysis
            </button>
          </div>
        </div>

        {/* User Info */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Account Info</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Role:</span>
              <span className="text-blue-600 capitalize">{user?.role}</span>
            </div>
            <div className="flex justify-between">
              <span>License:</span>
              <span className="text-green-600">{user?.license_type?.toUpperCase() || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span>Last Login:</span>
              <span className="text-gray-600">{formatDate(user?.last_login)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Available Test Cases */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Available Test Cases</h3>
        {syntheticCases.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {syntheticCases.map((case_) => (
              <div 
                key={case_.case_id}
                className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                onClick={() => isLicensedProfessional && navigate(`/case-analysis?caseId=${case_.case_id}`)}
              >
                <h4 className="font-medium text-gray-800">{case_.case_id}</h4>
                <p className="text-sm text-gray-600 mt-1">
                  {case_.patient_demographics?.age}y {case_.patient_demographics?.gender}
                </p>
                <p className="text-sm text-blue-600 mt-1">
                  {case_.suggested_diagnosis?.primary}
                </p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {case_.presenting_symptoms?.slice(0, 2).map((symptom, index) => (
                    <span 
                      key={index}
                      className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
                    >
                      {symptom.substring(0, 20)}...
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            <p>No test cases available</p>
          </div>
        )}
      </div>

      {/* Student Notice */}
      {!isLicensedProfessional && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="text-yellow-800 text-sm">
            <strong>Student Account:</strong> Some features are restricted to licensed mental health professionals. 
            This account is for educational purposes only.
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;