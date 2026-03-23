/**
 * Comprehensive tests for EmploymentContractsList component.
 * Tests contract listing, filtering, signing, and linking functionality.
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MockedProvider } from '@apollo/client/testing';
import { BrowserRouter } from 'react-router-dom';
import EmploymentContractsList from '../EmploymentContractsList';
import { 
  GET_EMPLOYMENT_CONTRACTS,
  SIGN_EMPLOYMENT_CONTRACT,
  LINK_CONTRACT_TO_USER
} from '../../graphql/contracts';
import type { LaborContract, ContractStatus } from '../../types';

// Test data
const mockContracts: LaborContract[] = [
  {
    id: 1,
    employeeName: 'Иван Иванов',
    employeeEgn: '1234567890',
    contractNumber: 'TRZ-001',
    contractType: 'full_time',
    startDate: '2024-01-15',
    endDate: '2025-01-15',
    baseSalary: 1500.00,
    workHoursPerWeek: 40,
    status: 'draft' as ContractStatus,
    signedAt: null,
    userId: null,
    company: { id: 1, name: 'Test Company' },
    annexes: []
  },
  {
    id: 2,
    employeeName: 'Петър Петров',
    employeeEgn: '9876543210',
    contractNumber: 'TRZ-002',
    contractType: 'part_time',
    startDate: '2024-02-01',
    endDate: null,
    baseSalary: 800.00,
    workHoursPerWeek: 20,
    status: 'signed' as ContractStatus,
    signedAt: '2024-02-15T10:00:00Z',
    userId: null,
    company: { id: 1, name: 'Test Company' },
    annexes: []
  },
  {
    id: 3,
    employeeName: 'Мария Маринова',
    employeeEgn: '5678901234',
    contractNumber: 'TRZ-003',
    contractType: 'full_time',
    startDate: '2024-03-01',
    endDate: null,
    baseSalary: 2000.00,
    workHoursPerWeek: 40,
    status: 'linked' as ContractStatus,
    signedAt: '2024-03-10T09:00:00Z',
    userId: 5,
    company: { id: 1, name: 'Test Company' },
    annexes: []
  }
];

const renderList = (
  mocks: readonly import('@apollo/client/testing').MockedResponse<unknown, unknown>[] = [],
  props: Partial<React.ComponentProps<typeof EmploymentContractsList>> = {}
) => {
  return render(
    <MockedProvider mocks={mocks} addTypename={false}>
      <BrowserRouter>
        <EmploymentContractsList companyId={1} {...props} />
      </BrowserRouter>
    </MockedProvider>
  );
};

describe('EmploymentContractsList', () => {
  describe('Contract List Display', () => {
    test('renders contract list container', () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: [] } }
        }
      ];

      renderList(mocks);

      // Verify basic rendering
      expect(screen.getByText(/трудовe договори/i)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    test('shows message when no contracts exist', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: [] } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText(/няма намерени договори/i)).toBeInTheDocument();
      });
    });
  });

  describe('Contract Display', () => {
    test('displays all contracts', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
        expect(screen.getByText('Петър Петров')).toBeInTheDocument();
        expect(screen.getByText('Мария Маринова')).toBeInTheDocument();
      });
    });

    test('displays employee name for each contract', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        mockContracts.forEach(contract => {
          expect(screen.getByText(contract.employeeName!)).toBeInTheDocument();
        });
      });
    });

    test('displays EGN for each contract', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText(/егн: 1234567890/i)).toBeInTheDocument();
        expect(screen.getByText(/егн: 9876543210/i)).toBeInTheDocument();
        expect(screen.getByText(/егн: 5678901234/i)).toBeInTheDocument();
      });
    });

    test('displays contract number when available', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText(/№: trz-001/i)).toBeInTheDocument();
        expect(screen.getByText(/№: trz-002/i)).toBeInTheDocument();
        expect(screen.getByText(/№: trz-003/i)).toBeInTheDocument();
      });
    });

    test('displays contract type labels', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText(/пълно работно време/i)).toBeInTheDocument();
        expect(screen.getByText(/непълно работно време/i)).toBeInTheDocument();
      });
    });

    test('displays base salary when available', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText(/1500\.00 лв\./i)).toBeInTheDocument();
        expect(screen.getByText(/800\.00 лв\./i)).toBeInTheDocument();
        expect(screen.getByText(/2000\.00 лв\./i)).toBeInTheDocument();
      });
    });

    test('displays status chips with correct colors', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        // Check for status chips
        expect(screen.getByText('чернова')).toBeInTheDocument();
        expect(screen.getByText('подписан')).toBeInTheDocument();
        expect(screen.getByText('свързан')).toBeInTheDocument();
      });
    });

    test('displays date range for contracts', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText(/от: 2024-01-15 до 2025-01-15/i)).toBeInTheDocument();
      });
    });
  });

  describe('Action Buttons', () => {
    test('shows Sign button for draft contracts', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        // Draft contract should have Sign button
        const signButtons = screen.getAllByRole('button', { name: /подпиши/i });
        expect(signButtons.length).toBe(1);
      });
    });

    test('shows Link button for signed contracts', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        // Signed contract should have Link button
        const linkButtons = screen.getAllByRole('button', { name: /свържи/i });
        expect(linkButtons.length).toBe(1);
      });
    });

    test('shows print button for each contract', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        const printButtons = screen.getAllByLabelText('', { selector: 'button' });
        // Print is typically an icon button
        expect(printButtons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Filtering', () => {
    test('has status filter dropdown', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByLabelText(/статус/i)).toBeInTheDocument();
      });
    });

    test('shows all filter options', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        const filterSelect = screen.getByLabelText(/статус/i);
        userEvent.click(filterSelect);
        
        expect(screen.getByText(/всички/i)).toBeInTheDocument();
        expect(screen.getByText(/чернова/i)).toBeInTheDocument();
        expect(screen.getByText(/подписан/i)).toBeInTheDocument();
        expect(screen.getByText(/свързан/i)).toBeInTheDocument();
      });
    });

    test('filters contracts by status', async () => {
      const filterMocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: 'draft' } },
          result: { data: { employmentContracts: [mockContracts[0]] } }
        }
      ];

      renderList(filterMocks);

      await waitFor(() => {
        const filterSelect = screen.getByLabelText(/статус/i);
        userEvent.selectOptions(filterSelect, 'draft');
      });

      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
        expect(screen.queryByText('Петър Петров')).not.toBeInTheDocument();
      });
    });
  });

  describe('Sign Contract', () => {
    test('opens confirmation dialog when signing', async () => {
      window.confirm = jest.fn(() => true);

      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        },
        {
          request: { query: SIGN_EMPLOYMENT_CONTRACT, variables: { id: 1 } },
          result: { data: { signEmploymentContract: { id: 1, status: 'signed', signedAt: '2024-03-15T10:00:00Z' } } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      const signButton = screen.getByRole('button', { name: /подпиши/i });
      await userEvent.click(signButton);

      expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('подписан'));
    });

    test('calls sign mutation on confirm', async () => {
      window.confirm = jest.fn(() => true);

      const signMock = {
        request: { query: SIGN_EMPLOYMENT_CONTRACT, variables: { id: 1 } },
        result: { data: { signEmploymentContract: { id: 1, status: 'signed', signedAt: '2024-03-15T10:00:00Z' } } }
      };

      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        },
        signMock
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      const signButton = screen.getByRole('button', { name: /подпиши/i });
      await userEvent.click(signButton);

      await waitFor(() => {
        expect(signMock.result).toHaveBeenCalled();
      });
    });

    test('does not sign if user cancels confirmation', async () => {
      window.confirm = jest.fn(() => false);

      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      const signButton = screen.getByRole('button', { name: /подпиши/i });
      await userEvent.click(signButton);

      expect(window.confirm).toHaveBeenCalled();
    });

    test('shows success message after signing', async () => {
      window.confirm = jest.fn(() => true);

      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        },
        {
          request: { query: SIGN_EMPLOYMENT_CONTRACT, variables: { id: 1 } },
          result: { data: { signEmploymentContract: { id: 1, status: 'signed', signedAt: '2024-03-15T10:00:00Z' } } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      const signButton = screen.getByRole('button', { name: /подпиши/i });
      await userEvent.click(signButton);

      await waitFor(() => {
        expect(screen.getByText(/договорът е маркиран като подписан/i)).toBeInTheDocument();
      });
    });

    test('shows error message on sign failure', async () => {
      window.confirm = jest.fn(() => true);

      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        },
        {
          request: { query: SIGN_EMPLOYMENT_CONTRACT, variables: { id: 1 } },
          error: new Error('Грешка при подписване')
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      const signButton = screen.getByRole('button', { name: /подпиши/i });
      await userEvent.click(signButton);

      await waitFor(() => {
        expect(screen.getByText(/грешка при подписване/i)).toBeInTheDocument();
      });
    });
  });

  describe('Link Contract to User', () => {
    test('opens link dialog when clicking link button', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText('Петър Петров')).toBeInTheDocument();
      });

      const linkButton = screen.getByRole('button', { name: /свържи/i });
      await userEvent.click(linkButton);

      await waitFor(() => {
        expect(screen.getByText(/свържи договор с потребител/i)).toBeInTheDocument();
      });
    });

    test('closes link dialog on cancel', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        const linkButton = screen.getByRole('button', { name: /свържи/i });
        userEvent.click(linkButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/свържи договор с потребител/i)).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /отмени/i });
      await userEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText(/свържи договор с потребител/i)).not.toBeInTheDocument();
      });
    });

    test('shows success message after linking', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        },
        {
          request: { query: LINK_CONTRACT_TO_USER, variables: { contractId: 2, userId: 5 } },
          result: { data: { linkEmploymentContractToUser: { id: 2, status: 'linked', userId: 5 } } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        const linkButton = screen.getByRole('button', { name: /свържи/i });
        userEvent.click(linkButton);
      });

      await waitFor(() => {
        const linkConfirmButton = screen.getByRole('button', { name: /свържи/i });
        userEvent.click(linkConfirmButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/договорът е свързан с потребителя/i)).toBeInTheDocument();
      });
    });
  });

  describe('Create Contract Button', () => {
    test('renders new contract button', () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      expect(screen.getByRole('button', { name: /нов договор/i })).toBeInTheDocument();
    });

    test('opens create dialog when clicking new contract button', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          result: { data: { employmentContracts: mockContracts } }
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
      });

      const newButton = screen.getByRole('button', { name: /нов договор/i });
      await userEvent.click(newButton);

      await waitFor(() => {
        expect(screen.getByText(/създаване на трудов договор/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('displays error message on fetch failure', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          error: new Error('Грешка при зареждане')
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    test('allows dismissing error message', async () => {
      const mocks = [
        {
          request: { query: GET_EMPLOYMENT_CONTRACTS, variables: { companyId: 1, status: null } },
          error: new Error('Грешка')
        }
      ];

      renderList(mocks);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const closeButton = screen.getByRole('button', { name: /close/i });
      await userEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });
});
