<template>
  <div class="treatment-planning max-w-4xl mx-auto">
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-4">AI Treatment Planning</h1>
      <p class="text-gray-600 mb-6">
        Generate evidence-based treatment recommendations using AI analysis of clinical guidelines and best practices.
      </p>

      <!-- Input Form -->
      <form @submit.prevent="getTreatmentRecommendations" class="space-y-4">
        <div>
          <label for="diagnosis" class="block text-sm font-medium text-gray-700 mb-2">
            Primary Diagnosis *
          </label>
          <input
            id="diagnosis"
            v-model="treatmentForm.diagnosis"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            placeholder="e.g., Major Depressive Disorder, Generalized Anxiety Disorder"
          />
        </div>

        <div>
          <label for="context" class="block text-sm font-medium text-gray-700 mb-2">
            Patient Context & Background
          </label>
          <textarea
            id="context"
            v-model="treatmentForm.patient_context"
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            placeholder="Patient demographics, severity, comorbidities, previous treatments, contraindications, preferences..."
          />
        </div>

        <button
          type="submit"
          :disabled="loading || !treatmentForm.diagnosis.trim()"
          class="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          <span v-if="loading">Generating Recommendations...</span>
          <span v-else>Generate Treatment Plan</span>
        </button>
      </form>

      <!-- Quick Diagnosis Buttons -->
      <div class="mt-4">
        <p class="text-sm text-gray-600 mb-2">Quick select common diagnoses:</p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="diagnosis in commonDiagnoses"
            :key="diagnosis"
            @click="treatmentForm.diagnosis = diagnosis"
            class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition"
          >
            {{ diagnosis }}
          </button>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="result" class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-xl font-semibold text-gray-800 mb-4">Treatment Recommendations</h2>
      
      <!-- Evidence Sources -->
      <div v-if="result.retrieved_sources?.length > 0" class="mb-6">
        <h3 class="text-lg font-medium text-gray-700 mb-3">Evidence-Based Sources</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="(source, index) in result.retrieved_sources"
            :key="index"
            class="bg-green-50 border border-green-200 rounded-lg p-4"
          >
            <div class="font-medium text-green-900">{{ source.treatment || 'Treatment Guideline' }}</div>
            <div class="text-sm text-green-700">For: {{ source.disorder }}</div>
            <div class="text-sm text-gray-600">
              Evidence Level: {{ source.evidence_level || 'A' }} | 
              Relevance: {{ Math.round(source.score * 100) }}%
            </div>
          </div>
        </div>
      </div>

      <!-- AI Recommendations -->
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-700 mb-3">Clinical Recommendations</h3>
        <div class="prose max-w-none">
          <div 
            v-html="formatAIResponse(result.ai_response?.response)"
            class="whitespace-pre-wrap text-gray-800 leading-relaxed"
          />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="mt-6 flex space-x-4">
        <button
          @click="exportRecommendations"
          class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
        >
          Export as PDF
        </button>
        <button
          @click="saveToTemplates"
          class="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition"
        >
          Save as Template
        </button>
      </div>

      <!-- Metadata -->
      <div class="mt-6 text-sm text-gray-500 border-t pt-4">
        <div class="flex justify-between items-center">
          <span>Model: {{ result.ai_response?.model_used }}</span>
          <span>Evidence Sources: {{ result.retrieved_documents }} guidelines</span>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div class="text-red-800">
        <strong>Error:</strong> {{ error }}
      </div>
    </div>

    <!-- Treatment Planning Guidelines -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
      <h3 class="font-medium text-blue-900 mb-2">Treatment Planning Guidelines</h3>
      <ul class="text-blue-800 text-sm space-y-1">
        <li>• Consider patient preferences and cultural factors</li>
        <li>• Review contraindications and medical history</li>
        <li>• Establish measurable treatment goals</li>
        <li>• Plan for outcome monitoring and assessment</li>
        <li>• Consider stepped care and treatment sequencing</li>
      </ul>
    </div>

    <!-- Clinical Disclaimer -->
    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-4">
      <div class="text-yellow-800 text-sm">
        <strong>Clinical Disclaimer:</strong> These recommendations are for educational purposes only. Treatment decisions must be individualized based on comprehensive clinical assessment and professional judgment.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { apiClient } from '../services/api'
import type { TreatmentRequest, RAGResponse } from '../types'

// Reactive state
const treatmentForm = ref<TreatmentRequest>({
  diagnosis: '',
  patient_context: ''
})

const loading = ref(false)
const result = ref<RAGResponse | null>(null)
const error = ref('')

const commonDiagnoses = [
  'Major Depressive Disorder',
  'Generalized Anxiety Disorder',
  'Post-Traumatic Stress Disorder',
  'Bipolar I Disorder',
  'ADHD',
  'Obsessive-Compulsive Disorder',
  'Panic Disorder',
  'Social Anxiety Disorder'
]

// Methods
const getTreatmentRecommendations = async () => {
  if (!treatmentForm.value.diagnosis.trim()) {
    error.value = 'Please enter a diagnosis'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const response = await apiClient.getTreatmentRecommendations(treatmentForm.value)
    result.value = response
  } catch (err: any) {
    console.error('Treatment recommendations error:', err)
    error.value = err.response?.data?.detail || 'Failed to get treatment recommendations. Please try again.'
  } finally {
    loading.value = false
  }
}

const formatAIResponse = (response?: string) => {
  if (!response) return ''
  
  // Convert markdown-style formatting to HTML
  return response
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
    .replace(/\n- /g, '<br>• ')
    .replace(/\n\d+\. /g, '<br>$&')
}

const exportRecommendations = () => {
  // Placeholder for PDF export functionality
  alert('PDF export functionality would be implemented here')
}

const saveToTemplates = () => {
  // Placeholder for template saving functionality
  alert('Template saving functionality would be implemented here')
}

// Sample data for quick testing
const loadSampleData = () => {
  treatmentForm.value = {
    diagnosis: 'Major Depressive Disorder',
    patient_context: '28-year-old female, moderate severity, first episode, no comorbidities. Patient prefers psychotherapy over medication initially. Good family support. Previous positive response to supportive counseling.'
  }
}

// Expose sample data function for development
if (process.env.NODE_ENV === 'development') {
  window.loadSampleTreatmentData = loadSampleData
}
</script>

<style scoped>
.treatment-planning {
  padding: 20px;
}

.prose {
  line-height: 1.6;
}

.prose p {
  margin-bottom: 1em;
}

.prose strong {
  font-weight: 600;
  color: #374151;
}

.prose em {
  font-style: italic;
  color: #4B5563;
}
</style>