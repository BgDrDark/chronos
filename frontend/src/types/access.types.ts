export interface AccessZone {
  id: number;
  name: string;
  description?: string | null;
  isActive?: boolean;
  createdAt?: string;
}

export interface AccessDoor {
  id: number;
  name: string;
  zoneId?: number | null;
  zone?: AccessZone | null;
  gatewayId?: number | null;
  gateway?: Gateway | null;
  isActive?: boolean;
  lastAccess?: string | null;
}

export interface AccessCode {
  id: number;
  userId?: number | null;
  user?: { firstName?: string; lastName?: string; employeeNumber?: string | null } | null;
  code: string;
  type: 'permanent' | 'temporary' | 'one_time';
  validFrom?: string | null;
  validUntil?: string | null;
  isActive?: boolean;
  usedCount?: number;
  maxUses?: number | null;
  createdAt?: string;
  createdBy?: number | null;
}

export interface AccessLog {
  id: number;
  userId?: number | null;
  user?: { firstName?: string; lastName?: string } | null;
  doorId?: number | null;
  door?: AccessDoor | null;
  zoneId?: number | null;
  zone?: AccessZone | null;
  accessType: 'code' | 'card' | 'biometric' | 'manual';
  success: boolean;
  timestamp: string;
  photoUrl?: string | null;
  notes?: string | null;
}

export interface Terminal {
  id: number;
  name: string;
  location?: string | null;
  type?: string;
  isActive?: boolean;
  lastPing?: string | null;
  lastOrderId?: number | null;
}

export interface Gateway {
  id: number;
  name: string;
  type: string;
  ipAddress?: string | null;
  port?: number | null;
  isConnected?: boolean;
  lastActivity?: string | null;
}