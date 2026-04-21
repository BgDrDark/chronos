import { gql } from '@apollo/client';

export const CREATE_INGREDIENT = gql`
  mutation CreateIngredient($input: IngredientInput!) {
    createIngredient(input: $input) {
      id
      name
      unit
    }
  }
`;

export const UPDATE_INGREDIENT = gql`
  mutation UpdateIngredient($input: IngredientInput!) {
    updateIngredient(input: $input) {
      id
      name
      unit
      barcode
      baselineMinStock
      currentStock
      storageZone {
        id
        name
      }
    }
  }
`;

export const ADD_BATCH = gql`
  mutation AddBatch($input: BatchInput!) {
    addBatch(input: $input) {
      id
      quantity
      expiryDate
    }
  }
`;

export const UPDATE_BATCH = gql`
  mutation UpdateBatch($input: BatchInput!) {
    updateBatch(input: $input) {
      id
      batchNumber
      quantity
      expiryDate
      invoiceNumber
      storageZoneId
      ingredientId
    }
  }
`;

export const CREATE_SUPPLIER = gql`
  mutation CreateSupplier($input: SupplierInput!) {
    createSupplier(input: $input) {
      id
      name
    }
  }
`;

export const UPDATE_SUPPLIER = gql`
  mutation UpdateSupplier($input: UpdateSupplierInput!) {
    updateSupplier(input: $input) {
      id
      name
      eik
      vatNumber
      address
      contactPerson
      phone
      email
    }
  }
`;

export const CREATE_STORAGE_ZONE = gql`
  mutation CreateStorageZone($input: StorageZoneInput!) {
    createStorageZone(input: $input) {
      id
      name
    }
  }
`;

export const UPDATE_STORAGE_ZONE = gql`
  mutation UpdateStorageZone($input: UpdateStorageZoneInput!) {
    updateStorageZone(input: $input) {
      id
      name
      tempMin
      tempMax
      description
      isActive
      assetType
      zoneType
    }
  }
`;

export const CREATE_RECIPE = gql`
  mutation CreateRecipe($input: RecipeInput!) {
    createRecipe(input: $input) {
      id
      name
    }
  }
`;

export const CREATE_WORKSTATION = gql`
  mutation CreateWorkstation($name: String!, $description: String, $companyId: Int!) {
    createWorkstation(name: $name, description: $description, companyId: $companyId) {
      id
      name
    }
  }
`;

export const DELETE_RECIPE = gql`
  mutation DeleteRecipe($recipeId: Int!) {
    deleteRecipe(id: $recipeId)
  }
`;

export const CREATE_PRODUCTION_ORDER = gql`
  mutation CreateProductionOrder($input: ProductionOrderInput!) {
    createProductionOrder(input: $input) {
      id
      status
      dueDate
    }
  }
`;

export const UPDATE_TASK_STATUS = gql`
  mutation UpdateTaskStatus($id: Int!, $status: String!) {
    updateProductionTaskStatus(id: $id, status: $status) {
      id
      status
      startedAt
      completedAt
    }
  }
`;

export const SCRAP_TASK = gql`
  mutation ScrapTask($input: ScrapTaskInput!) {
    scrapTask(input: $input) {
      id
      status
    }
  }
`;

export const GET_SCRAP_LOGS = gql`
  query GetScrapLogs($taskId: Int!) {
    scrapLogs(taskId: $taskId) {
      id
      quantity
      reason
      createdAt
      userId
    }
  }
`;

export const UPDATE_PRODUCTION_ORDER_STATUS = gql`
  mutation UpdateProductionOrderStatus($id: Int!, $status: String!) {
    updateProductionOrderStatus(id: $id, status: $status) {
      id
      status
    }
  }
`;

export const CONFIRM_PRODUCTION_ORDER = gql`
  mutation ConfirmProductionOrder($id: Int!) {
    confirmProductionOrder(id: $id) {
      id
      status
      confirmedAt
      confirmedBy
    }
  }
`;

export const MARK_TASK_SCRAP = gql`
  mutation MarkTaskScrap($id: Int!) {
    markTaskScrap(id: $id) {
      id
      status
      isScrap
    }
  }
`;

export const START_INVENTORY_SESSION = gql`
  mutation StartInventorySession {
    startInventorySession {
      id
      status
      startedAt
    }
  }
`;

export const ADD_INVENTORY_ITEM = gql`
  mutation AddInventoryItem($sessionId: Int!, $ingredientId: Int!, $foundQuantity: Float!) {
    addInventoryItem(sessionId: $sessionId, ingredientId: $ingredientId, foundQuantity: $foundQuantity) {
      id
      ingredientId
      ingredientName
      foundQuantity
      systemQuantity
      difference
    }
  }
`;

export const COMPLETE_INVENTORY_SESSION = gql`
  mutation CompleteInventorySession($sessionId: Int!) {
    completeInventorySession(sessionId: $sessionId) {
      id
      status
      protocolNumber
      completedAt
    }
  }
`;

export const UPDATE_BATCH_STATUS = gql`
  mutation UpdateBatchStatus($id: Int!, $status: String!) {
    updateBatchStatus(id: $id, status: $status) {
      id
      status
    }
  }
`;

export const CREATE_INVOICE_FROM_BATCH = gql`
  mutation CreateInvoiceFromBatch($batchId: Int!) {
    createInvoiceFromBatch(batchId: $batchId) {
      id
      number
      total
    }
  }
`;

export const BULK_ADD_BATCHES = gql`
  mutation BulkAddBatches($invoiceNumber: String!, $supplierId: Int!, $date: Date!, $items: [BatchInput!]!, $createInvoice: Boolean!) {
    bulkAddBatches(invoiceNumber: $invoiceNumber, supplierId: $supplierId, date: $date, items: $items, createInvoice: $createInvoice) {
      id
      batchNumber
      quantity
      ingredient {
        id
        name
      }
    }
  }
`;

export const UPDATE_RECIPE_PRICE = gql`
  mutation UpdateRecipePrice($recipeId: Int!, $input: RecipePriceUpdateInput!) {
    updateRecipePrice(recipeId: $recipeId, input: $input) {
      id
      sellingPrice
      costPrice
      markupPercentage
      premiumAmount
      markupAmount
      finalPrice
      portionPrice
    }
  }
`;

export const CALCULATE_RECIPE_COST = gql`
  mutation CalculateRecipeCost($recipeId: Int!) {
    calculateRecipeCost(recipeId: $recipeId) {
      recipeId
      recipeName
      costPrice
      markupAmount
      finalPrice
      portionPrice
    }
  }
`;

export const RECALCULATE_ALL_RECIPE_COSTS = gql`
  mutation RecalculateAllRecipeCosts {
    recalculateAllRecipeCosts {
      recipeId
      recipeName
      costPrice
      markupAmount
      finalPrice
      portionPrice
    }
  }
`;

export const GET_RECIPES_WITH_PRICES = gql`
  query GetRecipesWithPrices {
    recipesWithPrices {
      id
      name
      category
      defaultPieces
      sellingPrice
      costPrice
      markupPercentage
      premiumAmount
      portions
      lastPriceUpdate
      priceCalculatedAt
      markupAmount
      finalPrice
      portionPrice
    }
  }
`;

export const GET_PRICE_HISTORY = gql`
  query GetPriceHistory($recipeId: Int!) {
    priceHistory(recipeId: $recipeId) {
      id
      recipeId
      oldPrice
      newPrice
      oldMarkup
      newMarkup
      oldPremium
      newPremium
      oldCost
      newCost
      reason
      changedAt
      user {
        id
        firstName
        lastName
        email
      }
    }
  }
`;
