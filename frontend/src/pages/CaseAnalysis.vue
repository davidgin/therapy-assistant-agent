<template>
  <div class="case-analysis max-w-6xl mx-auto">
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-4">Clinical Case Analysis</h1>
      <p class="text-gray-600 mb-6">
        Analyze clinical cases using AI-powered comprehensive assessment and diagnostic reasoning.
      </p>

      <!-- Case Selection -->
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Select a Case for Analysis
        </label>
        <div v-if="availableCases.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="case_ in availableCases"
            :key="case_.case_id"
            @click="selectCase(case_.case_id)"
            class="border-2 rounded-lg p-4 cursor-pointer transition hover:shadow-md"
            :class="selectedCaseId === case_.case_id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'"
          >
            <h3 class="font-medium text-gray-800">{{ case_.case_id }}</h3>
            <p class="text-sm text-gray-600 mt-1">
              {{ case_.patient_demographics?.age }}y {{ case_.patient_demographics?.gender }}, 
              {{ case_.patient_demographics?.occupation }}
            </p>
            <p class="text-sm text-blue-600 mt-1">{{ case_.suggested_diagnosis?.primary }}</p>
            <div class="mt-2">
              <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {{ case_.severity }} severity
              </span>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-gray-500 py-8">
          Loading clinical cases...
        </div>
      </div>

      <!-- Manual Case ID Input -->
      <div class="border-t pt-4">
        <label for="manual-case-id" class="block text-sm font-medium text-gray-700 mb-2">
          Or Enter Case ID Manually
        </label>
        <div class="flex space-x-2">
          <input
            id="manual-case-id"
            v-model="manualCaseId"
            type="text"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="e.g., CASE_001"
          />
          <button
            @click="analyzeCase(manualCaseId)"
            :disabled="loading || !manualCaseId.trim()"
            class="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50 transition"
          >
            Analyze Case
          </button>
        </div>
      </div>
    </div>

    <!-- Case Details & Analysis Results -->
    <div v-if="analysisResult" class="space-y-6">
      <!-- Case Information -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Case Information</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Demographics -->
          <div>
            <h3 class="text-lg font-medium text-gray-700 mb-3">Patient Demographics</h3>
            <div class="space-y-2 text-sm">
              <div><strong>Age:</strong> {{ analysisResult.case_data.patient_demographics?.age }} years</div>
              <div><strong>Gender:</strong> {{ analysisResult.case_data.patient_demographics?.gender }}</div>
              <div><strong>Occupation:</strong> {{ analysisResult.case_data.patient_demographics?.occupation }}</div>
            </div>
          </div>

          <!-- Current Diagnosis -->
          <div>
            <h3 class="text-lg font-medium text-gray-700 mb-3">Suggested Diagnosis</h3>
            <div class="space-y-2 text-sm">
              <div><strong>Primary:</strong> {{ analysisResult.case_data.suggested_diagnosis?.primary }}</div>
              <div><strong>DSM-5 Code:</strong> {{ analysisResult.case_data.suggested_diagnosis?.dsm5_code }}</div>
              <div><strong>Confidence:</strong> {{ Math.round((analysisResult.case_data.suggested_diagnosis?.confidence || 0) * 100) }}%</div>
              <div><strong>Severity:</strong> {{ analysisResult.case_data.severity }}</div>
            </div>
          </div>
        </div>

        <!-- Presenting Symptoms -->
        <div class="mt-6">
          <h3 class="text-lg font-medium text-gray-700 mb-3">Presenting Symptoms</h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="symptom in analysisResult.case_data.presenting_symptoms"
              :key="symptom"
              class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
            >
              {{ symptom }}
            </span>
          </div>
        </div>

        <!-- Clinical History -->
        <div class="mt-6">
          <h3 class="text-lg font-medium text-gray-700 mb-3">Clinical History</h3>
          <p class="text-gray-800 text-sm leading-relaxed">{{ analysisResult.case_data.clinical_history }}</p>
        </div>
      </div>

      <!-- Knowledge Sources -->
      <div v-if="analysisResult.knowledge_sources?.length > 0" class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Referenced Knowledge Sources</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="(source, index) in analysisResult.knowledge_sources"
            :key="index"
            class="bg-purple-50 border border-purple-200 rounded-lg p-4"
          >
            <div class="font-medium text-purple-900">{{ source.type || 'Clinical Knowledge' }}</div>
            <div class="text-sm text-purple-700">{{ source.disorder }}</div>
            <div class="text-sm text-gray-600">Relevance: {{ Math.round(source.score * 100) }}%</div>
          </div>
        </div>
      </div>

      <!-- AI Analysis -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">AI Clinical Analysis</h2>
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <div class="prose max-w-none">
            <div 
              v-html="formatAIResponse(analysisResult.ai_analysis?.response)"
              class="whitespace-pre-wrap text-gray-800 leading-relaxed"
            />
          </div>
        </div>

        <!-- Analysis Metadata -->
        <div class="mt-4 text-sm text-gray-500 border-t pt-4">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><strong>Case ID:</strong> {{ analysisResult.case_id }}</div>
            <div><strong>Model:</strong> {{ analysisResult.ai_analysis?.model_used }}</div>
            <div><strong>Knowledge Sources:</strong> {{ analysisResult.retrieved_documents }}</div>
            <div><strong>Analysis Date:</strong> {{ new Date().toLocaleDateString() }}</div>
          </div>
        </div>
      </div>

      <!-- Treatment Recommendations -->
      <div v-if="analysisResult.case_data.treatment_recommendations" class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Original Treatment Recommendations</h2>
        <ul class="space-y-2">
          <li
            v-for="recommendation in analysisResult.case_data.treatment_recommendations"
            :key="recommendation"
            class="flex items-start space-x-2"
          >
            <span class="text-green-600 mt-1">•</span>
            <span class="text-gray-800">{{ recommendation }}</span>
          </li>
        </ul>
      </div>

      <!-- Action Buttons -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex flex-wrap gap-4">
          <button
            @click="exportAnalysis"
            class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
          >
            Export Analysis
          </button>
          <button
            @click="generateTreatmentPlan"
            class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition"
          >
            Generate Treatment Plan
          </button>
          <button
            @click="compareWithGuidelines"
            class="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition"
          >
            Compare with Guidelines
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      <p class="mt-2 text-gray-600">Analyzing case...</p>
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
        <strong>Educational Use Only:</strong> This case analysis is for educational and training purposes. All diagnostic and treatment decisions must be made by qualified mental health professionals.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../services/api'
