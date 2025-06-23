import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginRequest, LoginResponse } from '../types';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (credentials: LoginRequest) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  isLicensedProfessional: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!user;
  const isLicensedProfessional = user ? 
    ['therapist', 'psychiatrist', 'psychologist'].includes(user.role) : false;

  useEffect(() => {
    // Check for existing token on mount
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setUser(parsedUser);
        
        // Verify token is still valid
        apiClient.getCurrentUser()
          .then((currentUser) => {
            setUser(currentUser);
            localStorage.setItem('user', JSON.stringify(currentUser));
          })
          .catch(() => {
            // Token invalid, clear storage
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
          });
      } catch (error) {
        // Invalid saved user data
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
      }
    }
    
    setLoading(false);
  }, []);

  const login = async (credentials: LoginRequest): Promise<boolean> => {
    try {
      setLoading(true);
      const response: LoginResponse = await apiClient.login(credentials);
      
      // Store token and user
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      setUser(response.user);
      
      toast.success(`Welcome back, ${response.user.first_name}!`);
      return true;
    } catch (error: any) {
      console.error('Login error:', error);
      let message = 'Login failed. Please try again.';
      
      // Safely extract error message
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          message = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          message = error.response.data.detail.map((err: any) => err.msg).join(', ');
        } else {
          message = 'Invalid credentials. Please check your email and password.';
        }
      }
      
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    toast.success('Logged out successfully');
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    isAuthenticated,
    isLicensedProfessional,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};