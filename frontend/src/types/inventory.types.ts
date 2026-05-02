export interface StorageZone {
  id: number;
  name: string;
  description?: string | null;
  tempMin?: number | null;
  tempMax?: number | null;
  isActive?: boolean | null;
  assetType?: string | null;
  zoneType?: string | null;
}

export interface Supplier {
  id: number;
  name: string;
  eik?: string | null;
  vatNumber?: string | null;
  address?: string | null;
  contactPerson?: string | null;
  email?: string | null;
  phone?: string | null;
}

export interface Ingredient {
  id: number;
  name: string;
  barcode?: string | null;
  unit: string;
  currentStock: number;
  baselineMinStock: number;
  isPerishable: boolean;
  expiryWarningDays: number;
  productType: string;
  currentPrice?: number | null;
  storageZone?: StorageZone | null;
  batches?: Batch[];
}

export interface Batch {
  id: number;
  ingredientId: number;
  supplierId?: number | null;
  quantity: number;
  originalQuantity: number;
  batchNumber?: string | null;
  invoiceNumber?: string | null;
  expiryDate?: string | null;
  receivedDate: string;
  cost?: number | null;
  status: string;
  storageZone?: StorageZone | null;
  storageZoneId?: number | null;
  ingredient?: Ingredient | null;
  supplier?: Supplier | null;
  availableStock?: number;
  isExpired?: boolean;
  daysUntilExpiry?: number;
}

export interface StockConsumptionLog {
  id: number;
  ingredientId: number;
  batchId: number;
  quantity: number;
  reason: string;
  productionOrderId?: number | null;
  notes?: string | null;
  createdBy: number;
  createdAt: string;
}

export interface FefoSuggestion {
  batchId: number;
  batchNumber: string;
  availableQuantity: number;
  quantityToTake: number;
  expiryDate: string;
  daysUntilExpiry: number;
}

export interface InventorySession {
  id: number;
  startedAt: string;
  completedAt?: string | null;
  status: 'active' | 'completed' | 'cancelled';
  protocolNumber?: string | null;
}

export interface InventorySessionItem {
  id: number;
  ingredientId: number;
  ingredientName: string;
  ingredientUnit: string;
  foundQuantity: number;
  systemQuantity: number;
  difference: number;
  adjusted: boolean;
}

export interface Recipe {
  id: number;
  name: string;
  defaultPieces?: number | null;
  category?: string | null;
}

export interface RecipeIngredient {
  id: number;
  ingredient: Ingredient;
  ingredientId?: number | string | null;
  quantityGross: number;
  quantityNet?: number | null;
  wastePercentage?: number | null;
  originalQuantity?: number | null;
  barcode?: string | null;
}

export interface RecipeStep {
  id: number;
  name: string;
  stepOrder: number;
  estimatedDurationMinutes?: number | null;
  workstationId?: number;
}

export interface RecipeSection {
  id: number;
  name: string;
  type?: string | null;
  sectionType?: string | null;
  shelfLifeDays?: number | null;
  wastePercentage: number;
  sectionOrder: number;
  ingredients: RecipeIngredient[];
  steps: RecipeStep[];
}

export interface FullRecipe extends Recipe {
  description?: string | null;
  isBase: boolean;
  yieldQuantity?: number | null;
  yieldUnit?: string | null;
  shelfLifeDays?: number | null;
  shelfLifeFrozenDays?: number | null;
  productionDeadlineDays?: number | null;
  instructions?: string | null;
  sections: RecipeSection[];
}

export interface RecipeWithPrice extends Recipe {
  sellingPrice: number | null;
  costPrice: number | null;
  markupPercentage: number | null;
  premiumAmount: number | null;
  portions: number | null;
  lastPriceUpdate: string | null;
  priceCalculatedAt: string | null;
  markupAmount: number | null;
  finalPrice: number | null;
  portionPrice: number | null;
  category?: string | null;
}

export interface PriceHistory {
  id: number;
  recipeId: number;
  oldPrice: number | null;
  newPrice: number | null;
  oldMarkup: number | null;
  newMarkup: number | null;
  oldPremium: number | null;
  newPremium: number | null;
  oldCost: number | null;
  newCost: number | null;
  reason: string | null;
  changedAt: string;
  user?: { id: number; firstName?: string | null; lastName?: string | null; email: string } | null;
}

export interface RecipeCostResult {
  recipeId: number;
  recipeName: string;
  costPrice: number;
  markupAmount: number;
  finalPrice: number;
  portionPrice: number;
}

export interface RecipePriceUpdateInput {
  recipeId: number;
  markupPercentage?: number | null;
  premiumAmount?: number | null;
  portions?: number | null;
  reason?: string | null;
}