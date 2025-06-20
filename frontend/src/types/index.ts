// Type definitions for the Therapy Assistant Agent

export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  license_type?: LicenseType;
  license_number?: string;
  license_state?: string;
  organization?: string;
  is_active: boolean;
  is_verified: boolean;
  last_login?: string;
  created_at: string;
}

export type UserRole = 'therapist' | 'psychiatrist' | 'psychologist' | 'student' | 'admin';

export type LicenseType = 'lmft' | 'lcsw' | 'lpc' | 'psyd' | 'md' | 'phd' | 'student' | 'other';

export interface PatientDemographics {
  age: number;
  gender: string;
  ethnicity?: string;
  occupation?: string;
  education_level?: string;
  marital_status?: string;
}

export interface SuggestedDiagnosis {
  primary: string;
  dsm5_code: string;
  icd11_code: string;
  confidence: number;
}

export interface SyntheticCase {
  case_id: string;
  patient_demographics: PatientDemographics;
  presenting_symptoms: string[];
  clinical_history: string;
  assessment_notes: string;
  suggested_diagnosis: SuggestedDiagnosis;
  treatment_recommendations: string[];
  severity: string;
  risk_factors: string[];
  protective_factors: string[];
}

export interface DiagnosticRequest {
  symptoms: string;
  patient_context?: string;
}

export interface TreatmentRequest {
  diagnosis: string;
  patient_context?: string;
}

export interface RAGResponse {
  status: string;
  ai_response: {
    status: string;
    response: string;
    model_used: string;
    retrieved_sources: number;
  };
  retrieved_documents: number;
  retrieved_sources: Array<{
    disorder?: string;
    code?: string;
    treatment?: string;
    evidence_level?: string;
    score: number;
  }>;
}

export interface KnowledgeSearchRequest {
  query: string;
  doc_type?: string;
  disorder?: string;
}

export interface KnowledgeDocument {
  text: string;
  type: string;
  disorder?: string;
  code?: string;
  icd11_code?: string;
  treatment?: string;
  evidence_level?: string;
  category?: string;
  source?: string;
}

export interface CaseAnalysisResponse {
  status: string;
  case_id: string;
  case_data: SyntheticCase;
  ai_analysis: {
    status: string;
    response: string;
    model_used: string;
    case_id: string;
    retrieved_sources: number;
  };
  knowledge_sources: Array<{
    type: string;
    disorder: string;
    score: number;
  }>;
  retrieved_documents: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegistrationRequest {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  license_type?: LicenseType;
  license_number?: string;
  license_state?: string;
  organization?: string;
}

export interface SystemStatus {
  services: {
    chromadb?: {
      status: string;
      stats?: {
        total_documents: number;
        collection_name: string;
        database_type: string;
        embedding_function: string;
        document_types?: Record<string, number>;
        disorders_covered?: number;
        disorder_list?: string[];
      };
    };
    openai?: {
      status: string;
      model: string;
    };
  };
}

export interface ApiError {
  detail: string;
  status_code?: number;
}