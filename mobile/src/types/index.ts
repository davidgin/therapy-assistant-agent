export interface User {
  id: string;
  email: string;
  name: string;
  is_licensed: boolean;
  license_number?: string;
  license_state?: string;
  created_at: string;
}

export interface DiagnosticRequest {
  symptoms: string;
  patient_context?: string;
}

export interface DiagnosticResponse {
  analysis: string;
  suggested_diagnoses: string[];
  confidence: number;
  recommendations: string[];
}

export interface TreatmentRequest {
  diagnosis: string;
  patient_context?: string;
}

export interface TreatmentResponse {
  treatment_plan: string;
  interventions: string[];
  goals: string[];
  timeline: string;
}

export interface ClinicalCase {
  case_id: string;
  patient_demographics: {
    age: number;
    gender: string;
    occupation?: string;
  };
  presenting_symptoms: string[];
  clinical_history: string;
  suggested_diagnosis: {
    primary: string;
    dsm5_code?: string;
    confidence: number;
  };
  severity: 'mild' | 'moderate' | 'severe';
  treatment_recommendations: string[];
}

export interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
}

export type RootStackParamList = {
  Login: undefined;
  Dashboard: undefined;
  Diagnostic: undefined;
  Treatment: undefined;
  Cases: undefined;
  Profile: undefined;
};

export type BottomTabParamList = {
  Dashboard: undefined;
  Diagnostic: undefined;
  Treatment: undefined;
  Cases: undefined;
  Profile: undefined;
};