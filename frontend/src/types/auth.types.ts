export interface ApiKey {
  id: number;
  name: string;
  keyPrefix: string;
  isActive: boolean;
  createdAt: string;
  lastUsedAt?: string | null;
  permissions?: string[] | null;
}

export interface AuditLog {
  id: number;
  action: string;
  targetType: string;
  targetId?: number | null;
  details?: string | null;
  createdAt: string;
}

export interface Employee {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  qrToken?: string | null;
}

export interface UserDocument {
  id: number;
  filename: string;
  file_type: string;
  is_locked: boolean;
  created_at: string;
}

export interface Webhook {
  id: number;
  url: string;
  description?: string | null;
  isActive: boolean;
  events?: string[];
}

export interface WebAuthnCredential {
  id: string;
  type: string;
  transports?: string[];
}

export interface WebAuthnOptions {
  challenge: string;
  rpId?: string;
  allowCredentials?: WebAuthnCredential[];
  timeout?: number;
  userVerification?: 'required' | 'preferred' | 'discouraged';
}

export interface BiometricError {
  message: string;
  code?: string;
}

export interface OfficeLocation {
  latitude: number;
  longitude: number;
  radius: number;
  entryEnabled: boolean;
  exitEnabled: boolean;
}

export interface ActiveSession {
  id: string;
  user: { email: string };
  ipAddress?: string | null;
  userAgent?: string | null;
  expiresAt: string;
  lastUsedAt?: string | null;
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  
  if (typeof error === 'object' && error !== null) {
    const err = error as { 
      response?: { data?: { detail?: string | { message?: string } } }; 
      message?: string;
      graphQLErrors?: Array<{ message?: string }>;
      networkError?: { message?: string };
    };
    
    if (err.graphQLErrors && err.graphQLErrors.length > 0) {
      return err.graphQLErrors[0].message || 'Грешка от сървъра';
    }
    
    if (err.networkError) {
      return 'Няма връзка със сървъра';
    }
    
    if (err.response?.data?.detail) {
      if (typeof err.response.data.detail === 'string') return err.response.data.detail;
      if (err.response.data.detail.message) return err.response.data.detail.message;
    }
    if (err.message) return err.message;
  }
  
  return 'Неизвестна грешка';
}