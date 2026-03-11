import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  LocalShipping as DeliveryIcon,
  ShoppingCart as OrderIcon,
  RequestQuote as RequestIcon,
  People as SupplierIcon,
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const LogisticsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [suppliersOpen, setSuppliersOpen] = useState(false);
  const [requestsOpen, setRequestsOpen] = useState(false);
  const [ordersOpen, setOrdersOpen] = useState(false);
  const [deliveriesOpen, setDeliveriesOpen] = useState(false);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 2 }}>
        <Typography variant="h5" component="div" sx={{ fontWeight: 'bold', py: 2 }}>
          Логистика
        </Typography>
      </Box>
      
      <Tabs value={tabValue} onChange={handleTabChange} sx={{ px: 2 }}>
        <Tab icon={<SupplierIcon />} label="Доставчици" />
        <Tab icon={<RequestIcon />} label="Заявки" />
        <Tab icon={<OrderIcon />} label="Поръчки" />
        <Tab icon={<DeliveryIcon />} label="Доставки" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setSuppliersOpen(true)}
          >
            Нов доставчик
          </Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Име</TableCell>
                <TableCell>ЕИК</TableCell>
                <TableCell>Адрес</TableCell>
                <TableCell>Телефон</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell align="right">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Няма данни. Добавете първия доставчик.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setRequestsOpen(true)}
          >
            Нова заявка
          </Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Номер</TableCell>
                <TableCell>Заявил</TableCell>
                <TableCell>Отдел</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Приоритет</TableCell>
                <TableCell>Срок</TableCell>
                <TableCell>Авто</TableCell>
                <TableCell align="right">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell colSpan={8} align="center">
                  Няма заявки.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOrdersOpen(true)}
          >
            Нова поръчка
          </Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Номер</TableCell>
                <TableCell>Доставчик</TableCell>
                <TableCell>Заявка</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Дата поръчка</TableCell>
                <TableCell>Очаквана</TableCell>
                <TableCell align="right">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Няма поръчки.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDeliveriesOpen(true)}
          >
            Нова доставка
          </Button>
        </Box>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Номер</TableCell>
                <TableCell>Поръчка</TableCell>
                <TableCell>Автомобил</TableCell>
                <TableCell>Водач</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Изпратена</TableCell>
                <TableCell>Доставена</TableCell>
                <TableCell align="right">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell colSpan={8} align="center">
                  Няма доставки.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Dialogs would be implemented here */}
      <Dialog open={suppliersOpen} onClose={() => setSuppliersOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Нов доставчик</DialogTitle>
        <DialogContent>
          <TextField autoFocus margin="dense" label="Име" fullWidth variant="outlined" />
          <TextField margin="dense" label="ЕИК" fullWidth variant="outlined" />
          <TextField margin="dense" label="МОЛ" fullWidth variant="outlined" />
          <TextField margin="dense" label="Адрес" fullWidth variant="outlined" />
          <TextField margin="dense" label="Телефон" fullWidth variant="outlined" />
          <TextField margin="dense" label="Email" fullWidth variant="outlined" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSuppliersOpen(false)}>Отказ</Button>
          <Button onClick={() => setSuppliersOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={requestsOpen} onClose={() => setRequestsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Нова заявка</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Отдел</InputLabel>
            <Select label="Отдел">
              <MenuItem value="">-- Избери --</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Приоритет</InputLabel>
            <Select label="Приоритет" defaultValue="medium">
              <MenuItem value="low">Нисък</MenuItem>
              <MenuItem value="medium">Среден</MenuItem>
              <MenuItem value="high">Висок</MenuItem>
              <MenuItem value="urgent">Спешен</MenuItem>
            </Select>
          </FormControl>
          <TextField margin="dense" label="Мотивировка" fullWidth multiline rows={3} variant="outlined" />
          <TextField margin="dense" label="Срок" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRequestsOpen(false)}>Отказ</Button>
          <Button onClick={() => setRequestsOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={ordersOpen} onClose={() => setOrdersOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Нова поръчка</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Доставчик</InputLabel>
            <Select label="Доставчик">
              <MenuItem value="">-- Избери --</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Заявка</InputLabel>
            <Select label="Заявка">
              <MenuItem value="">-- Избери --</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Статус</InputLabel>
            <Select label="Статус" defaultValue="draft">
              <MenuItem value="draft">Чернова</MenuItem>
              <MenuItem value="sent">Изпратена</MenuItem>
              <MenuItem value="confirmed">Потвърдена</MenuItem>
            </Select>
          </FormControl>
          <TextField margin="dense" label="Дата поръчка" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
          <TextField margin="dense" label="Очаквана дата" type="date" fullWidth variant="outlined" InputLabelProps={{ shrink: true }} />
          <TextField margin="dense" label="Забележки" fullWidth multiline rows={3} variant="outlined" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOrdersOpen(false)}>Отказ</Button>
          <Button onClick={() => setOrdersOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deliveriesOpen} onClose={() => setDeliveriesOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Нова доставка</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Поръчка</InputLabel>
            <Select label="Поръчка">
              <MenuItem value="">-- Избери --</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Автомобил</InputLabel>
            <Select label="Автомобил">
              <MenuItem value="">-- Избери --</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Водач</InputLabel>
            <Select label="Водач">
              <MenuItem value="">-- Избери --</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Статус</InputLabel>
            <Select label="Статус" defaultValue="pending">
              <MenuItem value="pending">Чакаща</MenuItem>
              <MenuItem value="in_transit">В път</MenuItem>
              <MenuItem value="delivered">Доставена</MenuItem>
            </Select>
          </FormControl>
          <TextField margin="dense" label="Тракинг номер" fullWidth variant="outlined" />
          <TextField margin="dense" label="Забележки" fullWidth multiline rows={3} variant="outlined" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeliveriesOpen(false)}>Отказ</Button>
          <Button onClick={() => setDeliveriesOpen(false)} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LogisticsPage;
