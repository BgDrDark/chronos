import { gql } from '@apollo/client';

export const GET_MY_PAYMENT_HISTORY = gql`
  query MyPaymentHistory($year: Int) {
    myPaymentHistory(year: $year) {
      id
      amount
      paidAt
      payslip {
        id
        totalAmount
        grossSalary
        periodStart
        periodEnd
        regularAmount
        overtimeAmount
        bonusAmount
        taxAmount
        insuranceAmount
      }
    }
  }
`;
