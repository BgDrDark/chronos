export interface ProductionTask {
  id: number;
  recipeId?: number | null;
  quantity: number;
  unit?: string | null;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority?: number;
  notes?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt?: string;
  createdBy?: number | null;
}

export interface ProductionOrder {
  id: number;
  orderId?: number | null;
  recipeId: number;
  quantity: number;
  producedQuantity?: number;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  notes?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt?: string;
}

export interface TerminalOrder {
  id: number;
  terminalId?: number | null;
  orderNumber: string;
  customerName?: string | null;
  status: 'pending' | 'preparing' | 'ready' | 'completed' | 'cancelled';
  totalAmount: number;
  createdAt?: string;
  completedAt?: string | null;
}

export interface OrderItem {
  id?: number;
  recipeId: number;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  notes?: string | null;
}