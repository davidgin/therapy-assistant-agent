import axios, {AxiosInstance, AxiosResponse} from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  User,
  DiagnosticRequest,
  DiagnosticResponse,
  TreatmentRequest,
  TreatmentResponse,
  ClinicalCase,
} from '../types';

const API_BASE_URL = 'http://localhost:8000'; // Change this to your server URL

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.api.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    // Add response interceptor to handle auth errors
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await AsyncStorage.removeItem('auth_token');
          // You might want to redirect to login here
        }
        return Promise.reject(error);
      },
    );
  }

  // Authentication
  async login(email: string, password: string): Promise<{access_token: string; user: User}> {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response: AxiosResponse<{access_token: string; token_type: string}> = await this.api.post(
      '/auth/login',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    );

    // Store token
    await AsyncStorage.setItem('auth_token', response.data.access_token);

    // Get user info
    const userResponse: AxiosResponse<User> = await this.api.get('/auth/me');
    
    return {
      access_token: response.data.access_token,
      user: userResponse.data,
    };
  }

  async logout(): Promise<void> {
    await AsyncStorage.removeItem('auth_token');
  }

  async getCurrentUser(): Promise<User> {
    const response: AxiosResponse<User> = await this.api.get('/auth/me');
    return response.data;
  }

  // Diagnostic
  async submitDiagnostic(request: DiagnosticRequest): Promise<DiagnosticResponse> {
    const response: AxiosResponse<DiagnosticResponse> = await this.api.post('/diagnostic', request);
    return response.data;
  }

  // Treatment
  async submitTreatment(request: TreatmentRequest): Promise<TreatmentResponse> {
    const response: AxiosResponse<TreatmentResponse> = await this.api.post('/treatment', request);
    return response.data;
  }

  // Cases
  async getClinicalCases(): Promise<ClinicalCase[]> {
    const response: AxiosResponse<ClinicalCase[]> = await this.api.get('/cases');
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{status: string}> {
    const response: AxiosResponse<{status: string}> = await this.api.get('/health');
    return response.data;
  }

  // Voice and audio analysis
  async transcribeAudio(audioData: string): Promise<{transcription: string}> {
    const response: AxiosResponse<{transcription: string}> = await this.api.post('/voice/transcribe', {
      audio_data: audioData,
    });
    return response.data;
  }

  async analyzeVoice(audioData: string): Promise<{
    transcription: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    emotion: string;
    tone: 'calm' | 'anxious' | 'depressed' | 'agitated' | 'neutral';
    speechRate: number;
    pauseFrequency: number;
    confidence: number;
  }> {
    const response = await this.api.post('/voice/analyze', {
      audio_data: audioData,
    });
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;