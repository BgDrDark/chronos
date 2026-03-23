/**
 * Comprehensive tests for ContractDossier component.
 * Tests user contract display with annex history.
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { MockedProvider } from '@apollo/client/testing';
import { gql } from '@apollo/client';
import ContractDossier from '../ContractDossier';
import type { LaborContract, LaborContractAnnex, ContractStatus } from '../../types';

// GraphQL query used by ContractDossier
const GET_EMPLOYMENT_CONTRACT = gql`
  query GetEmploymentContract($userId: Int!) {
    employmentContracts(userId: $userId) {
      id
      employeeName
      employeeEgn
      contractNumber
      contractType
      startDate
      endDate
      baseSalary
      status
      signedAt
      userId
      company {
        id
        name
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

// Test data
const mockAnnexes: LaborContractAnnex[] = [
  {
    id: 1,
    annexNumber: 'А-001',
    effectiveDate: '2024-04-01',
    baseSalary: 2000.00,
    changeType: 'salary_increase',
    changeDescription: 'Годишно повишение',
    status: 'signed' as ContractStatus,
    isSigned: true,
    signedAt: '2024-04-05T10:00:00Z',
    signedByEmployee: true,
    signedByEmployer: true,
    createdAt: '2024-03-25'
  },
  {
    id: 2,
    annexNumber: 'А-002',
    effectiveDate: '2024-07-01',
    baseSalary: 2200.00,
    changeType: 'salary_increase',
    changeDescription: null,
    status: 'signed' as ContractStatus,
    isSigned: true,
    signedAt: '2024-07-01T09:00:00Z',
    signedByEmployee: true,
    signedByEmployer: true,
    createdAt: '2024-06-20'
  }
];

const mockContract: LaborContract = {
  id: 1,
  employeeName: 'Тест Тестов',
  employeeEgn: '1234567890',
  contractNumber: 'TRZ-001',
  contractType: 'full_time',
  startDate: '2024-01-15',
  endDate: '2025-01-15',
  baseSalary: 1500.00,
  workHoursPerWeek: 40,
  status: 'linked' as ContractStatus,
  signedAt: '2024-01-10T10:00:00Z',
  userId: 5,
  company: { id: 1, name: 'Test Company' },
  annexes: mockAnnexes
};

// Helper function to create mocks
const createMock = (userId: number, contracts: LaborContract[]) => ({
  request: {
    query: GET_EMPLOYMENT_CONTRACT,
    variables: { userId }
  },
  result: { data: { employmentContracts: contracts } }
});

const renderDossier = (
  mocks: readonly import('@apollo/client/testing').MockedResponse<unknown, unknown>[] = [],
  userId: number = 5
) => {
  return render(
    <MockedProvider mocks={mocks} addTypename={false}>
      <ContractDossier userId={userId} />
    </MockedProvider>
  );
};

describe('ContractDossier', () => {
  describe('Loading State', () => {
    test('shows loading indicator while fetching', async () => {
      const mocks = [createMock(5, [])];
      renderDossier(mocks);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Contract Display', () => {
    test('displays contract header', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/трудов договор/i)).toBeInTheDocument();
      });
    });

    test('displays employee name', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText('Тест Тестов')).toBeInTheDocument();
      });
    });

    test('displays employee EGN', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText('1234567890')).toBeInTheDocument();
      });
    });

    test('displays contract number', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText('TRZ-001')).toBeInTheDocument();
      });
    });

    test('displays contract type with label', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/пълно работно време/i)).toBeInTheDocument();
      });
    });

    test('displays contract period', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/2024-01-15 - 2025-01-15/i)).toBeInTheDocument();
      });
    });

    test('displays base salary', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/1500\.00 лв\./i)).toBeInTheDocument();
      });
    });

    test('displays status chip', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText('свързан')).toBeInTheDocument();
      });
    });
  });

  describe('Annex History', () => {
    test('displays annex history header', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/история на анексите/i)).toBeInTheDocument();
      });
    });

    test('displays all annexes', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/а-001/i)).toBeInTheDocument();
        expect(screen.getByText(/а-002/i)).toBeInTheDocument();
      });
    });

    test('displays annex salary changes', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/заплата: 2000\.00 лв\./i)).toBeInTheDocument();
        expect(screen.getByText(/заплата: 2200\.00 лв\./i)).toBeInTheDocument();
      });
    });

    test('displays signed indicator for signed annexes', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getAllByText(/подписан/i)).toHaveLength(2);
      });
    });
  });

  describe('Empty State', () => {
    test('shows message when no contract exists', async () => {
      const mocks = [createMock(999, [])];
      renderDossier(mocks, 999);

      await waitFor(() => {
        expect(screen.getByText(/няма намерен трудов договор/i)).toBeInTheDocument();
      });
    });

    test('does not show annex history when no annexes', async () => {
      const contractWithoutAnnexes: LaborContract = {
        ...mockContract,
        annexes: []
      };

      const mocks = [createMock(5, [contractWithoutAnnexes])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText('Тест Тестов')).toBeInTheDocument();
      });

      expect(screen.queryByText(/история на анексите/i)).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('shows error message on fetch failure', async () => {
      const mocks = [{
        request: {
          query: GET_EMPLOYMENT_CONTRACT,
          variables: { userId: 5 }
        },
        error: new Error('Грешка при зареждане')
      }];
      
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByText(/грешка при зареждане на договора/i)).toBeInTheDocument();
      });
    });
  });

  describe('Contract Type Labels', () => {
    test('displays correct label for full_time', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/пълно работно време/i)).toBeInTheDocument();
      });
    });

    test('displays correct label for part_time', async () => {
      const partTimeContract: LaborContract = {
        ...mockContract,
        contractType: 'part_time'
      };

      const mocks = [createMock(5, [partTimeContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/непълно работно време/i)).toBeInTheDocument();
      });
    });

    test('displays correct label for contractor', async () => {
      const contractorContract: LaborContract = {
        ...mockContract,
        contractType: 'contractor'
      };

      const mocks = [createMock(5, [contractorContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/граждански договор/i)).toBeInTheDocument();
      });
    });

    test('displays correct label for internship', async () => {
      const internshipContract: LaborContract = {
        ...mockContract,
        contractType: 'internship'
      };

      const mocks = [createMock(5, [internshipContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/стажант/i)).toBeInTheDocument();
      });
    });
  });

  describe('Status Labels', () => {
    test('displays correct label for draft status', async () => {
      const draftContract: LaborContract = {
        ...mockContract,
        status: 'draft' as ContractStatus
      };

      const mocks = [createMock(5, [draftContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText('чернова')).toBeInTheDocument();
      });
    });

    test('displays correct label for signed status', async () => {
      const signedContract: LaborContract = {
        ...mockContract,
        status: 'signed' as ContractStatus
      };

      const mocks = [createMock(5, [signedContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText('подписан')).toBeInTheDocument();
      });
    });

    test('displays correct label for linked status', async () => {
      const mocks = [createMock(5, [mockContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText('свързан')).toBeInTheDocument();
      });
    });
  });

  describe('Fallback Values', () => {
    test('displays dash for missing employee name', async () => {
      const contractWithoutName: LaborContract = {
        ...mockContract,
        employeeName: null
      };

      const mocks = [createMock(5, [contractWithoutName])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getAllByText('—')).toHaveLength(1);
      });
    });

    test('hides end date when not set', async () => {
      const contractWithoutEndDate: LaborContract = {
        ...mockContract,
        endDate: null
      };

      const mocks = [createMock(5, [contractWithoutEndDate])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.getByText(/2024-01-15/i)).toBeInTheDocument();
        expect(screen.queryByText(/2025-01-15/i)).not.toBeInTheDocument();
      });
    });

    test('hides signed date when not set', async () => {
      const unsignedContract: LaborContract = {
        ...mockContract,
        signedAt: null
      };

      const mocks = [createMock(5, [unsignedContract])];
      renderDossier(mocks);

      await waitFor(() => {
        expect(screen.queryByText(/дата на подписване/i)).not.toBeInTheDocument();
      });
    });
  });
});
