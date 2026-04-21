import React, { useState, useCallback, useMemo } from 'react';
import { useCurrency, formatCurrencyValue } from '../currencyContext';
import {
  Box, Typography, Card, CardContent, Button, Chip,
  CircularProgress, Alert, Grid, IconButton,
  Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import PrintIcon from '@mui/icons-material/Print';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LinkIcon from '@mui/icons-material/Link';
import EditIcon from '@mui/icons-material/Edit';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_EMPLOYMENT_CONTRACTS,
  SIGN_EMPLOYMENT_CONTRACT,
  LINK_CONTRACT_TO_USER,
  GET_USERS_FOR_LINK,
  GET_ORG_DATA_FOR_CONTRACT
} from '../graphql/contracts';
import { type LaborContract, type ContractStatus, type User, getErrorMessage } from '../types';
import EmploymentContractDialog from './EmploymentContractDialog';

interface EmploymentContractsListProps {
  companyId?: number;
}

const CONTRACT_TYPE_LABELS: Record<string, string> = {
  full_time: 'Пълно работно време',
  part_time: 'Непълно работно време',
  contractor: 'Граждански договор',
  internship: 'Стажант'
};

const STATUS_COLORS: Record<ContractStatus, 'warning' | 'success' | 'info' | 'default'> = {
  draft: 'warning',
  signed: 'success',
  linked: 'info'
};

const STATUS_LABELS: Record<ContractStatus, string> = {
  draft: 'Чернова',
  signed: 'Подписан',
  linked: 'Свързан'
};

interface GetEmploymentContractsData {
  employmentContracts: LaborContract[];
}

interface GetUsersData {
  users: {
    users: User[];
  };
}

interface OrgData {
  companies: Array<{ id: number; name: string }>;
}

