import React, { useState, useMemo } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, FormControl, InputLabel, Select, MenuItem,
  Grid, Alert, CircularProgress, Box, InputAdornment
} from '@mui/material';
import { useMutation, useQuery } from '@apollo/client';
import {
  CREATE_EMPLOYMENT_CONTRACT,
  GENERATE_CONTRACT_NUMBER,
  GET_ORG_DATA_FOR_CONTRACT
} from '../graphql/contracts';
import { type LaborContract, type LaborContractFormData, getErrorMessage } from '../types';
import { InfoIcon } from './ui/InfoIcon';
import { userFieldsHelp } from './ui/fieldsHelpText';

interface EmploymentContractDialogProps {
  open: boolean;
  onClose: () => void;
  contract?: LaborContract | null;
  companyId?: number;
  onSuccess: () => void;
}

const initialFormData: LaborContractFormData = {
  companyId: null,
  departmentId: null,
  positionId: null,
  employeeName: '',
  employeeEgn: '',
  contractNumber: '',
  contractType: 'full_time',
  startDate: '',
  endDate: '',
  baseSalary: '',
  workHoursPerWeek: '40',
  jobDescription: ''
};

interface OrgData {
  companies: Array<{ id: number; name: string }>;
  departments: Array<{ id: number; name: string; companyId: number }>;
  positions: Array<{ id: number; title: string; departmentId: number }>;
}

