import React from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Chip,
  CircularProgress, Alert, Divider
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ScheduleIcon from '@mui/icons-material/Schedule';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import { type LaborContract, type LaborContractAnnex, type ContractStatus } from '../types';
import { useCurrency, formatCurrencyValue } from '../currencyContext';
import { formatDate } from '../utils/dateUtils';

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

interface ContractDossierProps {
  userId: number;
  isReadOnly?: boolean;
}

const CONTRACT_TYPE_LABELS: Record<string, string> = {
  full_time: 'Пълно работно време',
  part_time: 'Непълно работно време',
  contractor: 'Граждански договор',
  internship: 'Стажант'
};

const STATUS_LABELS: Record<ContractStatus, { label: string; color: 'warning' | 'success' | 'info' }> = {
  draft: { label: 'Чернова', color: 'warning' },
  signed: { label: 'Подписан', color: 'success' },
  linked: { label: 'Свързан', color: 'info' }
};

const CHANGE_TYPE_LABELS: Record<string, string> = {
  salary_increase: 'Повишение на заплатата',
  salary_decrease: 'Намаление на заплатата',
  position_change: 'Промяна на длъжност',
  hours_change: 'Промяна на работно време',
  other: 'Друга промяна'
};

interface EmploymentContractQueryData {
  employmentContracts: LaborContract[];
}

const ContractDossier: React.FC<ContractDossierProps> = ({ userId }) => {
  const { currency } = useCurrency();
  const { data, loading, error } = useQuery<EmploymentContractQueryData>(
    GET_EMPLOYMENT_CONTRACT,
    {
      variables: { userId },
      skip: !userId
    }
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Грешка при зареждане на договора
      </Alert>
    );
  }

  const contracts = data?.employmentContracts || [];
  const contract = contracts.find((c: LaborContract) => c.userId === userId);

  if (!contract) {
    return (
      <Alert severity="info">
        Няма намерен трудов договор за този потребител
      </Alert>
    );
  }

  const status: ContractStatus = contract.status || 'draft';
  const statusInfo = STATUS_LABELS[status];
  const annexes = contract.annexes || [];

  return (
    <Card sx={{ mb: 3, borderRadius: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <CheckCircleIcon color="primary" />
          <Typography variant="h6" fontWeight="bold">
            Трудов договор
          </Typography>
          <Chip
            label={statusInfo.label}
            color={statusInfo.color}
            size="small"
          />
        </Box>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="caption" color="text.secondary">
              Име
            </Typography>
            <Typography variant="body1" fontWeight="medium">
              {contract.employeeName || '—'}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="caption" color="text.secondary">
              ЕГН
            </Typography>
            <Typography variant="body1" fontWeight="medium">
              {contract.employeeEgn || '—'}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="caption" color="text.secondary">
              Номер на договор
            </Typography>
            <Typography variant="body1">
              {contract.contractNumber || '—'}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="caption" color="text.secondary">
              Тип договор
            </Typography>
            <Typography variant="body1">
              {CONTRACT_TYPE_LABELS[contract.contractType] || contract.contractType || '—'}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="caption" color="text.secondary">
              Период
            </Typography>
            <Typography variant="body1">
              {contract.startDate}
              {contract.endDate && ` - ${contract.endDate}`}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="caption" color="text.secondary">
              Основна заплата
            </Typography>
            <Typography variant="body1" color="primary.main" fontWeight="bold">
              {contract.baseSalary ? formatCurrencyValue(contract.baseSalary, currency) : '—'}
            </Typography>
          </Grid>
          {contract.signedAt && (
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="caption" color="text.secondary">
                Дата на подписване
              </Typography>
              <Typography variant="body1">
                {formatDate(contract.signedAt)}
              </Typography>
            </Grid>
          )}
        </Grid>

        {annexes.length > 0 && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <ScheduleIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                История на Анексите
              </Typography>
            </Box>
            
            <Box sx={{ pl: 2, borderLeft: '2px solid', borderColor: 'divider' }}>
              {annexes.map((annex: LaborContractAnnex) => (
                <Box
                  key={annex.id}
                  sx={{
                    position: 'relative',
                    pl: 3,
                    pb: 2,
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      left: -6,
                      top: 4,
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      bgcolor: annex.isSigned ? 'success.main' : 'warning.main',
                      border: '2px solid',
                      borderColor: 'background.paper'
                    }
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    {formatDate(annex.effectiveDate)}
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    Анекс {annex.annexNumber || annex.id}
                    {annex.changeType && (
                      <Chip
                        label={CHANGE_TYPE_LABELS[annex.changeType] || annex.changeType}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Typography>
                  {annex.baseSalary && (
                    <Typography variant="body2" color="primary.main">
                      Заплата: {formatCurrencyValue(annex.baseSalary, currency)}
                    </Typography>
                  )}
                  {annex.changeDescription && (
                    <Typography variant="body2" color="text.secondary">
                      {annex.changeDescription}
                    </Typography>
                  )}
                  {annex.isSigned && (
                    <Chip
                      icon={<CheckCircleIcon />}
                      label="Подписан"
                      color="success"
                      size="small"
                      sx={{ mt: 0.5 }}
                    />
                  )}
                </Box>
              ))}
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default ContractDossier;
