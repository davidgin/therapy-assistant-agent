import React, { useState } from 'react';
import { TreatmentRequest, RAGResponse } from '../types';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';

const commonDiagnoses = [
  'Major Depressive Disorder',
  'Generalized Anxiety Disorder',
  'Post-Traumatic Stress Disorder',
  'Bipolar I Disorder',
  'ADHD',
  'Obsessive-Compulsive Disorder',
  'Panic Disorder',
  'Social Anxiety Disorder'
];

const TreatmentPlanning: React.FC = () => {
  const [formData, setFormData] = useState<TreatmentRequest>({
    diagnosis: '',
    patient_context: ''
  });
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.diagnosis.trim()) {
      toast.error('Please enter a diagnosis');
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.getTreatmentRecommendations(formData);
      setResult(response);
      toast.success('Treatment recommendations generated');
    } catch (error: any) {
      console.error('Treatment recommendations error:', error);
      toast.error(error.response?.data?.detail || 'Failed to get treatment recommendations');
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
        <h1 className="text-2xl font-bold text-gray-800 mb-4">AI Treatment Planning</h1>
        <p className="text-gray-600 mb-6">
          Generate evidence-based treatment recommendations using AI analysis of clinical guidelines and best practices.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="diagnosis" className="block text-sm font-medium text-gray-700 mb-2">
              Primary Diagnosis *
            </label>
            <input
              id="diagnosis"
              type="text"
              required
              value={formData.diagnosis}
              onChange={(e) => setFormData(prev => ({ ...prev, diagnosis: e.target.value }))}
              className="input-field"
              placeholder="e.g., Major Depressive Disorder, Generalized Anxiety Disorder"
            />
          </div>

          <div>
            <label htmlFor="context" className="block text-sm font-medium text-gray-700 mb-2">
              Patient Context & Background
            </label>
            <textarea
              id="context"
              rows={4}
              value={formData.patient_context}
              onChange={(e) => setFormData(prev => ({ ...prev, patient_context: e.target.value }))}
              className="input-field"
              placeholder="Patient demographics, severity, comorbidities, previous treatments, contraindications, preferences..."
            />
          </div>

          <button
            type="submit"
            disabled={loading || !formData.diagnosis.trim()}
            className="btn-primary w-full"
          >
            {loading ? 'Generating Recommendations...' : 'Generate Treatment Plan'}
          </button>
        </form>

        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">Quick select common diagnoses:</p>
          <div className="flex flex-wrap gap-2">
            {commonDiagnoses.map((diagnosis) => (
              <button
                key={diagnosis}
                onClick={() => setFormData(prev => ({ ...prev, diagnosis }))}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition"
              >
                {diagnosis}
              </button>
            ))}
          </div>
        </div>
      </div>

      {result && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Treatment Recommendations</h2>
          
          {result.retrieved_sources?.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-700 mb-3">Evidence-Based Sources</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.retrieved_sources.map((source, index) => (
                  <div
                    key={index}
                    className="bg-green-50 border border-green-200 rounded-lg p-4"
                  >
                    <div className="font-medium text-green-900">
                      {source.treatment || 'Treatment Guideline'}
                    </div>
                    <div className="text-sm text-green-700">For: {source.disorder}</div>
                    <div className="text-sm text-gray-600">
                      Evidence Level: {source.evidence_level || 'A'} | 
                      Relevance: {Math.round(source.score * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-700 mb-3">Clinical Recommendations</h3>
            <div 
              className="prose max-w-none text-gray-800 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: formatAIResponse(result.ai_response?.response) }}
            />
          </div>

          <div className="mt-6 text-sm text-gray-500 border-t pt-4">
            <div className="flex justify-between items-center">
              <span>Model: {result.ai_response?.model_used}</span>
              <span>Evidence Sources: {result.retrieved_documents} guidelines</span>
            </div>
          </div>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">Treatment Planning Guidelines</h3>
        <ul className="text-blue-800 text-sm space-y-1">
          <li>• Consider patient preferences and cultural factors</li>
          <li>• Review contraindications and medical history</li>
          <li>• Establish measurable treatment goals</li>
          <li>• Plan for outcome monitoring and assessment</li>
          <li>• Consider stepped care and treatment sequencing</li>
        </ul>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="text-yellow-800 text-sm">
          <strong>Clinical Disclaimer:</strong> These recommendations are for educational purposes only. Treatment decisions must be individualized based on comprehensive clinical assessment and professional judgment.
        </div>
      </div>
    </div>
  );
};

export default TreatmentPlanning;