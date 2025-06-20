import React, { useState } from 'react';
import { DiagnosticRequest, RAGResponse } from '../types';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';

const DiagnosticAssistant: React.FC = () => {
  const [formData, setFormData] = useState<DiagnosticRequest>({
    symptoms: '',
    patient_context: ''
  });
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.symptoms.trim()) {
      toast.error('Please enter patient symptoms');
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.getDiagnosticAssistance(formData);
      setResult(response);
      toast.success('Diagnostic analysis completed');
    } catch (error: any) {
      console.error('Diagnostic assistance error:', error);
      toast.error(error.response?.data?.detail || 'Failed to get diagnostic assistance');
    } finally {
      setLoading(false);
    }
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
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="card">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">AI Diagnostic Assistant</h1>
        <p className="text-gray-600 mb-6">
          Enter patient symptoms and context to receive AI-powered diagnostic assistance based on DSM-5-TR criteria.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="symptoms" className="block text-sm font-medium text-gray-700 mb-2">
              Patient Symptoms *
            </label>
            <textarea
              id="symptoms"
              rows={4}
              required
              value={formData.symptoms}
              onChange={(e) => setFormData(prev => ({ ...prev, symptoms: e.target.value }))}
              className="input-field"
              placeholder="Describe the patient's presenting symptoms in detail..."
            />
          </div>

          <div>
            <label htmlFor="context" className="block text-sm font-medium text-gray-700 mb-2">
              Additional Patient Context (Optional)
            </label>
            <textarea
              id="context"
              rows={3}
              value={formData.patient_context}
              onChange={(e) => setFormData(prev => ({ ...prev, patient_context: e.target.value }))}
              className="input-field"
              placeholder="Patient history, demographics, duration of symptoms, etc..."
            />
          </div>

          <button
            type="submit"
            disabled={loading || !formData.symptoms.trim()}
            className="btn-primary w-full"
          >
            {loading ? 'Analyzing...' : 'Get Diagnostic Assistance'}
          </button>
        </form>
      </div>

      {result && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">AI Analysis Results</h2>
          
          {result.retrieved_sources?.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-700 mb-3">Referenced Clinical Criteria</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.retrieved_sources.map((source, index) => (
                  <div
                    key={index}
                    className="bg-blue-50 border border-blue-200 rounded-lg p-4"
                  >
                    <div className="font-medium text-blue-900">{source.disorder}</div>
                    <div className="text-sm text-blue-700">Code: {source.code}</div>
                    <div className="text-sm text-gray-600">
                      Relevance: {Math.round(source.score * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-700 mb-3">Clinical Analysis</h3>
            <div 
              className="prose max-w-none text-gray-800 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: formatAIResponse(result.ai_response?.response) }}
            />
          </div>

          <div className="mt-6 text-sm text-gray-500 border-t pt-4">
            <div className="flex justify-between items-center">
              <span>Model: {result.ai_response?.model_used}</span>
              <span>Sources: {result.retrieved_documents} documents</span>
            </div>
          </div>
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="text-yellow-800 text-sm">
          <strong>Clinical Disclaimer:</strong> This AI assistant provides educational information only and is not a substitute for professional clinical judgment. All diagnostic decisions must be made by qualified mental health professionals based on comprehensive assessment.
        </div>
      </div>
    </div>
  );
};

export default DiagnosticAssistant;