import type { SyntheticCase, CaseAnalysisResponse } from '../types'

const route = useRoute()
const router = useRouter()

// Reactive state
const availableCases = ref<SyntheticCase[]>([])
const selectedCaseId = ref('')
const manualCaseId = ref('')
const analysisResult = ref<CaseAnalysisResponse | null>(null)
const loading = ref(false)
const error = ref('')

// Methods
const loadAvailableCases = async () => {
  try {
    const response = await apiClient.getSyntheticCases()
    availableCases.value = response.cases || []
  } catch (err) {
    console.error('Failed to load cases:', err)
  }
}

const selectCase = (caseId: string) => {
  selectedCaseId.value = caseId
  manualCaseId.value = caseId
  analyzeCase(caseId)
}

const analyzeCase = async (caseId: string) => {
  if (!caseId.trim()) {
    error.value = 'Please select or enter a case ID'
    return
  }

  loading.value = true
  error.value = ''
  analysisResult.value = null

  try {
    const response = await apiClient.getCaseAnalysis(caseId)
    analysisResult.value = response
    selectedCaseId.value = caseId
  } catch (err: any) {
    console.error('Case analysis error:', err)
    error.value = err.response?.data?.detail || 'Failed to analyze case. Please try again.'
  } finally {
    loading.value = false
  }
}

const formatAIResponse = (response?: string) => {
  if (!response) return ''
  
  return response
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
    .replace(/\n- /g, '<br>• ')
    .replace(/\n\d+\. /g, '<br>$&')
}

const exportAnalysis = () => {
  alert('Export functionality would be implemented here')
}

const generateTreatmentPlan = () => {
  if (analysisResult.value?.case_data.suggested_diagnosis?.primary) {
    router.push({
      path: '/treatment',
      query: { 
        diagnosis: analysisResult.value.case_data.suggested_diagnosis.primary,
        caseId: analysisResult.value.case_id
      }
    })
  }
}

const compareWithGuidelines = () => {
  alert('Guideline comparison functionality would be implemented here')
}

// Lifecycle
onMounted(async () => {
  await loadAvailableCases()
  
  // Check if case ID was passed in URL
  const caseIdFromQuery = route.query.caseId as string
  if (caseIdFromQuery) {
    manualCaseId.value = caseIdFromQuery
    await analyzeCase(caseIdFromQuery)
  }
})
</script>

<style scoped>
.case-analysis {
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