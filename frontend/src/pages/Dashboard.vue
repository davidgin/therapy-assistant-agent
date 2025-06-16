<template>
  <div class="dashboard">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <!-- System Status Card -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold mb-4 text-gray-800">System Status</h3>
        <div class="space-y-2">
          <div class="flex justify-between">
            <span>API Status:</span>
            <span :class="apiStatus.healthy ? 'text-green-600' : 'text-red-600'">
              {{ apiStatus.healthy ? 'Healthy' : 'Unhealthy' }}
            </span>
          </div>
          <div class="flex justify-between">
            <span>Vector DB:</span>
            <span :class="vectorDbStatus.healthy ? 'text-green-600' : 'text-red-600'">
              {{ vectorDbStatus.healthy ? 'Healthy' : 'Unhealthy' }}
            </span>
          </div>
          <div class="flex justify-between">
            <span>Knowledge Base:</span>
            <span class="text-blue-600">{{ knowledgeStats.total_documents || 0 }} docs</span>
          </div>
        </div>
      </div>

      <!-- Quick Actions Card -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold mb-4 text-gray-800">Quick Actions</h3>
        <div class="space-y-3">
          <button 
            @click="$router.push('/diagnostic')"
            class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition"
            :disabled="!isLicensedProfessional"
          >
            Diagnostic Assistant
          </button>
          <button 
            @click="$router.push('/treatment')"
            class="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 transition"
            :disabled="!isLicensedProfessional"
          >
            Treatment Planning
          </button>
          <button 
            @click="$router.push('/case-analysis')"
            class="w-full bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700 transition"
            :disabled="!isLicensedProfessional"
          >
            Case Analysis
          </button>
        </div>
      </div>

      <!-- Recent Activity Card -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold mb-4 text-gray-800">Recent Activity</h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span>Last Login:</span>
            <span class="text-gray-600">{{ formatDate(user?.last_login) }}</span>
          </div>
          <div class="flex justify-between">
            <span>Role:</span>
            <span class="text-blue-600">{{ user?.role }}</span>
          </div>
          <div class="flex justify-between">
            <span>License:</span>
            <span class="text-green-600">{{ user?.license_type || 'N/A' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Synthetic Cases Preview -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-lg font-semibold mb-4 text-gray-800">Available Test Cases</h3>
      <div v-if="syntheticCases.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div 
          v-for="case_ in syntheticCases.slice(0, 6)" 
          :key="case_.case_id"
          class="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
          @click="viewCase(case_)"
        >
          <h4 class="font-medium text-gray-800">{{ case_.case_id }}</h4>
          <p class="text-sm text-gray-600 mt-1">
            {{ case_.patient_demographics?.age }}y {{ case_.patient_demographics?.gender }}
          </p>
          <p class="text-sm text-blue-600 mt-1">
            {{ case_.suggested_diagnosis?.primary }}
          </p>
          <div class="mt-2 flex flex-wrap gap-1">
            <span 
              v-for="symptom in case_.presenting_symptoms?.slice(0, 2)" 
              :key="symptom"
              class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
            >
              {{ symptom.substring(0, 20) }}...
            </span>
          </div>
        </div>
      </div>
      <div v-else class="text-center text-gray-500 py-8">
        <p>No test cases available</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../services/api'
import type { User, SyntheticCase } from '../types'

const router = useRouter()

// Reactive state
const apiStatus = ref({ healthy: false })
const vectorDbStatus = ref({ healthy: false })
const knowledgeStats = ref({ total_documents: 0 })
const syntheticCases = ref<SyntheticCase[]>([])
const user = ref<User | null>(null)

// Computed properties
const isLicensedProfessional = computed(() => {
  return user.value?.role && ['therapist', 'psychiatrist', 'psychologist'].includes(user.value.role)
})

// Methods
const loadSystemStatus = async () => {
  try {
    const response = await apiClient.get('/health/services')
    apiStatus.value = response.data.services?.chromadb || { healthy: false }
    vectorDbStatus.value = response.data.services?.openai || { healthy: false }
    knowledgeStats.value = response.data.services?.chromadb?.stats || { total_documents: 0 }
  } catch (error) {
    console.error('Failed to load system status:', error)
  }
}

const loadSyntheticCases = async () => {
  try {
    const response = await apiClient.get('/api/v1/synthetic-cases')
    syntheticCases.value = response.data.cases || []
  } catch (error) {
    console.error('Failed to load synthetic cases:', error)
  }
}

const loadUserInfo = async () => {
  try {
    const response = await apiClient.get('/api/auth/me')
    user.value = response.data
  } catch (error) {
    console.error('Failed to load user info:', error)
  }
}

const viewCase = (case_: SyntheticCase) => {
  if (isLicensedProfessional.value) {
    router.push(`/case-analysis?caseId=${case_.case_id}`)
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleDateString()
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadSystemStatus(),
    loadSyntheticCases(),
    loadUserInfo()
  ])
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>