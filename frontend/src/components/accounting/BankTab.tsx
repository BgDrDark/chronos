import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  TextField,
  Typography,
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon } from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import { useCurrency, formatCurrencyValue } from '../../currencyContext';
import {
  GET_BANK_ACCOUNTS,
  GET_BANK_TRANSACTIONS,
  GET_INVOICES,
  CREATE_BANK_ACCOUNT,
  CREATE_BANK_TRANSACTION,
  MATCH_BANK_TRANSACTION,
  UNMATCH_BANK_TRANSACTION,
  AUTO_MATCH_BANK_TRANSACTIONS,
} from '../../graphql/accountingQueries';
import type { Invoice } from '../../types';
import { formatDate } from '../../utils/dateUtils';

interface BankAccount {
  id: number;
  iban: string;
  bic: string;
  bankName: string;
  accountType: string;
  isDefault: boolean;
  currency: string;
  isActive: boolean;
}

interface BankTransaction {
  id: number;
  bankAccountId: number;
  date: string;
  amount: number;
  type: string;
  description: string;
  reference: string;
  invoiceId?: number;
  matched: boolean;
}

export const BankTab: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showMatched, setShowMatched] = useState<boolean | undefined>(undefined);
  const [openAccountDialog, setOpenAccountDialog] = useState(false);
  const [openTransactionDialog, setOpenTransactionDialog] = useState(false);
  const [openMatchDialog, setOpenMatchDialog] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<BankTransaction | null>(null);
  const { currency } = useCurrency();

  const { data: accountsData, loading: loadingAccounts } = useQuery(GET_BANK_ACCOUNTS);
  const { data: transactionsData, loading: loadingTransactions, refetch } = useQuery(GET_BANK_TRANSACTIONS, {
    variables: { bankAccountId: accountId || undefined, startDate: startDate || undefined, endDate: endDate || undefined, matched: showMatched },
  });

  const { data: invoicesData } = useQuery(GET_INVOICES, {
    variables: { type: undefined, status: undefined },
  });

  const [createAccount] = useMutation(CREATE_BANK_ACCOUNT);
  const [createTransaction] = useMutation(CREATE_BANK_TRANSACTION);
  const [matchTransaction] = useMutation(MATCH_BANK_TRANSACTION);
  const [unmatchTransaction] = useMutation(UNMATCH_BANK_TRANSACTION);
  const [autoMatchTransactions] = useMutation(AUTO_MATCH_BANK_TRANSACTIONS);

  const accounts: BankAccount[] = accountsData?.bankAccounts || [];
  const transactions: BankTransaction[] = transactionsData?.bankTransactions || [];
  const invoices: Invoice[] = invoicesData?.invoices || [];

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  const [accountForm, setAccountForm] = useState({
    iban: '', bic: '', bankName: '', accountType: 'current', isDefault: false, currency: 'BGN'
  });

  const [transactionForm, setTransactionForm] = useState({
    date: new Date().toISOString().split('T')[0],
    amount: '', type: 'credit', description: '', reference: ''
  });

  const handleSaveAccount = async () => {
    try {
      await createAccount({ variables: { input: { ...accountForm, companyId: 1 } } });
      setOpenAccountDialog(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveTransaction = async () => {
    if (!accountId) return;
    try {
      await createTransaction({
        variables: {
          input: { bankAccountId: accountId, date: transactionForm.date, amount: parseFloat(transactionForm.amount), type: transactionForm.type, description: transactionForm.description, reference: transactionForm.reference, companyId: 1 }
        }
      });
      setOpenTransactionDialog(false);
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMatchTransaction = async (transactionId: number, invoiceId: number) => {
    try {
      await matchTransaction({ variables: { transactionId, invoiceId } });
      refetch();
      setOpenMatchDialog(false);
      setSelectedTransaction(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUnmatchTransaction = async (transactionId: number) => {
    try {
      await unmatchTransaction({ variables: { transactionId } });
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleAutoMatch = async () => {
    if (!accountId) return;
    try {
      const result = await autoMatchTransactions({ variables: { bankAccountId: accountId } });
      if (result.data?.autoMatchBankTransactions) {
        alert(`Съпоставени: ${result.data.autoMatchBankTransactions.matchedCount}, Не съпоставени: ${result.data.autoMatchBankTransactions.unmatchedCount}`);
      }
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenMatchDialog = (tx: BankTransaction) => {
    setSelectedTransaction(tx);
    setOpenMatchDialog(true);
  };

  const matchedCount = transactions.filter((tx: BankTransaction) => tx.matched).length;
  const unmatchedCount = transactions.filter((tx: BankTransaction) => !tx.matched).length;

  return (
    <Box>
      <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)} sx={{ mb: 2 }}>
        <Tab label="Банкови сметки" />
        <Tab label="Транзакции" />
      </Tabs>

      {activeTab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenAccountDialog(true)}>
              Нова сметка
            </Button>
          </Box>
          {loadingAccounts ? <CircularProgress /> : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>IBAN</TableCell>
                    <TableCell>Банка</TableCell>
                    <TableCell>BIC</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell>Валута</TableCell>
                    <TableCell>По подразбиране</TableCell>
                    <TableCell>Активна</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {accounts.map((acc: BankAccount) => (
                    <TableRow key={acc.id}>
                      <TableCell sx={{ fontFamily: 'monospace' }}>{acc.iban}</TableCell>
                      <TableCell>{acc.bankName}</TableCell>
                      <TableCell>{acc.bic}</TableCell>
                      <TableCell>{acc.accountType}</TableCell>
                      <TableCell>{acc.currency}</TableCell>
                      <TableCell>{acc.isDefault ? '✅' : ''}</TableCell>
                      <TableCell>{acc.isActive ? '✅' : '❌'}</TableCell>
                    </TableRow>
                  ))}
                  {accounts.length === 0 && (
                    <TableRow><TableCell colSpan={7} align="center">Няма банкови сметки</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      )}

      {activeTab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Сметка</InputLabel>
              <Select value={accountId || ''} label="Сметка" onChange={(e) => setAccountId(e.target.value as number)}>
                {accounts.map((acc: BankAccount) => (
                  <MenuItem key={acc.id} value={acc.id}>{acc.bankName} - {acc.iban?.slice(-4) || '----'}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField size="small" label="От дата" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <TextField size="small" label="До дата" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Съпоставени</InputLabel>
              <Select value={showMatched === undefined ? '' : showMatched ? 'matched' : 'unmatched'} label="Съпоставени" onChange={(e) => {
                const val = e.target.value;
                setShowMatched(val === 'matched' ? true : val === 'unmatched' ? false : undefined);
              }}>
                <MenuItem value="">Всички</MenuItem>
                <MenuItem value="matched">Само съпоставени</MenuItem>
                <MenuItem value="unmatched">Само не съпоставени</MenuItem>
              </Select>
            </FormControl>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenTransactionDialog(true)} disabled={!accountId}>Нова транзакция</Button>
            <Button variant="outlined" startIcon={<EditIcon />} onClick={handleAutoMatch} disabled={!accountId}>Автоматично съпоставяне</Button>
          </Box>
          {accountId && (
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Chip label={`Съпоставени: ${matchedCount}`} color="success" />
              <Chip label={`Не съпоставени: ${unmatchedCount}`} color="warning" />
            </Box>
          )}
          {loadingTransactions ? <CircularProgress /> : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Дата</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell align="right">Сума</TableCell>
                    <TableCell>Описание</TableCell>
                    <TableCell>Референция</TableCell>
                    <TableCell>Съответства</TableCell>
                    <TableCell>Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactions.map((tx: BankTransaction) => (
                    <TableRow key={tx.id} sx={{ backgroundColor: tx.type === 'credit' ? '#e8f5e9' : '#ffebee' }}>
                      <TableCell>{formatDate(tx.date)}</TableCell>
                      <TableCell><Chip label={tx.type === 'credit' ? 'Приход' : 'Разход'} color={tx.type === 'credit' ? 'success' : 'error'} size="small" /></TableCell>
                      <TableCell align="right">{formatPrice(Number(tx.amount))}</TableCell>
                      <TableCell>{tx.description}</TableCell>
                      <TableCell>{tx.reference}</TableCell>
                      <TableCell>{tx.matched ? <Chip label={`✅ ${tx.invoiceId || ''}`} size="small" color="success" /> : <Chip label="❌ Не" size="small" color="warning" variant="outlined" />}</TableCell>
                      <TableCell>
                        {tx.matched ? <Button size="small" color="error" onClick={() => handleUnmatchTransaction(tx.id)}>Премахни</Button> : <Button size="small" variant="contained" onClick={() => handleOpenMatchDialog(tx)}>Съпостави</Button>}
                      </TableCell>
                    </TableRow>
                  ))}
                  {transactions.length === 0 && (<TableRow><TableCell colSpan={7} align="center">Няма транзакции</TableCell></TableRow>)}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      )}

      <Dialog open={openAccountDialog} onClose={() => setOpenAccountDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова банкова сметка</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}><TextField fullWidth label="IBAN" value={accountForm.iban} onChange={(e) => setAccountForm({...accountForm, iban: e.target.value})} /></Grid>
            <Grid size={{ xs: 12 }}><TextField fullWidth label="Банка" value={accountForm.bankName} onChange={(e) => setAccountForm({...accountForm, bankName: e.target.value})} /></Grid>
            <Grid size={{ xs: 6 }}><TextField fullWidth label="BIC" value={accountForm.bic} onChange={(e) => setAccountForm({...accountForm, bic: e.target.value})} /></Grid>
            <Grid size={{ xs: 6 }}>
              <FormControl fullWidth><InputLabel>Тип</InputLabel><Select value={accountForm.accountType} label="Тип" onChange={(e) => setAccountForm({...accountForm, accountType: e.target.value})}><MenuItem value="current">Разплащателна</MenuItem><MenuItem value="escrow">Ескроу</MenuItem></Select></FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions><Button onClick={() => setOpenAccountDialog(false)}>Отказ</Button><Button onClick={handleSaveAccount} variant="contained">Запази</Button></DialogActions>
      </Dialog>

      <Dialog open={openTransactionDialog} onClose={() => setOpenTransactionDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нова транзакция</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 6 }}><TextField fullWidth label="Дата" type="date" value={transactionForm.date} onChange={(e) => setTransactionForm({...transactionForm, date: e.target.value})} slotProps={{ inputLabel: { shrink: true } }} /></Grid>
            <Grid size={{ xs: 6 }}><FormControl fullWidth><InputLabel>Тип</InputLabel><Select value={transactionForm.type} label="Тип" onChange={(e) => setTransactionForm({...transactionForm, type: e.target.value})}><MenuItem value="credit">Приход</MenuItem><MenuItem value="debit">Разход</MenuItem></Select></FormControl></Grid>
            <Grid size={{ xs: 12 }}><TextField fullWidth label="Сума" type="number" value={transactionForm.amount} onChange={(e) => setTransactionForm({...transactionForm, amount: e.target.value})} /></Grid>
            <Grid size={{ xs: 12 }}><TextField fullWidth label="Описание" value={transactionForm.description} onChange={(e) => setTransactionForm({...transactionForm, description: e.target.value})} /></Grid>
            <Grid size={{ xs: 12 }}><TextField fullWidth label="Референция" value={transactionForm.reference} onChange={(e) => setTransactionForm({...transactionForm, reference: e.target.value})} /></Grid>
          </Grid>
        </DialogContent>
        <DialogActions><Button onClick={() => setOpenTransactionDialog(false)}>Отказ</Button><Button onClick={handleSaveTransaction} variant="contained">Запази</Button></DialogActions>
      </Dialog>

      <Dialog open={openMatchDialog} onClose={() => setOpenMatchDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Съпостави транзакция #{selectedTransaction?.id}</DialogTitle>
        <DialogContent dividers>
          {selectedTransaction && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary">Транзакция:</Typography>
              <Typography variant="body1">{selectedTransaction.type === 'credit' ? 'Приход' : 'Разход'} - {formatPrice(Number(selectedTransaction.amount))}</Typography>
              <Typography variant="body2" color="text.secondary">Референция: {selectedTransaction.reference || '-'}</Typography>
            </Box>
          )}
          <Typography variant="subtitle2" sx={{ mb: 2 }}>Избери фактура:</Typography>
          <FormControl fullWidth size="small">
            <InputLabel>Фактура</InputLabel>
            <Select label="Фактура" onChange={(e) => { if (selectedTransaction && e.target.value) handleMatchTransaction(selectedTransaction.id, e.target.value as number); }}>
              {invoices.filter((inv: Invoice) => Math.abs(Number(inv.total) - Number(selectedTransaction?.amount)) < 0.01).map((inv: Invoice) => (
                <MenuItem key={inv.id} value={inv.id}>{inv.number} - {inv.supplier?.name || inv.clientName || '-'} - {formatPrice(Number(inv.total))}</MenuItem>
              ))}
            </Select>
          </FormControl>
          {invoices.filter((inv: Invoice) => Math.abs(Number(inv.total) - Number(selectedTransaction?.amount)) < 0.01).length === 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>Няма намерени фактури със същата сума.</Alert>
          )}
          <Divider sx={{ my: 2 }} />
          <Typography variant="caption" color="text.secondary">Или изберете ръчно:</Typography>
          <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
            {invoices.slice(0, 10).map((inv: Invoice) => (
              <ListItem key={inv.id} disablePadding sx={{ cursor: 'pointer' }} onClick={() => selectedTransaction && handleMatchTransaction(selectedTransaction.id, inv.id)}>
                <ListItemText primary={`${inv.number} - ${inv.supplier?.name || inv.clientName || '-'}`} secondary={`${formatPrice(Number(inv.total))} - ${formatDate(inv.date)}`} />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions><Button onClick={() => setOpenMatchDialog(false)}>Затвори</Button></DialogActions>
      </Dialog>
    </Box>
  );
};