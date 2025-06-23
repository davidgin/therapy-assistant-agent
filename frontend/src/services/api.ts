import axios, { AxiosInstance } from 'axios';
import type { 
  LoginRequest, 
  LoginResponse, 
  RegistrationRequest, 
  User,
  DiagnosticRequest,
  TreatmentRequest,
  RAGResponse,
  KnowledgeSearchRequest,
  CaseAnalysisResponse,
  SystemStatus,
  SyntheticCase
} from '../types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post('/api/auth/login', {
      username: credentials.username,
      password: credentials.password
    });
    return response.data;
  }

  async register(userData: RegistrationRequest): Promise<User> {
    const response = await this.client.post('/api/auth/register', userData);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/api/auth/me');
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/api/auth/logout');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  // System health endpoints
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await this.client.get('/health/services');
    return response.data;
  }

  async getHealth(): Promise<{ status: string; message: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // RAG endpoints
  async getDiagnosticAssistance(request: DiagnosticRequest): Promise<RAGResponse> {
    const params = new URLSearchParams();
    params.append('symptoms', request.symptoms);
    if (request.patient_context) {
      params.append('patient_context', request.patient_context);
    }

    const response = await this.client.get(`/api/v1/rag/diagnose?${params}`);
    return response.data;
  }

  async getTreatmentRecommendations(request: TreatmentRequest): Promise<RAGResponse> {
    const params = new URLSearchParams();
    params.append('diagnosis', request.diagnosis);
    if (request.patient_context) {
      params.append('patient_context', request.patient_context);
    }

    const response = await this.client.get(`/api/v1/rag/treatment?${params}`);
    return response.data;
  }

  async getCaseAnalysis(caseId: string): Promise<CaseAnalysisResponse> {
    const response = await this.client.get(`/api/v1/rag/case-analysis/${caseId}`);
    return response.data;
  }

  async searchKnowledge(request: KnowledgeSearchRequest): Promise<any> {
    const params = new URLSearchParams();
    params.append('query', request.query);
    if (request.doc_type) {
      params.append('doc_type', request.doc_type);
    }
    if (request.disorder) {
      params.append('disorder', request.disorder);
    }

    const response = await this.client.get(`/api/v1/rag/search/knowledge?${params}`);
    return response.data;
  }

  // Data endpoints
  async getSyntheticCases(): Promise<{ status: string; total_cases: number; cases: SyntheticCase[] }> {
    const response = await this.client.get('/api/v1/synthetic-cases');
    return response.data;
  }

  async getDisordersList(): Promise<{ status: string; total_disorders: number; disorders: string[] }> {
    const response = await this.client.get('/api/v1/rag/knowledge/disorders');
    return response.data;
  }

  async getDocumentTypes(): Promise<{ status: string; document_types: Record<string, number> }> {
    const response = await this.client.get('/api/v1/rag/knowledge/types');
    return response.data;
  }

  // Generic HTTP methods
  async get(url: string, params?: any) {
    return this.client.get(url, { params });
  }

  async post(url: string, data?: any) {
    return this.client.post(url, data);
  }

  async put(url: string, data?: any) {
    return this.client.put(url, data);
  }

  async delete(url: string) {
    return this.client.delete(url);
  }
}

export const apiClient = new ApiClient();
export default apiClient;