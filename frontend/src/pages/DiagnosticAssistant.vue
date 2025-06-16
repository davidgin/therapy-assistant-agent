<template>
  <div class="diagnostic-assistant max-w-4xl mx-auto">
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-4">AI Diagnostic Assistant</h1>
      <p class="text-gray-600 mb-6">
        Enter patient symptoms and context to receive AI-powered diagnostic assistance based on DSM-5-TR criteria.
      </p>

      <!-- Input Form -->
      <form @submit.prevent="getDiagnosticAssistance" class="space-y-4">
        <div>
          <label for="symptoms" class="block text-sm font-medium text-gray-700 mb-2">
            Patient Symptoms *
          </label>
          <textarea
            id="symptoms"
            v-model="diagnosticForm.symptoms"
            rows="4"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Describe the patient's presenting symptoms in detail..."
          />
        </div>

        <div>
          <label for="context" class="block text-sm font-medium text-gray-700 mb-2">
            Additional Patient Context (Optional)
          </label>
          <textarea
            id="context"
            v-model="diagnosticForm.patient_context"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Patient history, demographics, duration of symptoms, etc..."
          />
        </div>

        <button
          type="submit"
          :disabled="loading || !diagnosticForm.symptoms.trim()"
          class="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          <span v-if="loading">Analyzing...</span>
          <span v-else>Get Diagnostic Assistance</span>
        </button>
      </form>
    </div>

    <!-- Results Section -->
    <div v-if="result" class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-xl font-semibold text-gray-800 mb-4">AI Analysis Results</h2>
      
      <!-- Retrieved Sources -->
      <div v-if="result.retrieved_sources?.length > 0" class="mb-6">
        <h3 class="text-lg font-medium text-gray-700 mb-3">Referenced Clinical Criteria</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="(source, index) in result.retrieved_sources"
            :key="index"
            class="bg-blue-50 border border-blue-200 rounded-lg p-4"
          >
            <div class="font-medium text-blue-900">{{ source.disorder }}</div>
            <div class="text-sm text-blue-700">Code: {{ source.code }}</div>
            <div class="text-sm text-gray-600">Relevance: {{ Math.round(source.score * 100) }}%</div>
          </div>
        </div>
      </div>

      <!-- AI Response -->
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-700 mb-3">Clinical Analysis</h3>
        <div class="prose max-w-none">
          <div 
            v-html="formatAIResponse(result.ai_response?.response)"
            class="whitespace-pre-wrap text-gray-800 leading-relaxed"
          />
        </div>
      </div>

      <!-- Metadata -->
      <div class="mt-6 text-sm text-gray-500 border-t pt-4">
        <div class="flex justify-between items-center">
          <span>Model: {{ result.ai_response?.model_used }}</span>
          <span>Sources: {{ result.retrieved_documents }} documents</span>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div class="text-red-800">
        <strong>Error:</strong> {{ error }}
      </div>
    </div>

    <!-- Clinical Disclaimer -->
    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-6">
      <div class="text-yellow-800 text-sm">
        <strong>Clinical Disclaimer:</strong> This AI assistant provides educational information only and is not a substitute for professional clinical judgment. All diagnostic decisions must be made by qualified mental health professionals based on comprehensive assessment.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { apiClient } from '../services/api'
import type { DiagnosticRequest, RAGResponse } from '../types'

// Reactive state
const diagnosticForm = ref<DiagnosticRequest>({
  symptoms: '',
  patient_context: ''
})

const loading = ref(false)
const result = ref<RAGResponse | null>(null)
const error = ref('')

// Methods
const getDiagnosticAssistance = async () => {
  if (!diagnosticForm.value.symptoms.trim()) {
    error.value = 'Please enter patient symptoms'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    const response = await apiClient.getDiagnosticAssistance(diagnosticForm.value)
    result.value = response
  } catch (err: any) {
    console.error('Diagnostic assistance error:', err)
    error.value = err.response?.data?.detail || 'Failed to get diagnostic assistance. Please try again.'
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

// Sample data for quick testing
const loadSampleData = () => {
  diagnosticForm.value = {
    symptoms: 'Patient reports persistent sadness lasting 3 weeks, loss of interest in activities, difficulty concentrating at work, sleep disturbances with early morning awakening, fatigue and low energy, and feelings of worthlessness.',
    patient_context: '28-year-old female software engineer. Recent job loss 4 weeks ago. No prior psychiatric history. Family history of depression (mother). PHQ-9 score: 16.'
  }
}

// Expose sample data function for development
if (process.env.NODE_ENV === 'development') {
  window.loadSampleDiagnosticData = loadSampleData
}
</script>

<style scoped>
.diagnostic-assistant {
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