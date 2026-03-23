import { gql } from '@apollo/client';

export const GET_EMPLOYMENT_CONTRACTS = gql`
  query GetEmploymentContracts($companyId: Int, $status: String) {
    employmentContracts(companyId: $companyId, status: $status) {
      id
      employeeName
      employeeEgn
      contractNumber
      contractType
      startDate
      endDate
      baseSalary
      workHoursPerWeek
      status
      signedAt
      userId
      company {
        id
        name
      }
      department {
        id
        name
      }
      position {
        id
        title
      }
      annexes {
        id
        annexNumber
        effectiveDate
        baseSalary
        changeType
        changeDescription
        status
        isSigned
      }
    }
  }
`;

export const GET_ORG_DATA_FOR_CONTRACT = gql`
  query GetOrgDataForContract {
    companies {
      id
      name
    }
    departments {
      id
      name
      companyId
    }
    positions {
      id
      title
      departmentId
    }
  }
`;

export const CREATE_EMPLOYMENT_CONTRACT = gql`
  mutation CreateEmploymentContract($input: EmploymentContractCreateInput!) {
    createEmploymentContract(input: $input) {
      id
      employeeName
      status
    }
  }
`;

export const SIGN_EMPLOYMENT_CONTRACT = gql`
  mutation SignEmploymentContract($id: Int!) {
    signEmploymentContract(id: $id) {
      id
      status
      signedAt
    }
  }
`;

export const LINK_CONTRACT_TO_USER = gql`
  mutation LinkContractToUser($contractId: Int!, $userId: Int!) {
    linkEmploymentContractToUser(contractId: $contractId, userId: $userId) {
      id
      status
      userId
    }
  }
`;

export const GET_USERS_FOR_LINK = gql`
  query GetUsersForLink {
    users(limit: 1000) {
      users {
        id
        firstName
        lastName
        email
      }
    }
  }
`;

export const GENERATE_CONTRACT_NUMBER = gql`
  mutation GenerateContractNumber($companyId: Int!) {
    generateContractNumber(companyId: $companyId)
  }
`;

export const GET_CONTRACT_PDF_URL = gql`
  mutation GetContractPdfUrl($contractId: Int!) {
    getContractPdfUrl(contractId: $contractId)
  }
`;

export const GET_ANNEX_PDF_URL = gql`
  mutation GetAnnexPdfUrl($annexId: Int!) {
    getAnnexPdfUrl(annexId: $annexId)
  }
`;
