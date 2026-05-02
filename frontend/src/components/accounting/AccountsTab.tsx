import React, { useState } from 'react';
import { Box, Select, MenuItem, Button, TableContainer, Paper, Table, TableHead, TableRow, TableCell, TableBody, Chip, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, Grid, TextField, FormControl, InputLabel } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { useQuery, useMutation } from '@apollo/client';
import { useCurrency } from '../../currencyContext';
import { GET_ACCOUNTS, CREATE_ACCOUNT } from '../../graphql/accountingQueries';
import { Account } from '../../types';

const AccountsTab: React.FC = () => {
  const [type, setType] = useState('');
  useCurrency();

  const { data, loading, refetch } = useQuery(GET_ACCOUNTS, {
    variables: { type: type || undefined },
  });

  const [createAccount] = useMutation(CREATE_ACCOUNT);

  const accounts = data?.accounts || [];

  const [openDialog, setOpenDialog] = useState(false);
  const [accountForm, setAccountForm] = useState({ code: '', name: '', type: 'expense', parentId: null as number | null });

  const handleSave = async () => {
    try {
      await createAccount({
        variables: {
          input: { ...accountForm, companyId: 1, openingBalance: 0 }
        }
      });
      setOpenDialog(false);
      setAccountForm({ code: '', name: '', type: 'expense', parentId: null });
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <Select size="small" value={type} onChange={(e) => setType(e.target.value)} displayEmpty sx={{ minWidth: 150 }}>
          <MenuItem value="">Всички типове</MenuItem>
          <MenuItem value="asset">Активи</MenuItem>
          <MenuItem value="liability">Пасиви</MenuItem>
          <MenuItem value="equity">Собствен капитал</MenuItem>
          <MenuItem value="revenue">Приходи</MenuItem>
          <MenuItem value="expense">Разходи</MenuItem>
        </Select>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenDialog(true)}>
          Нова сметка
        </Button>
      </Box>

      {loading ? <CircularProgress /> : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Код</TableCell>
                <TableCell>Име</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell align="right">Начално салдо</TableCell>
                <TableCell align="right">Крайно салдо</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {accounts.map((acc: Account) => (
                <TableRow key={acc.id}>
                  <TableCell sx={{ fontWeight: 'bold' }}>{acc.code}</TableCell>
                  <TableCell>{acc.name}</TableCell>
                  <TableCell>
                    <Chip label={acc.type} size="small" color={
                      acc.type === 'asset' ? 'success' :
                      acc.type === 'liability' ? 'error' :
                      acc.type === 'revenue' ? 'info' : 'default'
                    } />
                  </TableCell>
                  <TableCell align="right">{Number(acc.balance).toFixed(2)}</TableCell>
                  <TableCell align="right">{Number(acc.balance).toFixed(2)}</TableCell>
                </TableRow>
              ))}
              {accounts.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">Няма сметки</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова сметка</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 4 }}>
              <TextField fullWidth label="Код" value={accountForm.code} onChange={(e) => setAccountForm({...accountForm, code: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 8 }}>
              <TextField fullWidth label="Име" value={accountForm.name} onChange={(e) => setAccountForm({...accountForm, name: e.target.value})} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Тип</InputLabel>
                <Select value={accountForm.type} label="Тип" onChange={(e) => setAccountForm({...accountForm, type: e.target.value})}>
                  <MenuItem value="asset">Актив</MenuItem>
                  <MenuItem value="liability">Пасив</MenuItem>
                  <MenuItem value="equity">Собствен капитал</MenuItem>
                  <MenuItem value="revenue">Приход</MenuItem>
                  <MenuItem value="expense">Разход</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Отказ</Button>
          <Button onClick={handleSave} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AccountsTab;
