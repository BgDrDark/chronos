import { gql } from '@apollo/client';

export const GET_PAYMENT_BATCHES = gql`
  query PaymentBatches($companyId: Int, $status: String) {
    paymentBatches(companyId: $companyId, status: $status) {
      id
      companyId
      periodStart
      periodEnd
      paymentDate
      totalAmount
      status
      paymentMethod
      paymentReference
      createdAt
      paidByUser {
        id
        fullName
      }
      items {
        id
        userId
        amount
        user {
          id
          fullName
        }
      }
    }
  }
`;

export const GET_PAYMENT_BATCH = gql`
  query PaymentBatch($id: Int!) {
    paymentBatch(id: $id) {
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
      items {
        id
        payslipId
        userId
        amount
        paidAt
        user {
          id
          fullName
        }
        payslip {
          id
          totalAmount
          grossSalary
        }
      }
    }
  }
`;

export const GET_PAYMENT_STATISTICS = gql`
  query PaymentStatistics($companyId: Int!, $year: Int!, $month: Int) {
    paymentStatistics(companyId: $companyId, year: $year, month: $month) {
      totalBatches
      totalAmount
      totalEmployeesPaid
      averagePaymentPerEmployee
      byMethod
      byStatus
    }
  }
`;
