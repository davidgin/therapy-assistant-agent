import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SyntheticCase, CaseAnalysisResponse } from '../types';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';

const CaseAnalysis: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [availableCases, setAvailableCases] = useState<SyntheticCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [manualCaseId, setManualCaseId] = useState('');
  const [analysisResult, setAnalysisResult] = useState<CaseAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load available cases
    const loadCases = async () => {
      try {
        const response = await apiClient.getSyntheticCases();
        setAvailableCases(response.cases || []);
      } catch (error) {
        console.error('Failed to load cases:', error);
      }
    };

    loadCases();

    // Check for case ID in URL params
    const caseIdFromUrl = searchParams.get('caseId');
    if (caseIdFromUrl) {
      setManualCaseId(caseIdFromUrl);
      analyzeCase(caseIdFromUrl);
    }
  }, [searchParams]);

  const analyzeCase = async (caseId: string) => {
    if (!caseId.trim()) {
      toast.error('Please select or enter a case ID');
      return;
    }

    setLoading(true);
    setAnalysisResult(null);

    try {
      const response = await apiClient.getCaseAnalysis(caseId);
      setAnalysisResult(response);
      setSelectedCaseId(caseId);
      toast.success('Case analysis completed');
    } catch (error: any) {
      console.error('Case analysis error:', error);
      toast.error(error.response?.data?.detail || 'Failed to analyze case');
    } finally {
      setLoading(false);
    }
  };

  const selectCase = (caseId: string) => {
    setSelectedCaseId(caseId);
    setManualCaseId(caseId);
    analyzeCase(caseId);
  };

  const formatAIResponse = (response?: string) => {
    if (!response) return '';
    return response
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>')
      .replace(/\n- /g, '<br>• ')
      .replace(/\n\d+\. /g, '<br>$&');
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="card">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">Clinical Case Analysis</h1>
        <p className="text-gray-600 mb-6">
          Analyze clinical cases using AI-powered comprehensive assessment and diagnostic reasoning.
        </p>

        {/* Case Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select a Case for Analysis
          </label>
          {availableCases.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {availableCases.map((case_) => (
                <div
                  key={case_.case_id}
                  onClick={() => selectCase(case_.case_id)}
                  className={`border-2 rounded-lg p-4 cursor-pointer transition hover:shadow-md ${
                    selectedCaseId === case_.case_id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <h3 className="font-medium text-gray-800">{case_.case_id}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {case_.patient_demographics?.age}y {case_.patient_demographics?.gender}, 
                    {case_.patient_demographics?.occupation}
                  </p>
                  <p className="text-sm text-blue-600 mt-1">{case_.suggested_diagnosis?.primary}</p>
                  <div className="mt-2">
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {case_.severity} severity
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              Loading clinical cases...
            </div>
          )}
        </div>

        {/* Manual Case ID Input */}
        <div className="border-t pt-4">
          <label htmlFor="manual-case-id" className="block text-sm font-medium text-gray-700 mb-2">
            Or Enter Case ID Manually
          </label>
          <div className="flex space-x-2">
            <input
              id="manual-case-id"
              type="text"
              value={manualCaseId}
              onChange={(e) => setManualCaseId(e.target.value)}
              className="flex-1 input-field"
              placeholder="e.g., CASE_001"
            />
            <button
              onClick={() => analyzeCase(manualCaseId)}
              disabled={loading || !manualCaseId.trim()}
              className="btn-primary"
            >
              Analyze Case
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="loading-spinner h-8 w-8 mx-auto mb-2"></div>
          <p className="text-gray-600">Analyzing case...</p>
        </div>
      )}

      {/* Case Analysis Results */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Case Information */}
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Case Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-3">Patient Demographics</h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Age:</strong> {analysisResult.case_data.patient_demographics?.age} years</div>
                  <div><strong>Gender:</strong> {analysisResult.case_data.patient_demographics?.gender}</div>
                  <div><strong>Occupation:</strong> {analysisResult.case_data.patient_demographics?.occupation}</div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-3">Suggested Diagnosis</h3>
                <div className="space-y-2 text-sm">
                  <div><strong>Primary:</strong> {analysisResult.case_data.suggested_diagnosis?.primary}</div>
                  <div><strong>DSM-5 Code:</strong> {analysisResult.case_data.suggested_diagnosis?.dsm5_code}</div>
                  <div><strong>Confidence:</strong> {Math.round((analysisResult.case_data.suggested_diagnosis?.confidence || 0) * 100)}%</div>
                  <div><strong>Severity:</strong> {analysisResult.case_data.severity}</div>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-700 mb-3">Presenting Symptoms</h3>
              <div className="flex flex-wrap gap-2">
                {analysisResult.case_data.presenting_symptoms?.map((symptom, index) => (
                  <span
                    key={index}
                    className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                  >
                    {symptom}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-700 mb-3">Clinical History</h3>
              <p className="text-gray-800 text-sm leading-relaxed">{analysisResult.case_data.clinical_history}</p>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">AI Clinical Analysis</h2>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <div 
                className="prose max-w-none text-gray-800 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: formatAIResponse(analysisResult.ai_analysis?.response) }}
              />
            </div>

            <div className="mt-4 text-sm text-gray-500 border-t pt-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div><strong>Case ID:</strong> {analysisResult.case_id}</div>
                <div><strong>Model:</strong> {analysisResult.ai_analysis?.model_used}</div>
                <div><strong>Knowledge Sources:</strong> {analysisResult.retrieved_documents}</div>
                <div><strong>Analysis Date:</strong> {new Date().toLocaleDateString()}</div>
              </div>
            </div>
          </div>

          {/* Treatment Recommendations */}
          {analysisResult.case_data.treatment_recommendations && (
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Original Treatment Recommendations</h2>
              <ul className="space-y-2">
                {analysisResult.case_data.treatment_recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span className="text-gray-800">{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="text-yellow-800 text-sm">
          <strong>Educational Use Only:</strong> This case analysis is for educational and training purposes. All diagnostic and treatment decisions must be made by qualified mental health professionals.
        </div>
      </div>
    </div>
  );
};

export default CaseAnalysis;