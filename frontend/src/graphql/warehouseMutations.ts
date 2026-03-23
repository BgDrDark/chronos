import { gql } from '@apollo/client';

export const CONSUME_FROM_BATCH = gql`
  mutation ConsumeFromBatch($batchId: Int!, $quantity: Decimal!, $reason: String!, $notes: String) {
    consumeFromBatch(batchId: $batchId, quantity: $quantity, reason: $reason, notes: $notes) {
      id
      quantity
      status
    }
  }
`;

export const AUTO_CONSUME_FEFO = gql`
  mutation AutoConsumeFefo($ingredientId: Int!, $quantity: Decimal!, $reason: String!, $notes: String) {
    autoConsumeFefo(ingredientId: $ingredientId, quantity: $quantity, reason: $reason, notes: $notes) {
      id
      quantity
      reason
      createdAt
    }
  }
`;

export const GET_FEFO_SUGGESTION = gql`
  query GetFefoSuggestion($ingredientId: Int!, $quantity: Decimal!) {
    getFefoSuggestion(ingredientId: $ingredientId, quantity: $quantity) {
      batchId
      batchNumber
      availableQuantity
      quantityToTake
      expiryDate
      daysUntilExpiry
    }
  }
`;

export const GET_CONSUMPTION_LOGS = gql`
  query GetConsumptionLogs($ingredientId: Int, $batchId: Int, $startDate: Date, $endDate: Date) {
    stockConsumptionLogs(ingredientId: $ingredientId, batchId: $batchId, startDate: $startDate, endDate: $endDate) {
      id
      quantity
      reason
      notes
      createdAt
      ingredient {
        id
        name
        unit
      }
      batch {
        id
        batchNumber
      }
      creator {
        id
        firstName
        lastName
      }
    }
  }
`;
