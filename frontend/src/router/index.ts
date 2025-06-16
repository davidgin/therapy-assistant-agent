import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../pages/Dashboard.vue'
import DiagnosticAssistant from '../pages/DiagnosticAssistant.vue'
import TreatmentPlanning from '../pages/TreatmentPlanning.vue'
import CaseAnalysis from '../pages/CaseAnalysis.vue'
import Login from '../pages/Login.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/diagnostic',
      name: 'DiagnosticAssistant',
      component: DiagnosticAssistant,
      meta: { requiresAuth: true, requiresLicense: true }
    },
    {
      path: '/treatment',
      name: 'TreatmentPlanning',
      component: TreatmentPlanning,
      meta: { requiresAuth: true, requiresLicense: true }
    },
    {
      path: '/case-analysis',
      name: 'CaseAnalysis',
      component: CaseAnalysis,
      meta: { requiresAuth: true, requiresLicense: true }
    }
  ]
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresLicense && userRole === 'student') {
    // Students can't access licensed professional features
    next('/')
  } else {
    next()
  }
})

export default router