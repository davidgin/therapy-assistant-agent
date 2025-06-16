<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Therapy Assistant Agent
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Sign in to your account
        </p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <div class="rounded-md shadow-sm -space-y-px">
          <div>
            <label for="username" class="sr-only">Email or Username</label>
            <input
              id="username"
              v-model="loginForm.username"
              name="username"
              type="text"
              required
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              placeholder="Email or Username"
            />
          </div>
          <div>
            <label for="password" class="sr-only">Password</label>
            <input
              id="password"
              v-model="loginForm.password"
              name="password"
              type="password"
              required
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              placeholder="Password"
            />
          </div>
        </div>

        <div v-if="error" class="text-red-600 text-sm text-center">
          {{ error }}
        </div>

        <div>
          <button
            type="submit"
            :disabled="loading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="loading">Signing in...</span>
            <span v-else>Sign in</span>
          </button>
        </div>

        <div class="text-center">
          <p class="text-sm text-gray-600">
            Don't have an account? 
            <router-link to="/register" class="font-medium text-indigo-600 hover:text-indigo-500">
              Register here
            </router-link>
          </p>
        </div>
      </form>

      <!-- Demo Login Section -->
      <div class="mt-8 border-t pt-6">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Demo Accounts</h3>
        <div class="space-y-2">
          <button
            @click="loginAsDemo('therapist')"
            class="w-full text-left px-4 py-2 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100 transition"
          >
            <div class="font-medium text-blue-900">Licensed Therapist</div>
            <div class="text-sm text-blue-700">Access all RAG features</div>
          </button>
          <button
            @click="loginAsDemo('student')"
            class="w-full text-left px-4 py-2 bg-green-50 border border-green-200 rounded hover:bg-green-100 transition"
          >
            <div class="font-medium text-green-900">Student</div>
            <div class="text-sm text-green-700">Limited access for learning</div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../services/api'
import type { LoginRequest } from '../types'

const router = useRouter()

// Reactive state
const loginForm = ref<LoginRequest>({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

// Methods
const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    error.value = 'Please enter both username and password'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.login(loginForm.value)
    
    // Store token and user info
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('user', JSON.stringify(response.user))
    localStorage.setItem('userRole', response.user.role)
    
    // Redirect to dashboard
    router.push('/')
    
  } catch (err: any) {
    console.error('Login error:', err)
    error.value = err.response?.data?.detail || 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}

const loginAsDemo = (role: 'therapist' | 'student') => {
  if (role === 'therapist') {
    loginForm.value = {
      username: 'demo.therapist@example.com',
      password: 'demo123'
    }
  } else {
    loginForm.value = {
      username: 'demo.student@example.com', 
      password: 'demo123'
    }
  }
  handleLogin()
}
</script>

<style scoped>
/* Additional custom styles if needed */
</style>