const EmploymentContractDialog: React.FC<EmploymentContractDialogProps> = ({
  open,
  onClose,
  contract,
  companyId: propCompanyId,
  onSuccess
}) => {
  const [formData, setFormData] = useState<LaborContractFormData>(initialFormData);
  const [apiError, setApiError] = useState('');
  const [validationError, setValidationError] = useState('');
  const prevOpenRef = React.useRef<boolean>(open);

  const { data: orgData } = useQuery<OrgData>(GET_ORG_DATA_FOR_CONTRACT);

  React.useEffect(() => {
    if (prevOpenRef.current && !open) {
      setFormData(initialFormData);
      setApiError('');
      setValidationError('');
    }
    prevOpenRef.current = open;
  }, [open]);

  React.useEffect(() => {
    if (open) {
      if (contract) {
        setFormData({
          companyId: contract.company?.id || null,
          departmentId: contract.department?.id || null,
          positionId: contract.position?.id || null,
          employeeName: contract.employeeName || '',
          employeeEgn: contract.employeeEgn || '',
          contractNumber: contract.contractNumber || '',
          contractType: (contract.contractType as LaborContractFormData['contractType']) || 'full_time',
          startDate: contract.startDate || '',
          endDate: contract.endDate || '',
          baseSalary: contract.baseSalary?.toString() || '',
          workHoursPerWeek: contract.workHoursPerWeek?.toString() || '40',
          jobDescription: ''
        });
      } else {
        setFormData({
          ...initialFormData,
          companyId: propCompanyId || null
        });
      }
      setApiError('');
      setValidationError('');
    }
  }, [contract, open, propCompanyId]);

  const filteredDepartments = useMemo(() => {
    if (!orgData?.departments) return [];
    if (!formData.companyId) return orgData.departments;
    return orgData.departments.filter(d => d.companyId === formData.companyId);
  }, [orgData, formData.companyId]);

  const filteredPositions = useMemo(() => {
    if (!orgData?.positions) return [];
    if (!formData.departmentId) return orgData.positions;
    return orgData.positions.filter(p => p.departmentId === formData.departmentId);
  }, [orgData, formData.departmentId]);

  const handleTextChange = (field: keyof LaborContractFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
    setValidationError('');
  };

  const handleSelectChange = (field: keyof LaborContractFormData) => (
    event: { target: { value: unknown } }
  ) => {
    const value = event.target.value;
    const newFormData = { ...formData, [field]: value };
    if (field === 'companyId') {
      newFormData.departmentId = null;
      newFormData.positionId = null;
    } else if (field === 'departmentId') {
      newFormData.positionId = null;
    }
    setFormData(newFormData);
    setValidationError('');
  };

  const validateForm = (): boolean => {
    if (!formData.employeeName.trim()) {
      setValidationError('Името на служителя е задължително');
      return false;
    }
    if (!formData.employeeEgn.trim()) {
      setValidationError('ЕГН е задължително');
      return false;
    }
    if (!formData.startDate) {
      setValidationError('Началната дата е задължителна');
      return false;
    }
    return true;
  };

  const [createContract, { loading }] = useMutation(CREATE_EMPLOYMENT_CONTRACT, {
    onCompleted: () => {
      onSuccess();
    },
    onError: (err) => {
      setApiError(getErrorMessage(err));
    }
  });

  const [generateNumber, { loading: generatingNumber }] = useMutation(GENERATE_CONTRACT_NUMBER, {
    onCompleted: (data) => {
      setFormData(prev => ({ ...prev, contractNumber: data.generateContractNumber }));
    },
    onError: (err) => {
      setApiError(getErrorMessage(err));
    }
  });

  const handleGenerateNumber = () => {
    if (formData.companyId) {
      generateNumber({ variables: { companyId: formData.companyId } });
    } else {
      setValidationError('Моля, първо изберете фирма');
    }
  };

  const handleSubmit = () => {
    if (!validateForm()) return;

    const input = {
      employeeName: formData.employeeName,
      employeeEgn: formData.employeeEgn,
      companyId: formData.companyId,
      departmentId: formData.departmentId || null,
      positionId: formData.positionId || null,
      contractType: formData.contractType,
      contractNumber: formData.contractNumber || null,
      startDate: formData.startDate,
      endDate: formData.endDate || null,
      baseSalary: formData.baseSalary ? parseFloat(formData.baseSalary) : null,
      workHoursPerWeek: parseInt(formData.workHoursPerWeek, 10) || 40,
      jobDescription: formData.jobDescription || null
    };

    createContract({ variables: { input } });
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {contract ? 'Редактиране на договор' : 'Създаване на трудов договор'}
      </DialogTitle>
      <DialogContent>
        {apiError && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setApiError('')}>
            {apiError}
          </Alert>
        )}
        {validationError && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            {validationError}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid size={{ xs: 12, sm: 4 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Фирма *</InputLabel>
              <Select
                value={formData.companyId ?? ''}
                label="Фирма *"
                onChange={handleSelectChange('companyId')}
              >
                {orgData?.companies.map((c) => (
                  <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Отдел</InputLabel>
              <Select
                value={formData.departmentId ?? ''}
                label="Отдел"
                onChange={handleSelectChange('departmentId')}
              >
                {filteredDepartments.map((d) => (
                  <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Длъжност</InputLabel>
              <Select
                value={formData.positionId ?? ''}
                label="Длъжност"
                onChange={handleSelectChange('positionId')}
              >
                {filteredPositions.map((p) => (
                  <MenuItem key={p.id} value={p.id}>{p.title}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Име на служител *"
              value={formData.employeeName}
              onChange={handleTextChange('employeeName')}
              required
              size="small"
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={userFieldsHelp.firstName} /></InputAdornment> } }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="ЕГН *"
              value={formData.employeeEgn}
              onChange={handleTextChange('employeeEgn')}
              required
              size="small"
              inputProps={{ maxLength: 10 }}
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={userFieldsHelp.egn} /></InputAdornment> } }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
              <TextField
                fullWidth
                label="Номер на договор"
                value={formData.contractNumber}
                onChange={handleTextChange('contractNumber')}
                size="small"
                placeholder="Натиснете бутона за автоматичен номер"
                slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={userFieldsHelp.contractNumber} /></InputAdornment> } }}
              />
              <Button
                variant="outlined"
                size="small"
                onClick={handleGenerateNumber}
                disabled={generatingNumber || !formData.companyId}
                sx={{ mt: 0.5, whiteSpace: 'nowrap' }}
              >
                {generatingNumber ? <CircularProgress size={20} /> : 'Генерирай'}
              </Button>
            </Box>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Тип договор</InputLabel>
              <Select
                value={formData.contractType}
                label="Тип договор"
                onChange={handleSelectChange('contractType')}
              >
                <MenuItem value="full_time">Пълно работно време</MenuItem>
                <MenuItem value="part_time">Непълно работно време</MenuItem>
                <MenuItem value="contractor">Граждански договор</MenuItem>
                <MenuItem value="internship">Стажант</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <TextField
              fullWidth
              label="Начална дата *"
              type="date"
              value={formData.startDate}
              onChange={handleTextChange('startDate')}
              required
              size="small"
              InputLabelProps={{ shrink: true }}
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={userFieldsHelp.contractStartDate} /></InputAdornment> } }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <TextField
              fullWidth
              label="Крайна дата"
              type="date"
              value={formData.endDate}
              onChange={handleTextChange('endDate')}
              size="small"
              InputLabelProps={{ shrink: true }}
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={userFieldsHelp.contractEndDate} /></InputAdornment> } }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 4 }}>
            <TextField
              fullWidth
              label="Работни часове/седмица"
              type="number"
              value={formData.workHoursPerWeek}
              onChange={handleTextChange('workHoursPerWeek')}
              size="small"
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={userFieldsHelp.workHoursPerWeek} /></InputAdornment> } }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Основна заплата"
              type="number"
              value={formData.baseSalary}
              onChange={handleTextChange('baseSalary')}
              size="small"
              slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={userFieldsHelp.baseSalary} /></InputAdornment> } }}
            />
          </Grid>
          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              label="Трудова характеристика"
              multiline
              rows={4}
              value={formData.jobDescription}
              onChange={handleTextChange('jobDescription')}
              size="small"
              placeholder="Описание на длъжността и задълженията..."
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отмени</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
        >
          {loading ? <CircularProgress size={24} /> : contract ? 'Запази' : 'Създай'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default EmploymentContractDialog;
