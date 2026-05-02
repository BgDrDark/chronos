import { vi } from 'vitest';
/**
 * Comprehensive tests for EmploymentContractDialog component.
 * Tests contract creation form validation, submission, and error handling.
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MockedProvider } from '@apollo/client/testing';
import EmploymentContractDialog from '../EmploymentContractDialog';
import { CREATE_EMPLOYMENT_CONTRACT } from '../../graphql/contracts';
import type { LaborContract } from '../../types';

// Test data
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
  status: 'draft',
  signedAt: null,
  userId: null,
  company: { id: 1, name: 'Test Company' },
  annexes: []
};

const mockOnSuccess = vi.fn();
const mockOnClose = vi.fn();

const renderDialog = (
  mocks: readonly import('@apollo/client/testing').MockedResponse<unknown, unknown>[] = [],
  props: Partial<React.ComponentProps<typeof EmploymentContractDialog>> = {}
) => {
  return render(
    <MockedProvider mocks={mocks} addTypename={false}>
      <EmploymentContractDialog
        open={true}
        onClose={mockOnClose}
        companyId={1}
        onSuccess={mockOnSuccess}
        {...props}
      />
    </MockedProvider>
  );
};

describe('EmploymentContractDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    test('renders dialog with correct title for new contract', () => {
      renderDialog();
      expect(screen.getByText('Създаване на трудов договор')).toBeInTheDocument();
    });

    test('renders dialog with correct title for editing contract', () => {
      renderDialog([], { contract: mockContract });
      expect(screen.getByText('Редактиране на договор')).toBeInTheDocument();
    });

    test('renders all form fields', () => {
      renderDialog();
      
      expect(screen.getByLabelText(/име на служител/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/егн/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/номер на договор/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/тип договор/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/начална дата/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/крайна дата/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/работни часове/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/основна заплата/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/трудова характеристика/i)).toBeInTheDocument();
    });

    test('renders action buttons', () => {
      renderDialog();
      
      expect(screen.getByRole('button', { name: /отмени/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /създай/i })).toBeInTheDocument();
    });

    test('renders edit button when editing existing contract', () => {
      renderDialog([], { contract: mockContract });
      expect(screen.getByRole('button', { name: /запази/i })).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    test('shows validation error when employee name is empty', async () => {
      renderDialog();
      
      const submitButton = screen.getByRole('button', { name: /създай/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/име на служителя е задължително/i)).toBeInTheDocument();
      });
    });

    test('shows validation error when EGN is empty', async () => {
      renderDialog();
      
      const nameInput = screen.getByLabelText(/име на служител/i);
      await userEvent.type(nameInput, 'Тест Тестов');
      
      const submitButton = screen.getByRole('button', { name: /създай/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/егн е задължително/i)).toBeInTheDocument();
      });
    });

    test('shows validation error when start date is empty', async () => {
      renderDialog();
      
      const nameInput = screen.getByLabelText(/име на служител/i);
      const egnInput = screen.getByLabelText(/егн/i);
      
      await userEvent.type(nameInput, 'Тест Тестов');
      await userEvent.type(egnInput, '1234567890');
      
      const submitButton = screen.getByRole('button', { name: /създай/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/началната дата е задължителна/i)).toBeInTheDocument();
      });
    });

    test('clears validation error when user starts typing', async () => {
      renderDialog();
      
      const submitButton = screen.getByRole('button', { name: /създай/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/име на служителя е задължително/i)).toBeInTheDocument();
      });
      
      const nameInput = screen.getByLabelText(/име на служител/i);
      await userEvent.type(nameInput, 'Т');
      
      await waitFor(() => {
        expect(screen.queryByText(/име на служителя е задължително/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Input', () => {
    test('allows typing in employee name field', async () => {
      renderDialog();
      
      const nameInput = screen.getByLabelText(/име на служител/i) as HTMLInputElement;
      await userEvent.type(nameInput, 'Иван Иванов');
      
      expect(nameInput.value).toBe('Иван Иванов');
    });

    test('allows typing in EGN field', async () => {
      renderDialog();
      
      const egnInput = screen.getByLabelText(/егн/i) as HTMLInputElement;
      await userEvent.type(egnInput, '1234567890');
      
      expect(egnInput.value).toBe('1234567890');
    });

    test('limits EGN to 10 characters', async () => {
      renderDialog();
      
      const egnInput = screen.getByLabelText(/егн/i) as HTMLInputElement;
      await userEvent.type(egnInput, '123456789012345');
      
      expect(egnInput.value).toHaveLength(10);
    });

    test('allows selecting contract type', async () => {
      renderDialog();
      
      const select = screen.getByLabelText(/тип договор/i);
      await userEvent.click(select);
      
      const options = screen.getAllByRole('option');
      expect(options.length).toBeGreaterThan(0);
    });

    test('pre-fills form when editing existing contract', () => {
      renderDialog([], { contract: mockContract });
      
      const nameInput = screen.getByLabelText(/име на служител/i) as HTMLInputElement;
      const egnInput = screen.getByLabelText(/егн/i) as HTMLInputElement;
      
      expect(nameInput.value).toBe('Тест Тестов');
      expect(egnInput.value).toBe('1234567890');
    });
  });

  describe('Dialog Actions', () => {
    test('calls onClose when Cancel is clicked', async () => {
      renderDialog();
      
      const cancelButton = screen.getByRole('button', { name: /отмени/i });
      await userEvent.click(cancelButton);
      
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    test('closes dialog on successful submission', async () => {
      const mocks = [
        {
          request: {
            query: CREATE_EMPLOYMENT_CONTRACT,
            variables: {
              input: expect.objectContaining({
                employeeName: 'Нов Служител',
                employeeEgn: '1234567890',
                companyId: 1,
                contractType: 'full_time',
                startDate: '2024-01-15'
              })
            }
          },
          result: {
            data: {
              createEmploymentContract: {
                id: 1,
                employeeName: 'Нов Служител',
                status: 'draft'
              }
            }
          }
        }
      ];

      renderDialog(mocks);
      
      // Fill required fields
      await userEvent.type(screen.getByLabelText(/име на служител/i), 'Нов Служител');
      await userEvent.type(screen.getByLabelText(/егн/i), '1234567890');
      await userEvent.type(screen.getByLabelText(/начална дата/i), '2024-01-15');
      
      // Submit
      const submitButton = screen.getByRole('button', { name: /създай/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    test('submits form with valid data', async () => {
      const mocks = [
        {
          request: {
            query: CREATE_EMPLOYMENT_CONTRACT,
            variables: {
              input: expect.objectContaining({
                employeeName: 'Нов Служител',
                employeeEgn: '1234567890'
              })
            }
          },
          result: { data: { createEmploymentContract: { id: 1, employeeName: 'Нов Служител', status: 'draft' } } }
        }
      ];

      renderDialog(mocks);
      
      // Fill required fields
      await userEvent.type(screen.getByLabelText(/име на служител/i), 'Нов Служител');
      await userEvent.type(screen.getByLabelText(/егн/i), '1234567890');
      await userEvent.type(screen.getByLabelText(/начална дата/i), '2024-01-15');
      
      // Submit
      const submitButton = screen.getByRole('button', { name: /създай/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    });

    test('shows error message on API failure', async () => {
      const mocks = [
        {
          request: {
            query: CREATE_EMPLOYMENT_CONTRACT,
            variables: {
              input: expect.objectContaining({
                employeeName: 'Нов Служител',
                employeeEgn: '1234567890'
              })
            }
          },
          error: new Error('Грешка при създаване на договор')
        }
      ];

      renderDialog(mocks);
      
      // Fill required fields
      await userEvent.type(screen.getByLabelText(/име на служител/i), 'Нов Служител');
      await userEvent.type(screen.getByLabelText(/егн/i), '1234567890');
      await userEvent.type(screen.getByLabelText(/начална дата/i), '2024-01-15');
      
      const submitButton = screen.getByRole('button', { name: /създай/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/грешка при създаване на договор/i)).toBeInTheDocument();
      });
    });

    test('allows dismissing error message', async () => {
      const mocks = [
        {
          request: {
            query: CREATE_EMPLOYMENT_CONTRACT,
            variables: {}
          },
          error: new Error('API Error')
        }
      ];

      renderDialog(mocks);
      
      // Trigger error by submitting empty form
      const submitButton = screen.getByRole('button', { name: /създай/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      
      // Click close button on alert
      const closeButton = screen.getByRole('button', { name: /close/i });
      await userEvent.click(closeButton);
      
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Contract Type Options', () => {
    test('shows all contract type options', async () => {
      renderDialog();
      
      const select = screen.getByLabelText(/тип договор/i);
      await userEvent.click(select);
      
      expect(screen.getByText(/пълно работно време/i)).toBeInTheDocument();
      expect(screen.getByText(/непълно работно време/i)).toBeInTheDocument();
      expect(screen.getByText(/граждански договор/i)).toBeInTheDocument();
      expect(screen.getByText(/стажант/i)).toBeInTheDocument();
    });

    test('allows selecting different contract types', async () => {
      renderDialog();
      
      const select = screen.getByLabelText(/тип договор/i);
      await userEvent.click(select);
      
      // Select part-time
      await userEvent.selectOptions(select, 'part_time');
      
      const selectedOption = within(select).queryByRole('option', { selected: true }) || 
        select.querySelector('option:checked');
      expect(selectedOption?.textContent).toContain('Непълно');
    });
  });

  describe('Optional Fields', () => {
    test('allows filling optional contract number', async () => {
      renderDialog();
      
      const contractNumberInput = screen.getByLabelText(/номер на договор/i) as HTMLInputElement;
      await userEvent.type(contractNumberInput, 'TRZ-2024-001');
      
      expect(contractNumberInput.value).toBe('TRZ-2024-001');
    });

    test('allows filling optional end date', async () => {
      renderDialog();
      
      const endDateInput = screen.getByLabelText(/крайна дата/i) as HTMLInputElement;
      await userEvent.type(endDateInput, '2025-01-15');
      
      expect(endDateInput.value).toBe('2025-01-15');
    });

    test('allows filling optional base salary', async () => {
      renderDialog();
      
      const salaryInput = screen.getByLabelText(/основна заплата/i) as HTMLInputElement;
      await userEvent.type(salaryInput, '1500');
      
      expect(salaryInput.value).toBe('1500');
    });

    test('allows filling work hours per week', async () => {
      renderDialog();
      
      const hoursInput = screen.getByLabelText(/работни часове/i) as HTMLInputElement;
      await userEvent.clear(hoursInput);
      await userEvent.type(hoursInput, '32');
      
      expect(hoursInput.value).toBe('32');
    });

    test('allows filling job description', async () => {
      renderDialog();
      
      const descriptionInput = screen.getByLabelText(/трудова характеристика/i) as HTMLTextAreaElement;
      await userEvent.type(descriptionInput, 'Описание на длъжността и задълженията');
      
      expect(descriptionInput.value).toBe('Описание на длъжността и задълженията');
    });
  });

  describe('Form Reset', () => {
    test('resets form when dialog opens with no contract', () => {
      const { rerender } = render(
        <MockedProvider mocks={[]}>
          <EmploymentContractDialog
            open={false}
            onClose={mockOnClose}
            companyId={1}
            onSuccess={mockOnSuccess}
          />
        </MockedProvider>
      );
      
      // Fill some data while closed
      rerender(
        <MockedProvider mocks={[]}>
          <EmploymentContractDialog
            open={true}
            onClose={mockOnClose}
            companyId={1}
            onSuccess={mockOnSuccess}
          />
        </MockedProvider>
      );
      
      const nameInput = screen.getByLabelText(/име на служител/i) as HTMLInputElement;
      expect(nameInput.value).toBe('');
    });
  });
});
