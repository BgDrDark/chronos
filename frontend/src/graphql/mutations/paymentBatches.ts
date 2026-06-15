import { gql } from '@apollo/client';

export const CREATE_PAYMENT_BATCH = gql`
  mutation CreatePaymentBatch($input: CreatePaymentBatchInput!) {
    createPaymentBatch(input: $input) {
      id
      companyId
      periodStart
      periodEnd
      paymentDate
      totalAmount
      status
      paymentMethod
      paymentReference
      notes
      createdAt
      paidByUser {
        id
        fullName
      }
    }
  }
`;

export const ADD_ITEMS_TO_BATCH = gql`
  mutation AddItemsToBatch($input: AddItemsToBatchInput!) {
    addItemsToBatch(input: $input) {
      id
      totalAmount
      status
      items {
        id
        userId
        amount
        paidAt
        user {
          id
          fullName
        }
      }
    }
  }
`;

export const COMPLETE_PAYMENT_BATCH = gql`
  mutation CompletePaymentBatch($batchId: Int!) {
    completePaymentBatch(batchId: $batchId) {
      id
      status
      items {
        id
        paidAt
      }
    }
  }
`;

export const CANCEL_PAYMENT_BATCH = gql`
  mutation CancelPaymentBatch($batchId: Int!) {
    cancelPaymentBatch(batchId: $batchId) {
      id
      status
    }
  }
`;