const EmploymentContractsList: React.FC<EmploymentContractsListProps> = ({ companyId }) => {
  const { currency } = useCurrency();
  const [statusFilter, setStatusFilter] = useState<ContractStatus | ''>('');
  const [companyFilter, setCompanyFilter] = useState<number | ''>(companyId || '');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<LaborContract | null>(null);
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [selectedContractForLink, setSelectedContractForLink] = useState<LaborContract | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<number | ''>('');
  const [apiError, setApiError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const { data, loading, refetch } = useQuery<GetEmploymentContractsData>(
    GET_EMPLOYMENT_CONTRACTS,
    {
      variables: {
        companyId: companyFilter || null,
        status: statusFilter || null
      },
      fetchPolicy: 'network-only'
    }
  );

  const { data: usersData } = useQuery<GetUsersData>(GET_USERS_FOR_LINK);
  const { data: orgData } = useQuery<OrgData>(GET_ORG_DATA_FOR_CONTRACT);

  const [signContract, { loading: signing }] = useMutation(SIGN_EMPLOYMENT_CONTRACT);
  const [linkContract, { loading: linking }] = useMutation(LINK_CONTRACT_TO_USER);

  const contracts = useMemo(() => data?.employmentContracts || [], [data]);

  const handleCreate = useCallback(() => {
    setSelectedContract(null);
    setDialogOpen(true);
  }, []);

  const handleEdit = useCallback((contract: LaborContract) => {
    setSelectedContract(contract);
    setDialogOpen(true);
  }, []);

  const handleSign = useCallback(async (contractId: number) => {
    if (!window.confirm('Сигурни ли сте, че искате да маркирате договора като подписан?')) {
      return;
    }
    try {
      setApiError('');
      await signContract({ variables: { id: contractId } });
      setSuccessMessage('Договорът е маркиран като подписан');
      refetch();
    } catch (err) {
      setApiError(getErrorMessage(err));
    }
  }, [signContract, refetch]);

  const handleLink = useCallback((contract: LaborContract) => {
    setSelectedContractForLink(contract);
    setSelectedUserId('');
    setLinkDialogOpen(true);
  }, []);

  const handleLinkConfirm = useCallback(async () => {
    if (!selectedContractForLink || !selectedUserId) return;
    try {
      setApiError('');
      await linkContract({
        variables: {
          contractId: selectedContractForLink.id,
          userId: selectedUserId
        }
      });
      setSuccessMessage('Договорът е свързан с потребителя');
      setLinkDialogOpen(false);
      refetch();
    } catch (err) {
      setApiError(getErrorMessage(err));
    }
  }, [selectedContractForLink, selectedUserId, linkContract, refetch]);

  const handlePrint = useCallback((contractId: number) => {
    const apiUrl = import.meta.env.VITE_API_URL || 'https://dev.oblak24.org';
    window.open(`${apiUrl}/export/contract/${contractId}/pdf`, '_blank');
  }, []);

  const handlePrintAnnex = useCallback((annexId: number) => {
    const apiUrl = import.meta.env.VITE_API_URL || 'https://dev.oblak24.org';
    window.open(`${apiUrl}/export/annex/${annexId}/pdf`, '_blank');
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <Typography variant="h6">Трудови договори ({contracts.length})</Typography>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Фирма</InputLabel>
            <Select
              value={companyFilter}
              label="Фирма"
              onChange={(e) => setCompanyFilter(e.target.value as number | '')}
            >
              <MenuItem value=""> Всички</MenuItem>
              {orgData?.companies.map((c) => (
                <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Статус</InputLabel>
            <Select
              value={statusFilter}
              label="Статус"
              onChange={(e) => setStatusFilter(e.target.value as ContractStatus | '')}
            >
              <MenuItem value=""> Всички</MenuItem>
              <MenuItem value="draft"> Чернова</MenuItem>
              <MenuItem value="signed"> Подписан</MenuItem>
              <MenuItem value="linked"> Свързан</MenuItem>
            </Select>
          </FormControl>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          Нов договор
        </Button>
      </Box>

      {apiError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setApiError('')}>
          {apiError}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage('')}>
          {successMessage}
        </Alert>
      )}

      {contracts.length === 0 ? (
        <Alert severity="info">Няма намерени договори</Alert>
      ) : (
        <Grid container spacing={2}>
          {contracts.map((contract) => {
            const status = contract.status || 'draft';
            return (
              <Grid size={{ xs: 12 }} key={contract.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6">
                            {contract.employeeName || 'Без име'}
                          </Typography>
                          <Chip
                            label={STATUS_LABELS[status]}
                            color={STATUS_COLORS[status]}
                            size="small"
                          />
                          {contract.company && (
                            <Chip
                              label={contract.company.name}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          ЕГН: {contract.employeeEgn || '—'}
                        </Typography>
                        {contract.contractNumber && (
                          <Typography variant="body2" color="text.secondary">
                            №: {contract.contractNumber}
                          </Typography>
                        )}
                        <Typography variant="body2" color="text.secondary">
                          {CONTRACT_TYPE_LABELS[contract.contractType] || contract.contractType}
                        </Typography>
                        {contract.department && (
                          <Typography variant="body2" color="text.secondary">
                            Отдел: {contract.department.name}
                          </Typography>
                        )}
                        {contract.position && (
                          <Typography variant="body2" color="text.secondary">
                            Длъжност: {contract.position.title}
                          </Typography>
                        )}
                        <Typography variant="body2" color="text.secondary">
                          {contract.startDate}
                          {contract.endDate && ` до ${contract.endDate}`}
                        </Typography>
                        {contract.baseSalary && (
                          <Typography variant="body2" color="primary.main" fontWeight="bold">
                            {formatCurrencyValue(contract.baseSalary, currency)}
                          </Typography>
                        )}

                        {contract.annexes && contract.annexes.length > 0 && (
                          <Box sx={{ mt: 2, pl: 1, borderLeft: '2px solid', borderColor: 'divider' }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Анекси ({contract.annexes.length}):
                            </Typography>
                            {contract.annexes.map((annex) => (
                              <Box key={annex.id} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                <Chip 
                                  label={`${annex.annexNumber || 'Анекс '+annex.id} - ${annex.effectiveDate}`}
                                  size="small"
                                  color={annex.isSigned ? 'success' : 'warning'}
                                />
                                <IconButton 
                                  size="small" 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handlePrintAnnex(annex.id);
                                  }}
                                  title="Принтирай анекс"
                                >
                                  <PrintIcon fontSize="small" />
                                </IconButton>
                              </Box>
                            ))}
                          </Box>
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {status === 'draft' && (
                          <Button
                            size="small"
                            variant="contained"
                            color="success"
                            startIcon={<CheckCircleIcon />}
                            onClick={() => handleSign(contract.id)}
                            disabled={signing}
                          >
                            Подпиши
                          </Button>
                        )}
                        {status === 'signed' && (
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<LinkIcon />}
                            onClick={() => handleLink(contract)}
                            disabled={linking}
                          >
                            Свържи
                          </Button>
                        )}
                        <IconButton onClick={() => handlePrint(contract.id)} title="Принтирай">
                          <PrintIcon />
                        </IconButton>
                        <IconButton onClick={() => handleEdit(contract)} title="Редактирай">
                          <EditIcon />
                        </IconButton>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      <EmploymentContractDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        contract={selectedContract}
        companyId={companyFilter || undefined}
        onSuccess={() => {
          setDialogOpen(false);
          refetch();
        }}
      />

      <Dialog open={linkDialogOpen} onClose={() => setLinkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Свържи договор с потребител</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Потребител</InputLabel>
            <Select
              value={selectedUserId}
              label="Потребител"
              onChange={(e) => setSelectedUserId(e.target.value as number)}
            >
              {usersData?.users?.users?.map((user: User) => (
                <MenuItem key={user.id} value={user.id}>
                  {user.firstName} {user.lastName} ({user.email})
                </MenuItem>
              )) || []}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkDialogOpen(false)}>Отмени</Button>
          <Button
            onClick={handleLinkConfirm}
            variant="contained"
            disabled={!selectedUserId || linking}
          >
            Свържи
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EmploymentContractsList;
