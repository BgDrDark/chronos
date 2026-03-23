import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid,
  CircularProgress,
  Alert,
  Select,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  LocalShipping as SupplierIcon,
  Kitchen as ZoneIcon,
  Add as AddIcon,
  Edit as EditIcon,
  QrCode as QrCodeIcon,
  Warning as WarningIcon,
  QrCodeScanner as ScanIcon,
  Search as SearchIcon,
  RemoveShoppingCart as ConsumeIcon,
  History as HistoryIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import { CREATE_INGREDIENT, UPDATE_INGREDIENT, UPDATE_BATCH, CREATE_SUPPLIER, UPDATE_SUPPLIER, CREATE_STORAGE_ZONE, UPDATE_STORAGE_ZONE, UPDATE_BATCH_STATUS, START_INVENTORY_SESSION, ADD_INVENTORY_ITEM, COMPLETE_INVENTORY_SESSION, BULK_ADD_BATCHES } from '../graphql/confectioneryMutations';
import { ME_QUERY, INVENTORY_SESSIONS_QUERY, INVENTORY_SESSION_ITEMS_QUERY, INVENTORY_BY_BARCODE_QUERY, INGREDIENTS_QUERY } from '../graphql/queries';
import { CONSUME_FROM_BATCH, AUTO_CONSUME_FEFO, GET_FEFO_SUGGESTION, GET_CONSUMPTION_LOGS } from '../graphql/warehouseMutations';
import { getErrorMessage, type Ingredient, type Batch, type Supplier, type StorageZone, type InventorySession, type InventorySessionItem, type StockConsumptionLog, type FefoSuggestion } from '../types';
import { type SxProps, type Theme } from '@mui/material';

interface BatchItem {
  ingredientId: string;
  barcode: string;
  quantity: string;
  expiryDate: string;
  batchNumber: string;
  storageZoneId: string;
}

interface ValidatedTextFieldProps {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  tooltip?: string;
  placeholder?: string;
  error?: string;
  required?: boolean;
  type?: 'text' | 'number' | 'date';
  select?: boolean;
  children?: React.ReactNode;
  size?: 'small' | 'medium';
  fullWidth?: boolean;
  disabled?: boolean;
  multiline?: boolean;
  rows?: number;
  InputProps?: { sx?: object };
  sx?: SxProps<Theme>;
}

const ValidatedTextField: React.FC<ValidatedTextFieldProps> = ({
  label, value, onChange, tooltip, placeholder, error, required,
  type = 'text', select, children, size = 'small', fullWidth = true,
  disabled, multiline, rows, InputProps, sx
}) => {
  const showError = !!error;
  const hasValue = value !== '' && value !== null && value !== undefined;
  
  return (
    <Tooltip title={tooltip || ''} arrow placement="top">
      <TextField
        label={label}
        value={value}
        onChange={(e) => {
          if (type === 'number') {
            onChange(e.target.value.replace(/[^0-9.]/g, ''));
          } else {
            onChange(e.target.value);
          }
        }}
        placeholder={placeholder}
        error={showError}
        helperText={error}
        required={required}
        type={type}
        select={select}
        size={size}
        fullWidth={fullWidth}
        disabled={disabled}
        multiline={multiline}
        rows={rows}
        sx={sx}
        InputProps={{
          ...InputProps,
          sx: {
            ...InputProps?.sx,
            '& .MuiOutlinedInput-root': {
              '&.Mui-error': {
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'error.main',
                  borderWidth: 2,
                },
              },
              ...(hasValue && !showError && {
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'success.main',
                  borderWidth: 2,
                },
              }),
            },
          },
        }}
      >
        {children}
      </TextField>
    </Tooltip>
  );
};

const GET_WAREHOUSE_DATA = gql`
  query GetWarehouseData {
    ingredients {
      id
      name
      barcode
      unit
      currentStock
      baselineMinStock
      isPerishable
      expiryWarningDays
      productType
      storageZone {
        id
        name
      }
    }
    suppliers {
      id
      name
      contactPerson
      phone
      eik
      vatNumber
      address
      email
    }
    storageZones {
      id
      name
      tempMin
      tempMax
      description
      isActive
      assetType
      zoneType
    }
    batches(status: null) {
      id
      ingredientId
      batchNumber
      quantity
      expiryDate
      status
      receivedAt
      invoiceNumber
      ingredient {
        name
        unit
      }
      supplier {
        name
      }
    }
  }
`;

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const WarehousePage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [openIngredientModal, setOpenIngredientModal] = useState(false);
  const [openBatchModal, setOpenBatchModal] = useState(false);
  const [openSupplierModal, setOpenSupplierModal] = useState(false);
  const [openZoneModal, setOpenZoneModal] = useState(false);
  const [selectedIngredientId, setSelectedIngredientId] = useState<number | null>(null);
  const [batchFilterStatus, setBatchFilterStatus] = useState<string>('active');

  // Form states
  const [ingredientForm, setIngredientForm] = useState({
    name: '',
    unit: 'kg',
    barcode: '',
    storageZoneId: '',
    baselineMinStock: '0',
  });

  const [batchForm, setBatchForm] = useState({
    supplierId: '',
    invoiceNumber: '',
    invoiceDate: new Date().toISOString().split('T')[0],
    createInvoice: true,
    items: [] as BatchItem[],
  });

  const [currentBatchItem, setCurrentBatchItem] = useState<BatchItem>({
    ingredientId: '',
    barcode: '',
    quantity: '',
    expiryDate: '',
    batchNumber: '',
    storageZoneId: '',
  });

  const [supplierForm, setSupplierForm] = useState({
    name: '',
    contactPerson: '',
    phone: '',
    eik: '',
    vatNumber: '',
  });

  const [zoneForm, setZoneForm] = useState({
    name: '',
    tempMin: '',
    tempMax: '',
    description: '',
    isActive: true,
    assetType: 'KMA',
    zoneType: 'food',
  });

  // Edit forms
  const [editSupplierForm, setEditSupplierForm] = useState({
    id: 0,
    name: '',
    contactPerson: '',
    phone: '',
    eik: '',
    vatNumber: '',
    address: '',
    email: '',
  });

  const [editZoneForm, setEditZoneForm] = useState({
    id: 0,
    name: '',
    tempMin: '',
    tempMax: '',
    description: '',
    isActive: true,
    assetType: 'KMA',
    zoneType: 'food',
  });

  const [editIngredientForm, setEditIngredientForm] = useState({
    id: 0,
    name: '',
    unit: 'kg',
    barcode: '',
    storageZoneId: '',
    baselineMinStock: '0',
    productType: 'raw',
    isPerishable: true,
    expiryWarningDays: '3',
  });

  // Consumption tab state
  const [consumptionMode, setConsumptionMode] = useState<'fefo' | 'manual'>('fefo');
  const [consumptionIngredientId, setConsumptionIngredientId] = useState<string>('');
  const [consumptionQuantity, setConsumptionQuantity] = useState<string>('');
  const [consumptionReason, setConsumptionReason] = useState<string>('manual');
  const [consumptionNotes, setConsumptionNotes] = useState<string>('');
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [consumptionError, setConsumptionError] = useState<string | null>(null);
  const [consumptionSuccess, setConsumptionSuccess] = useState<string | null>(null);

  const [logFilters, setLogFilters] = useState({
    ingredientId: '',
    batchId: '',
    startDate: '',
    endDate: '',
  });

  // Validation state
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Validation functions
  const validateIngredient = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!ingredientForm.name || ingredientForm.name.trim().length < 2) {
      errors.name = 'Името трябва да е поне 2 символа';
    }
    if (!ingredientForm.unit) {
      errors.unit = 'Избери мерна единица';
    }
    if (ingredientForm.baselineMinStock && parseFloat(ingredientForm.baselineMinStock) < 0) {
      errors.baselineMinStock = 'Минималното количество не може да е отрицателно';
    }
    return errors;
  };

  const validateBatch = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!batchForm.supplierId) {
      errors.supplierId = 'Избери доставчик';
    }
    if (!batchForm.invoiceNumber) {
      errors.invoiceNumber = 'Въведи номер на фактура';
    }
    if (batchForm.items.length === 0) {
      errors.items = 'Добави поне един артикул';
    }
    return errors;
  };

  const validateSupplier = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!supplierForm.name || supplierForm.name.trim().length < 2) {
      errors.name = 'Името трябва да е поне 2 символа';
    }
    if (!supplierForm.eik || supplierForm.eik.trim().length < 9) {
      errors.eik = 'Въведи валиден ЕИК';
    }
    return errors;
  };

  const validateZone = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!zoneForm.name || zoneForm.name.trim().length < 2) {
      errors.name = 'Името трябва да е поне 2 символа';
    }
    if (zoneForm.tempMin && zoneForm.tempMax && parseFloat(zoneForm.tempMin) > parseFloat(zoneForm.tempMax)) {
      errors.tempMax = 'Макс. температура трябва да е > мин.';
    }
    return errors;
  };

  const validateEditSupplier = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!editSupplierForm.name || editSupplierForm.name.trim().length < 2) {
      errors.name = 'Името трябва да е поне 2 символа';
    }
    if (!editSupplierForm.eik || editSupplierForm.eik.trim().length < 9) {
      errors.eik = 'Въведи валиден ЕИК';
    }
    return errors;
  };

  const validateEditZone = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!editZoneForm.name || editZoneForm.name.trim().length < 2) {
      errors.name = 'Името трябва да е поне 2 символа';
    }
    if (editZoneForm.tempMin && editZoneForm.tempMax && parseFloat(editZoneForm.tempMin) > parseFloat(editZoneForm.tempMax)) {
      errors.tempMax = 'Макс. температура трябва да е > мин.';
    }
    return errors;
  };

  const validateEditIngredient = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!editIngredientForm.name || editIngredientForm.name.trim().length < 2) {
      errors.name = 'Името трябва да е поне 2 символа';
    }
    if (!editIngredientForm.unit) {
      errors.unit = 'Избери мерна единица';
    }
    return errors;
  };

  const validateEditBatch = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    if (!editBatchForm.quantity || parseFloat(editBatchForm.quantity) <= 0) {
      errors.quantity = 'Количеството трябва да е > 0';
    }
    if (!editBatchForm.expiryDate) {
      errors.expiryDate = 'Въведи срок на годност';
    }
    return errors;
  };

  const { data, loading, error, refetch } = useQuery(GET_WAREHOUSE_DATA);
  
  // Auto-select ingredient when barcode is entered in current batch item form
  useEffect(() => {
    if (currentBatchItem.barcode && data?.ingredients) {
      const found = data.ingredients.find((i: Ingredient) => i.barcode === currentBatchItem.barcode);
      if (found) {
        setCurrentBatchItem(prev => ({ ...prev, ingredientId: found.id.toString(), storageZoneId: found.storageZone?.id?.toString() || prev.storageZoneId }));
      }
    }
  }, [currentBatchItem.barcode, data]);
  
  const { data: ingredientsData } = useQuery(INGREDIENTS_QUERY);
  const [createIngredient] = useMutation(CREATE_INGREDIENT);
  const [createSupplier] = useMutation(CREATE_SUPPLIER);
  const [updateSupplier] = useMutation(UPDATE_SUPPLIER);
  const [createZone] = useMutation(CREATE_STORAGE_ZONE);
  const [updateZone] = useMutation(UPDATE_STORAGE_ZONE);
  
  // Edit states
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [editingZone, setEditingZone] = useState<StorageZone | null>(null);
  const [editingIngredient, setEditingIngredient] = useState<Ingredient | null>(null);
  const [editingBatch, setEditingBatch] = useState<Batch | null>(null);
  const [updateBatchStatus] = useMutation(UPDATE_BATCH_STATUS);
  const [updateBatch] = useMutation(UPDATE_BATCH);
  const [updateIngredient] = useMutation(UPDATE_INGREDIENT);
  const [bulkAddBatches] = useMutation(BULK_ADD_BATCHES);
  
  // Edit batch form
  const [editBatchForm, setEditBatchForm] = useState({
    id: 0,
    ingredientId: '',
    quantity: '',
    expiryDate: '',
    supplierId: '',
    invoiceNumber: '',
    batchNumber: '',
    storageZoneId: '',
  });
  
  // Scanner target: 'ingredient' | 'batch' | null
  const [scannerTarget, setScannerTarget] = useState<'ingredient' | 'batch' | null>(null);
  
  // Inventory mutations
  const [startInventorySession] = useMutation(START_INVENTORY_SESSION);
  const [addInventoryItem] = useMutation(ADD_INVENTORY_ITEM);
  const [completeInventorySession] = useMutation(COMPLETE_INVENTORY_SESSION);
  
  const { data: inventorySessionsData, refetch: refetchInventory } = useQuery(INVENTORY_SESSIONS_QUERY);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const { data: sessionItemsData, refetch: refetchSessionItems } = useQuery(INVENTORY_SESSION_ITEMS_QUERY, {
    variables: { sessionId: currentSessionId },
    skip: !currentSessionId
  });
  const [inventorySearch, setInventorySearch] = useState<string>('');
  const [inventoryQuantity, setInventoryQuantity] = useState<string>('');

  // Consumption mutations
  const [consumeFromBatch] = useMutation(CONSUME_FROM_BATCH);
  const [autoConsumeFefo] = useMutation(AUTO_CONSUME_FEFO);

  // Consumption queries
  const { data: fefoData } = useQuery(GET_FEFO_SUGGESTION, {
    variables: { ingredientId: parseInt(consumptionIngredientId) || 0, quantity: parseFloat(consumptionQuantity) || 0 },
    skip: !consumptionIngredientId || !consumptionQuantity || parseFloat(consumptionQuantity) <= 0,
    fetchPolicy: 'network-only',
  });

  const { data: logsData, refetch: refetchLogs, loading: logsLoading } = useQuery(GET_CONSUMPTION_LOGS, {
    variables: {
      ingredientId: logFilters.ingredientId ? parseInt(logFilters.ingredientId) : undefined,
      batchId: logFilters.batchId ? parseInt(logFilters.batchId) : undefined,
      startDate: logFilters.startDate || undefined,
      endDate: logFilters.endDate || undefined,
    },
    fetchPolicy: 'cache-and-network',
  });

  const { data: barcodeData } = useQuery(INVENTORY_BY_BARCODE_QUERY, {
    variables: { barcode: inventorySearch || '' },
    skip: !inventorySearch || inventorySearch.length < 3
  });
  const [updatingBatchId, setUpdatingBatchId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [scannerOpen, setScannerOpen] = useState(false);
  const [foundIngredient, setFoundIngredient] = useState<Ingredient | null>(null);
  const scannerRef = useRef<Html5Qrcode | null>(null);

  const stopScanner = useCallback(async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();
        scannerRef.current = null;
      } catch (e) {
        console.error('Error stopping scanner:', e);
      }
    }
    setScannerOpen(false);
    setScannerTarget(null);
  }, []);

  const handleBarcodeFound = useCallback((barcode: string) => {
    setSearchQuery(barcode);
    setScannerOpen(false);
    
    if (scannerTarget === 'ingredient') {
      setIngredientForm({ ...ingredientForm, barcode });
    } else if (scannerTarget === 'batch') {
      const ingredient = data?.ingredients?.find((i: Ingredient) => i.barcode === barcode);
      if (ingredient) {
        setCurrentBatchItem({ ...currentBatchItem, ingredientId: ingredient.id.toString(), barcode, storageZoneId: ingredient.storageZone?.id?.toString() || '' });
      } else {
        setCurrentBatchItem({ ...currentBatchItem, barcode });
      }
    }
    setScannerTarget(null);
  }, [ingredientForm, scannerTarget, data, currentBatchItem]);

  // Start scanner when dialog opens
  useEffect(() => {
    if (scannerOpen && !scannerRef.current) {
      const onScanSuccess = (decodedText: string) => {
        handleBarcodeFound(decodedText);
        stopScanner();
      };
      
      scannerRef.current = new Html5Qrcode('barcode-scanner');
      scannerRef.current.start(
        { facingMode: 'environment' },
        { fps: 5, qrbox: { width: 250, height: 150 } },
        onScanSuccess,
        () => {}
      ).catch(err => console.error('Scanner start error:', err));
    }
    
    return () => {
      if (scannerRef.current) {
        scannerRef.current.stop().then(() => {
          scannerRef.current = null;
        }).catch(console.error);
      }
    };
  }, [scannerOpen, handleBarcodeFound, stopScanner]);

  const openScannerFor = (target: 'ingredient' | 'batch') => {
    setScannerTarget(target);
    setScannerOpen(true);
  };

  const filteredIngredients = data?.ingredients?.filter((i: Ingredient) => 
    !searchQuery || 
    i.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    i.barcode === searchQuery
  ) || [];

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const { data: loadingData, loading: loadingUser } = useQuery(ME_QUERY);
  const user = loadingData?.me;

  const handleAddIngredient = async () => {
    const errors = validateIngredient();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    
    if (!user?.companyId) return;
    try {
      await createIngredient({
        variables: {
          input: {
            name: ingredientForm.name,
            unit: ingredientForm.unit,
            barcode: ingredientForm.barcode || null,
            storageZoneId: ingredientForm.storageZoneId ? parseInt(ingredientForm.storageZoneId) : null,
            baselineMinStock: parseFloat(ingredientForm.baselineMinStock),
            companyId: user.companyId,
          },
        },
      });
      setOpenIngredientModal(false);
      setIngredientForm({ name: '', unit: 'kg', barcode: '', storageZoneId: '', baselineMinStock: '0' });
      setValidationErrors({});
      refetch();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  };

  const handleAddItemToBatch = () => {
    if (!currentBatchItem.ingredientId || !currentBatchItem.quantity || !currentBatchItem.expiryDate) {
      alert('Моля попълнете всички задължителни полета за артикула (продукт, количество, срок на годност)');
      return;
    }
    setBatchForm({
      ...batchForm,
      items: [...batchForm.items, { ...currentBatchItem }]
    });
    setCurrentBatchItem({
      ingredientId: '',
      barcode: '',
      quantity: '',
      expiryDate: '',
      batchNumber: '',
      storageZoneId: '',
    });
  };

  const handleRemoveItemFromBatch = (index: number) => {
    const newItems = [...batchForm.items];
    newItems.splice(index, 1);
    setBatchForm({ ...batchForm, items: newItems });
  };

  const handleAddBatch = async () => {
    const errors = validateBatch();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    
    try {
      await bulkAddBatches({
        variables: {
          invoiceNumber: batchForm.invoiceNumber,
          supplierId: parseInt(batchForm.supplierId),
          date: batchForm.invoiceDate,
          createInvoice: batchForm.createInvoice,
          items: batchForm.items.map(item => ({
            ingredientId: parseInt(item.ingredientId),
            quantity: parseFloat(item.quantity),
            expiryDate: item.expiryDate,
            batchNumber: item.batchNumber || null,
            storageZoneId: item.storageZoneId ? parseInt(item.storageZoneId) : null,
          })),
        },
      });
      
      setOpenBatchModal(false);
      setBatchForm({ 
        supplierId: '', 
        invoiceNumber: '', 
        invoiceDate: new Date().toISOString().split('T')[0], 
        createInvoice: true, 
        items: [] 
      });
      setValidationErrors({});
      refetch();
      alert('Успешно заприходени артикули!');
    } catch (err) {
      console.error(err);
      alert('Грешка при запис на данните');
    }
  };

  const handleAddSupplier = async () => {
    const errors = validateSupplier();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    
    if (!user?.companyId) return;
    try {
      await createSupplier({
        variables: {
          input: {
            name: supplierForm.name,
            contactPerson: supplierForm.contactPerson,
            phone: supplierForm.phone,
            eik: supplierForm.eik,
            vatNumber: supplierForm.vatNumber,
            companyId: user.companyId,
          },
        },
      });
      setOpenSupplierModal(false);
      setSupplierForm({ name: '', contactPerson: '', phone: '', eik: '', vatNumber: '' });
      setValidationErrors({});
      refetch();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  };

  const handleAddZone = async () => {
    const errors = validateZone();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    
    if (!user?.companyId) return;
    try {
      await createZone({
        variables: {
          input: {
            name: zoneForm.name,
            tempMin: zoneForm.tempMin ? parseFloat(zoneForm.tempMin) : null,
            tempMax: zoneForm.tempMax ? parseFloat(zoneForm.tempMax) : null,
            description: zoneForm.description,
            companyId: user.companyId,
            isActive: zoneForm.isActive,
            assetType: zoneForm.assetType,
            zoneType: zoneForm.zoneType,
          },
        },
      });
      setOpenZoneModal(false);
      setZoneForm({ name: '', tempMin: '', tempMax: '', description: '', isActive: true, assetType: 'KMA', zoneType: 'food' });
      setValidationErrors({});
      refetch();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  };

  const handleUpdateSupplier = async () => {
    const errors = validateEditSupplier();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    
    try {
      await updateSupplier({
        variables: {
          input: {
            id: editSupplierForm.id,
            name: editSupplierForm.name,
            contactPerson: editSupplierForm.contactPerson,
            phone: editSupplierForm.phone,
            eik: editSupplierForm.eik,
            vatNumber: editSupplierForm.vatNumber,
            address: editSupplierForm.address,
            email: editSupplierForm.email,
          },
        },
      });
      setEditingSupplier(null);
      setValidationErrors({});
      refetch();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  };

  const handleUpdateZone = async () => {
    const errors = validateEditZone();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    
    try {
      await updateZone({
        variables: {
          input: {
            id: editZoneForm.id,
            name: editZoneForm.name,
            tempMin: editZoneForm.tempMin ? parseFloat(editZoneForm.tempMin) : null,
            tempMax: editZoneForm.tempMax ? parseFloat(editZoneForm.tempMax) : null,
            description: editZoneForm.description,
            isActive: editZoneForm.isActive,
            assetType: editZoneForm.assetType,
            zoneType: editZoneForm.zoneType,
          },
        },
      });
      setEditingZone(null);
      setValidationErrors({});
      refetch();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  };

  // Open edit modals with data
  useEffect(() => {
    if (editingSupplier) {
      setEditSupplierForm({
        id: editingSupplier.id,
        name: editingSupplier.name || '',
        contactPerson: editingSupplier.contactPerson || '',
        phone: editingSupplier.phone || '',
        eik: editingSupplier.eik || '',
        vatNumber: editingSupplier.vatNumber || '',
        address: editingSupplier.address || '',
        email: editingSupplier.email || '',
      });
    }
  }, [editingSupplier]);

  useEffect(() => {
    if (editingZone) {
      setEditZoneForm({
        id: editingZone.id,
        name: editingZone.name || '',
        tempMin: editingZone.tempMin != null ? String(editingZone.tempMin) : '',
        tempMax: editingZone.tempMax != null ? String(editingZone.tempMax) : '',
        description: editingZone.description || '',
        isActive: editingZone.isActive ?? true,
        assetType: editingZone.assetType || 'KMA',
        zoneType: editingZone.zoneType || 'food',
      });
    }
  }, [editingZone]);

  useEffect(() => {
    if (editingIngredient) {
      setEditIngredientForm({
        id: editingIngredient.id,
        name: editingIngredient.name || '',
        unit: editingIngredient.unit || 'kg',
        barcode: editingIngredient.barcode || '',
        storageZoneId: editingIngredient.storageZone?.id?.toString() || '',
        baselineMinStock: editingIngredient.baselineMinStock?.toString() || '0',
        productType: editingIngredient.productType || 'raw',
        isPerishable: editingIngredient.isPerishable ?? true,
        expiryWarningDays: editingIngredient.expiryWarningDays?.toString() || '3',
      });
    }
  }, [editingIngredient]);

  const handleUpdateIngredient = async () => {
    const errors = validateEditIngredient();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    
    if (!user?.companyId) return;
    try {
      await updateIngredient({
        variables: {
          input: {
            id: editIngredientForm.id,
            name: editIngredientForm.name,
            unit: editIngredientForm.unit,
            barcode: editIngredientForm.barcode || null,
            storageZoneId: editIngredientForm.storageZoneId ? parseInt(editIngredientForm.storageZoneId) : null,
            baselineMinStock: parseFloat(editIngredientForm.baselineMinStock),
            productType: editIngredientForm.productType,
            isPerishable: editIngredientForm.isPerishable,
            expiryWarningDays: parseInt(editIngredientForm.expiryWarningDays),
            companyId: user.companyId,
          },
        },
      });
      setEditingIngredient(null);
      setValidationErrors({});
      refetch();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  };

  const handleBatchStatusChange = async (batchId: number, newStatus: string) => {
    try {
      setUpdatingBatchId(batchId);
      await updateBatchStatus({
        variables: {
          id: batchId,
          status: newStatus
        }
      });
      refetch();
    } catch (err) {
      alert(getErrorMessage(err));
    } finally {
      setUpdatingBatchId(null);
    }
  };

  useEffect(() => {
    if (editingBatch) {
      setEditBatchForm({
        id: editingBatch.id,
        ingredientId: editingBatch.ingredientId?.toString() || '',
        quantity: editingBatch.quantity?.toString() || '',
        expiryDate: editingBatch.expiryDate ? editingBatch.expiryDate.split('T')[0] : '',
        supplierId: editingBatch.supplier?.id?.toString() || '',
        invoiceNumber: editingBatch.invoiceNumber || '',
        batchNumber: editingBatch.batchNumber || '',
        storageZoneId: editingBatch.storageZoneId?.toString() || '',
      });
    }
  }, [editingBatch]);

  const handleUpdateBatch = async () => {
    const errors = validateEditBatch();
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) return;
    
    try {
      await updateBatch({
        variables: {
          input: {
            id: editBatchForm.id,
            ingredientId: parseInt(editBatchForm.ingredientId),
            quantity: parseFloat(editBatchForm.quantity),
            expiryDate: editBatchForm.expiryDate,
            supplierId: editBatchForm.supplierId ? parseInt(editBatchForm.supplierId) : null,
            invoiceNumber: editBatchForm.invoiceNumber || null,
            batchNumber: editBatchForm.batchNumber || null,
            storageZoneId: editBatchForm.storageZoneId ? parseInt(editBatchForm.storageZoneId) : null,
          },
        },
      });
      setEditingBatch(null);
      setValidationErrors({});
      refetch();
    } catch (err) {
      alert(getErrorMessage(err));
    }
  };

  // Consumption handlers
  const handleConsumeFefo = async () => {
    if (!consumptionIngredientId || !consumptionQuantity) {
      setConsumptionError('Моля, изберете артикул и въведете количество');
      return;
    }

    const qty = parseFloat(consumptionQuantity);
    if (qty <= 0) {
      setConsumptionError('Количеството трябва да е по-голямо от 0');
      return;
    }

    try {
      setConsumptionError(null);
      await autoConsumeFefo({
        variables: {
          ingredientId: parseInt(consumptionIngredientId),
          quantity: qty,
          reason: consumptionReason,
          notes: consumptionNotes || null,
        },
      });

      setConsumptionSuccess(`Успешно изразходвани ${qty} бр.`);
      setConsumptionQuantity('');
      setConsumptionNotes('');
      setConsumptionReason('manual');
      refetch();
      refetchLogs();
    } catch (err) {
      setConsumptionError(getErrorMessage(err));
    }
  };

  const handleConsumeManual = async () => {
    if (!selectedBatchId || !consumptionQuantity) {
      setConsumptionError('Моля, изберете партида и въведете количество');
      return;
    }

    const qty = parseFloat(consumptionQuantity);
    if (qty <= 0) {
      setConsumptionError('Количеството трябва да е по-голямо от 0');
      return;
    }

    try {
      setConsumptionError(null);
      await consumeFromBatch({
        variables: {
          batchId: selectedBatchId,
          quantity: qty,
          reason: consumptionReason,
          notes: consumptionNotes || null,
        },
      });

      setConsumptionSuccess(`Успешно изразходвани ${qty} бр. от партида`);
      setConsumptionQuantity('');
      setConsumptionNotes('');
      setSelectedBatchId(null);
      refetch();
      refetchLogs();
    } catch (err) {
      setConsumptionError(getErrorMessage(err));
    }
  };

  const handleSelectBatch = (batchId: number) => {
    setSelectedBatchId(batchId);
  };

  const clearConsumptionMessages = () => {
    setConsumptionError(null);
    setConsumptionSuccess(null);
  };

  if (loading || loadingUser) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  if (error) return <Typography color="error">Грешка при зареждане на данните: {error.message}</Typography>;

  if (!user?.companyId && user?.role?.name !== 'super_admin') {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="warning">
          Вашият профил не е свързан с фирма. Моля, свържете се с администратор или първо създайте фирма.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Управление на Склад
        </Typography>
        <Box>
          <Tooltip title="Добави нов продукт в склада (Ctrl+F1)" arrow>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              sx={{ mr: 1 }}
              onClick={() => setOpenIngredientModal(true)}
            >
              Нов Продукт
            </Button>
          </Tooltip>
          <Tooltip title="Приеми нова стока от доставчик (Ctrl+F2)" arrow>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              color="primary"
              onClick={() => setOpenBatchModal(true)}
            >
              Прием на стока
            </Button>
          </Tooltip>
        </Box>
      </Box>

      {/* Search Bar with Scanner */}
      <Paper sx={{ p: 2, mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
        <SearchIcon color="action" />
        <TextField
          fullWidth
          placeholder="Търси по име или баркод..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          size="small"
        />
        <Tooltip title="Отвори скенера за баркод (Ctrl+S)" arrow>
          <IconButton color="primary" onClick={() => setScannerOpen(true)}>
            <ScanIcon />
          </IconButton>
        </Tooltip>
      </Paper>

      {/* Found Ingredient Alert */}
      {foundIngredient && (
        <Alert severity="info" sx={{ mb: 2 }} onClose={() => setFoundIngredient(null)}>
          Намерен продукт: <strong>{foundIngredient.name}</strong> - 
          Наличност: {foundIngredient.currentStock} {foundIngredient.unit}
        </Alert>
      )}

      {/* Statistics Dashboard */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#e3f2fd' }}>
            <Typography variant="h4" color="primary">{data?.ingredients?.length || 0}</Typography>
            <Typography variant="body2">Продукти</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#fff3e0' }}>
            <Typography variant="h4" color="warning.main">
              {data?.ingredients?.filter((i: Ingredient) => parseFloat(i.currentStock.toString()) <= parseFloat(i.baselineMinStock.toString())).length || 0}
            </Typography>
            <Typography variant="body2">Ниска наличност</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#fce4ec' }}>
            <Typography variant="h4" color="error.main">
              {data?.batches?.filter((b: Batch) => b.expiryDate && new Date(b.expiryDate) < new Date()).length || 0}
            </Typography>
            <Typography variant="body2">Изтекли партиди</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#e8f5e9' }}>
            <Typography variant="h4" color="success.main">{data?.suppliers?.length || 0}</Typography>
            <Typography variant="body2">Доставчици</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Main Tabs Content */}
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          centered
        >
          <Tab icon={<InventoryIcon />} label="Наличности" />
          <Tab icon={<QrCodeIcon />} label="Партиди" />
          <Tab icon={<ConsumeIcon />} label="Изразходване" />
          <Tab icon={<SupplierIcon />} label="Доставчици" />
          <Tab icon={<ZoneIcon />} label="Зони за съхранение" />
          <Tab icon={<ScanIcon />} label="Инвентаризация" />
        </Tabs>
        {/* Наличности */}
        <TabPanel value={tabValue} index={0}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Продукт</TableCell>
                  <TableCell>Зона</TableCell>
                  <TableCell align="right">Наличност</TableCell>
                  <TableCell align="right">Мин. Лимит</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredIngredients.map((item: Ingredient) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                        {item.name}
                      </Typography>
                    </TableCell>
                    <TableCell>{item.storageZone?.name || 'Няма зона'}</TableCell>
                    <TableCell align="right">
                      {item.currentStock} {item.unit}
                    </TableCell>
                    <TableCell align="right">
                      {item.baselineMinStock} {item.unit}
                    </TableCell>
                    <TableCell>
                      {Number(item.currentStock) <= Number(item.baselineMinStock) ? (
                        <Chip
                          icon={<WarningIcon />}
                          label="Ниска наличност"
                          color="warning"
                          size="small"
                        />
                      ) : (
                        <Chip label="В норма" color="success" size="small" />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Редактирай">
                        <IconButton size="small" onClick={() => setEditingIngredient(item)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Button size="small" onClick={() => { setSelectedIngredientId(item.id); setTabValue(1); }}>
                        Партиди
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
        {/* Партиди */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Филтрирай по продукт</InputLabel>
              <Select
                value={selectedIngredientId || ''}
                onChange={(e) => setSelectedIngredientId(e.target.value ? Number(e.target.value) : null)}
                label="Филтрирай по продукт"
              >
                <MenuItem value="">Всички продукти</MenuItem>
                {data?.ingredients.map((ing: Ingredient) => (
                  <MenuItem key={ing.id} value={ing.id}>{ing.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Статус</InputLabel>
              <Select
                value={batchFilterStatus}
                onChange={(e) => setBatchFilterStatus(e.target.value)}
                label="Статус"
              >
                <MenuItem value="active">Активни</MenuItem>
                <MenuItem value="quarantined">Карантина</MenuItem>
                <MenuItem value="expired">Изтекли</MenuItem>
                <MenuItem value="depleted">Изчерпани</MenuItem>
                <MenuItem value="scrap">Брак</MenuItem>
              </Select>
            </FormControl>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Продукт</TableCell>
                  <TableCell>Партида №</TableCell>
                  <TableCell align="right">Количество</TableCell>
                  <TableCell>Годност до</TableCell>
                  <TableCell>Доставчик</TableCell>
                  <TableCell>Фактура</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.batches
                  .filter((b: Batch) => !selectedIngredientId || b.ingredientId === selectedIngredientId)
                  .filter((b: Batch) => b.status === batchFilterStatus)
                  .map((batch: Batch) => {
                    const expiryDate = batch.expiryDate ? new Date(batch.expiryDate) : null;
                    const isExpired = expiryDate ? expiryDate < new Date() : false;
                    return (
                      <TableRow key={batch.id} sx={isExpired ? { backgroundColor: '#fff3e0' } : {}}>
                        <TableCell>{batch.ingredient?.name}</TableCell>
                        <TableCell>{batch.batchNumber || '-'}</TableCell>
                        <TableCell align="right">{batch.quantity} {batch.ingredient?.unit}</TableCell>
                        <TableCell>
                          {expiryDate ? expiryDate.toLocaleDateString('bg-BG') : '-'}
                          {isExpired && <Chip label="Изтекъл" color="error" size="small" sx={{ ml: 1 }} />}
                        </TableCell>
                        <TableCell>{batch.supplier?.name || '-'}</TableCell>
                        <TableCell>{batch.invoiceNumber || '-'}</TableCell>
                        <TableCell>
                          <Select
                            value={batch.status}
                            size="small"
                            disabled={updatingBatchId === batch.id}
                            onChange={(e) => handleBatchStatusChange(batch.id, e.target.value)}
                            sx={{ minWidth: 120 }}
                          >
                            <MenuItem value="active">Активна</MenuItem>
                            <MenuItem value="quarantined">Карантина</MenuItem>
                            <MenuItem value="expired">Изтекла</MenuItem>
                            <MenuItem value="depleted">Изчерпана</MenuItem>
                            <MenuItem value="scrap">Брак</MenuItem>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="Редактирай">
                            <IconButton size="small" onClick={() => setEditingBatch(batch)}>
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    );
                  })}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
        {/* Изразходване */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ p: 2 }}>
            {consumptionError && (
              <Alert severity="error" onClose={clearConsumptionMessages} sx={{ mb: 2 }}>
                {consumptionError}
              </Alert>
            )}
            {consumptionSuccess && (
              <Alert severity="success" onClose={clearConsumptionMessages} sx={{ mb: 2 }}>
                {consumptionSuccess}
              </Alert>
            )}

            {/* Mode Selection */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>Режим на изразходване</Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant={consumptionMode === 'fefo' ? 'contained' : 'outlined'}
                  startIcon={<TrendingDownIcon />}
                  onClick={() => setConsumptionMode('fefo')}
                >
                  Автоматично (FEFO)
                </Button>
                <Button
                  variant={consumptionMode === 'manual' ? 'contained' : 'outlined'}
                  startIcon={<QrCodeIcon />}
                  onClick={() => setConsumptionMode('manual')}
                >
                  Ръчно (по партида)
                </Button>
              </Box>
            </Box>

            <Grid container spacing={3}>
              {/* Left Column - Form */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle1" sx={{ mb: 2 }}>
                    {consumptionMode === 'fefo' ? 'Автоматично изразходване (FEFO)' : 'Ръчно изразходване'}
                  </Typography>

                  {/* Ingredient Selection */}
                  <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                    <InputLabel>Артикул</InputLabel>
                    <Select
                      value={consumptionIngredientId}
                      label="Артикул"
                      onChange={(e) => setConsumptionIngredientId(e.target.value)}
                    >
                      {data?.ingredients.map((ing: Ingredient) => (
                        <MenuItem key={ing.id} value={ing.id}>
                          {ing.name} ({ing.currentStock} {ing.unit})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {/* Quantity */}
                  <TextField
                    fullWidth
                    size="small"
                    label="Количество"
                    type="number"
                    value={consumptionQuantity}
                    onChange={(e) => setConsumptionQuantity(e.target.value)}
                    sx={{ mb: 2 }}
                    inputProps={{ min: 0, step: 0.001 }}
                  />

                  {/* Reason */}
                  <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                    <InputLabel>Причина</InputLabel>
                    <Select
                      value={consumptionReason}
                      label="Причина"
                      onChange={(e) => setConsumptionReason(e.target.value)}
                    >
                      <MenuItem value="manual">Ръчно</MenuItem>
                      <MenuItem value="production">Производство</MenuItem>
                      <MenuItem value="expiry">Изтекъл срок</MenuItem>
                      <MenuItem value="damaged">Повредено</MenuItem>
                      <MenuItem value="quality_check">Качествена проверка</MenuItem>
                    </Select>
                  </FormControl>

                  {/* Notes */}
                  <TextField
                    fullWidth
                    size="small"
                    label="Бележки"
                    multiline
                    rows={2}
                    value={consumptionNotes}
                    onChange={(e) => setConsumptionNotes(e.target.value)}
                    sx={{ mb: 2 }}
                  />

                  {/* Execute Button */}
                  <Button
                    fullWidth
                    variant="contained"
                    color="warning"
                    onClick={consumptionMode === 'fefo' ? handleConsumeFefo : handleConsumeManual}
                    disabled={!consumptionIngredientId || !consumptionQuantity}
                  >
                    Изразходвай
                  </Button>
                </Paper>
              </Grid>

              {/* Right Column - FEFO Suggestions or Batch Selection */}
              <Grid size={{ xs: 12, md: 6 }}>
                {consumptionMode === 'fefo' ? (
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" sx={{ mb: 2 }}>
                      FEFO предложение
                    </Typography>
                    {!consumptionIngredientId || !consumptionQuantity ? (
                      <Typography color="text.secondary">
                        Изберете артикул и въведете количество за да видите предложение
                      </Typography>
                    ) : fefoData?.getFefoSuggestion?.length === 0 ? (
                      <Typography color="warning.main">
                        Няма налични партиди за този артикул
                      </Typography>
                    ) : (
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Партида</TableCell>
                              <TableCell align="right">Налично</TableCell>
                              <TableCell align="right">Ще се вземе</TableCell>
                              <TableCell>Срок годност</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {fefoData?.getFefoSuggestion?.map((s: FefoSuggestion, idx: number) => (
                              <TableRow key={idx}>
                                <TableCell>{s.batchNumber}</TableCell>
                                <TableCell align="right">{s.availableQuantity.toFixed(3)}</TableCell>
                                <TableCell align="right">{s.quantityToTake.toFixed(3)}</TableCell>
                                <TableCell>
                                  <Chip
                                    size="small"
                                    label={`${s.daysUntilExpiry} дни`}
                                    color={s.daysUntilExpiry <= 7 ? 'error' : s.daysUntilExpiry <= 30 ? 'warning' : 'default'}
                                  />
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    )}
                  </Paper>
                ) : (
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" sx={{ mb: 2 }}>
                      Избор на партида
                    </Typography>
                    {!consumptionIngredientId ? (
                      <Typography color="text.secondary">
                        Първо изберете артикул
                      </Typography>
                    ) : (
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Партида</TableCell>
                              <TableCell align="right">Количество</TableCell>
                              <TableCell>Срок годност</TableCell>
                              <TableCell>Избери</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {data?.batches
                              ?.filter((b: Batch) => 
                                b.ingredientId === parseInt(consumptionIngredientId) && 
                                b.status === 'active' && 
                                Number(b.quantity) > 0
                              )
                              .map((b: Batch) => (
                                <TableRow 
                                  key={b.id}
                                  sx={{ 
                                    bgcolor: selectedBatchId === b.id ? 'action.selected' : 'inherit',
                                    cursor: 'pointer'
                                  }}
                                  onClick={() => handleSelectBatch(b.id)}
                                >
                                  <TableCell>{b.batchNumber}</TableCell>
                                  <TableCell align="right">{Number(b.quantity).toFixed(3)}</TableCell>
                                  <TableCell>
                                    {b.expiryDate ? new Date(b.expiryDate).toLocaleDateString('bg-BG') : '-'}
                                  </TableCell>
                                  <TableCell>
                                    <Chip 
                                      size="small" 
                                      label={selectedBatchId === b.id ? 'Избрана' : 'Избери'} 
                                      color={selectedBatchId === b.id ? 'primary' : 'default'}
                                    />
                                  </TableCell>
                                </TableRow>
                              ))}
                            {data?.batches?.filter((b: Batch) => 
                              b.ingredientId === parseInt(consumptionIngredientId) && 
                              b.status === 'active' && 
                              Number(b.quantity) > 0
                            ).length === 0 && (
                              <TableRow>
                                <TableCell colSpan={4} align="center">
                                  Няма налични партиди
                                </TableCell>
                              </TableRow>
                            )}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    )}
                  </Paper>
                )}
              </Grid>
            </Grid>

            {/* Consumption History */}
            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                <HistoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                История на изразходванията
              </Typography>

              {/* Filters */}
              <Paper sx={{ p: 2, mb: 2 }}>
                <Grid container spacing={2} alignItems="center">
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <TextField
                      fullWidth
                      size="small"
                      label="От дата"
                      type="date"
                      InputLabelProps={{ shrink: true }}
                      value={logFilters.startDate}
                      onChange={(e) => setLogFilters({ ...logFilters, startDate: e.target.value })}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <TextField
                      fullWidth
                      size="small"
                      label="До дата"
                      type="date"
                      InputLabelProps={{ shrink: true }}
                      value={logFilters.endDate}
                      onChange={(e) => setLogFilters({ ...logFilters, endDate: e.target.value })}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Филтрирай по артикул</InputLabel>
                      <Select
                        value={logFilters.ingredientId}
                        label="Филтрирай по артикул"
                        onChange={(e) => setLogFilters({ ...logFilters, ingredientId: e.target.value })}
                      >
                        <MenuItem value="">Всички</MenuItem>
                        {data?.ingredients.map((ing: Ingredient) => (
                          <MenuItem key={ing.id} value={ing.id}>{ing.name}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <Button fullWidth variant="outlined" onClick={() => refetchLogs()}>
                      Обнови
                    </Button>
                  </Grid>
                </Grid>
              </Paper>

              {logsLoading ? (
                <CircularProgress />
              ) : (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Дата</TableCell>
                        <TableCell>Артикул</TableCell>
                        <TableCell>Партида</TableCell>
                        <TableCell align="right">Количество</TableCell>
                        <TableCell>Причина</TableCell>
                        <TableCell>Потребител</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {logsData?.stockConsumptionLogs?.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} align="center">
                            Няма записи за изразходване
                          </TableCell>
                        </TableRow>
                      ) : (
                        logsData?.stockConsumptionLogs?.map((log: StockConsumptionLog) => (
                          <TableRow key={log.id}>
                            <TableCell>
                              {new Date(log.createdAt).toLocaleString('bg-BG')}
                            </TableCell>
                            <TableCell>{log.ingredient?.name || '-'}</TableCell>
                            <TableCell>{log.batch?.batchNumber || '-'}</TableCell>
                            <TableCell align="right">
                              <Typography color="error.main" fontWeight="bold">
                                -{log.quantity.toFixed(3)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip 
                                size="small" 
                                label={
                                  log.reason === 'manual' ? 'Ръчно' :
                                  log.reason === 'production' ? 'Производство' :
                                  log.reason === 'expiry' ? 'Изтекъл срок' :
                                  log.reason === 'damaged' ? 'Повредено' :
                                  log.reason === 'quality_check' ? 'Качествена проверка' :
                                  log.reason
                                }
                              />
                            </TableCell>
                            <TableCell>
                              {log.creator?.firstName} {log.creator?.lastName}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          </Box>
        </TabPanel>
        {/* Доставчици */}
        <TabPanel value={tabValue} index={3}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Фирма</TableCell>
                  <TableCell>Лице за контакт</TableCell>
                  <TableCell>Телефон</TableCell>
                  <TableCell>ЕИК / ДДС</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.suppliers.map((s: Supplier) => (
                  <TableRow key={s.id}>
                    <TableCell>{s.name}</TableCell>
                    <TableCell>{s.contactPerson}</TableCell>
                    <TableCell>{s.phone}</TableCell>
                    <TableCell>
                      <Typography variant="caption">{s.eik} / {s.vatNumber}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Редактирай">
                        <IconButton size="small" onClick={() => setEditingSupplier(s)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Box sx={{ mt: 2 }}>
            <Tooltip title="Добави нов доставчик (Ctrl+F5)" arrow>
              <Button startIcon={<AddIcon />} onClick={() => setOpenSupplierModal(true)}>
                Добави Доставчик
              </Button>
            </Tooltip>
          </Box>
        </TabPanel>
        {/* Зони за съхранение */}
        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={2}>
            {data?.storageZones.map((z: StorageZone) => (
              <Grid size={{ xs: 12, sm: 4 }} key={z.id}>
                <Paper variant="outlined" sx={{ p: 2, position: 'relative' }}>
                  <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
                    <Tooltip title="Редактирай">
                      <IconButton size="small" onClick={() => setEditingZone(z)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                    <Chip 
                      label={z.zoneType === 'food' ? 'Хранителен' : 'Нехранителен'} 
                      size="small" 
                      color={z.zoneType === 'food' ? 'success' : 'default'} 
                    />
                    <Chip 
                      label={z.assetType === 'KMA' ? 'КМА' : 'ДМА'} 
                      size="small" 
                      variant="outlined"
                    />
                    {!z.isActive && <Chip label="Неактивна" size="small" color="error" />}
                  </Box>
                  <Typography variant="h6" color="primary">{z.name}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Режим: {z.tempMin}°C до {z.tempMax}°C
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {z.description}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
          <Box sx={{ mt: 2 }}>
            <Tooltip title="Създай нова зона за съхранение (Ctrl+F6)" arrow>
              <Button startIcon={<AddIcon />} onClick={() => setOpenZoneModal(true)}>
                Нова Зона
              </Button>
            </Tooltip>
          </Box>
        </TabPanel>
        {/* Инвентаризация */}
        <TabPanel value={tabValue} index={5}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                {!currentSessionId ? (
                  <Tooltip title="Стартирай нова инвентаризационна сесия (Ctrl+F12)" arrow>
                    <Button 
                      variant="contained" 
                      color="primary"
                      onClick={async () => {
                        const result = await startInventorySession();
                        setCurrentSessionId(result.data.startInventorySession.id);
                        refetchInventory();
                      }}
                    >
                      Започни инвентаризация
                    </Button>
                  </Tooltip>
                ) : (
                  <>
                    <Button 
                      variant="contained" 
                      color="success"
                      onClick={async () => {
                        if (confirm('Сигурни ли сте че искате да приключите инвентаризацията? Количествата ще бъдат коригирани.')) {
                          await completeInventorySession({ variables: { sessionId: currentSessionId } });
                          setCurrentSessionId(null);
                          refetchInventory();
                        }
                      }}
                    >
                      Приключи
                    </Button>
                    <Button 
                      variant="outlined"
                      color="error"
                      onClick={() => setCurrentSessionId(null)}
                    >
                      Отказ
                    </Button>
                  </>
                )}
              </Box>
            </Grid>
            {currentSessionId && (
              <>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>Сканиране</Typography>
                    <TextField
                      fullWidth
                      label="Баркод"
                      value={inventorySearch}
                      onChange={(e) => setInventorySearch(e.target.value)}
                      onKeyDown={async (e) => {
                        if (e.key === 'Enter' && inventorySearch && inventoryQuantity) {
                          const ingredient = ingredientsData?.ingredients?.find((i: Ingredient) => i.barcode === inventorySearch);
                          if (ingredient) {
                            await addInventoryItem({
                              variables: {
                                sessionId: currentSessionId,
                                ingredientId: ingredient.id,
                                foundQuantity: parseFloat(inventoryQuantity)
                              }
                            });
                            setInventorySearch('');
                            setInventoryQuantity('');
                            refetchSessionItems();
                          }
                        }
                      }}
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      fullWidth
                      label="Намерено количество"
                      type="number"
                      value={inventoryQuantity}
                      onChange={(e) => setInventoryQuantity(e.target.value)}
                      sx={{ mb: 2 }}
                    />
                    <Button 
                      variant="contained"
                      fullWidth
                      onClick={async () => {
                        const ingredient = ingredientsData?.ingredients?.find((i: Ingredient) => i.barcode === inventorySearch);
                        if (ingredient && inventoryQuantity) {
                          await addInventoryItem({
                            variables: {
                              sessionId: currentSessionId,
                              ingredientId: ingredient.id,
                              foundQuantity: parseFloat(inventoryQuantity)
                            }
                          });
                          setInventorySearch('');
                          setInventoryQuantity('');
                          refetchSessionItems();
                        }
                      }}
                      disabled={!inventorySearch || !inventoryQuantity}
                    >
                      Добави
                    </Button>
                    
                    {barcodeData?.inventoryByBarcode && (
                      <Alert severity="info" sx={{ mt: 2 }}>
                        <strong>{barcodeData.inventoryByBarcode.ingredientName}</strong>
                        <br />
                        По система: {barcodeData.inventoryByBarcode.systemQuantity} {barcodeData.inventoryByBarcode.ingredientUnit}
                      </Alert>
                    )}
                  </Paper>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>Сканирани артикули</Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Продукт</TableCell>
                          <TableCell align="right">Намерено</TableCell>
                          <TableCell align="right">По система</TableCell>
                          <TableCell align="right">Разлика</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {sessionItemsData?.inventorySessionItems?.map((item: InventorySessionItem) => (
                          <TableRow key={item.id} sx={{ 
                            backgroundColor: item.difference > 0 ? '#e8f5e9' : item.difference < 0 ? '#ffebee' : 'inherit'
                          }}>
                            <TableCell>{item.ingredientName}</TableCell>
                            <TableCell align="right">{item.foundQuantity} {item.ingredientUnit}</TableCell>
                            <TableCell align="right">{item.systemQuantity} {item.ingredientUnit}</TableCell>
                            <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                              {item.difference > 0 ? '+' : ''}{item.difference?.toFixed(3)} {item.ingredientUnit}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              </>
            )}
            {!currentSessionId && (
              <Grid size={{ xs: 12 }}>
                <Typography variant="h6" gutterBottom>Минали инвентаризации</Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>№</TableCell>
                        <TableCell>Дата</TableCell>
                        <TableCell>Статус</TableCell>
                        <TableCell>Протокол</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {inventorySessionsData?.inventorySessions?.map((session: InventorySession) => (
                        <TableRow 
                          key={session.id} 
                          hover 
                          onClick={() => setCurrentSessionId(session.id)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell>{session.id}</TableCell>
                          <TableCell>{new Date(session.startedAt).toLocaleString('bg-BG')}</TableCell>
                          <TableCell>
                            <Chip 
                              label={session.status === 'active' ? 'Активна' : 'Приключена'} 
                              color={session.status === 'active' ? 'primary' : 'default'} 
                              size="small" 
                            />
                          </TableCell>
                          <TableCell>{session.protocolNumber || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            )}
          </Grid>
        </TabPanel>
      </Paper>

      {/* Modal: Прием на стока (Партида) */}
      <Dialog open={openBatchModal} onClose={() => { setOpenBatchModal(false); setValidationErrors({}); }} fullWidth maxWidth="md">
        <DialogTitle>Прием на стока / Нова доставка</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            {/* Header: Invoice & Supplier */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>Данни за доставката</Typography>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TextField
                      fullWidth
                      select
                      label="Доставчик"
                      size="small"
                      value={batchForm.supplierId}
                      onChange={(e) => setBatchForm({ ...batchForm, supplierId: e.target.value })}
                      error={!!validationErrors.supplierId}
                      helperText={validationErrors.supplierId}
                      required
                    >
                      {data?.suppliers.map((s: Supplier) => (
                        <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
                      ))}
                    </TextField>
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TextField
                      fullWidth
                      label="Номер на фактура"
                      size="small"
                      placeholder="Ф-2026-001"
                      value={batchForm.invoiceNumber}
                      onChange={(e) => setBatchForm({ ...batchForm, invoiceNumber: e.target.value })}
                      error={!!validationErrors.invoiceNumber}
                      helperText={validationErrors.invoiceNumber}
                      required
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TextField
                      fullWidth
                      label="Дата на доставка"
                      size="small"
                      type="date"
                      InputLabelProps={{ shrink: true }}
                      value={batchForm.invoiceDate}
                      onChange={(e) => setBatchForm({ ...batchForm, invoiceDate: e.target.value })}
                    />
                  </Grid>
                  <Grid size={{ xs: 12 }}>
                    <FormControlLabel
                      control={
                        <Switch 
                          checked={batchForm.createInvoice} 
                          onChange={(e) => setBatchForm({...batchForm, createInvoice: e.target.checked})} 
                        />
                      }
                      label="Автоматично създай входяща фактура в счетоводство"
                    />
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* Form: Add Item */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>Добавяне на артикул</Typography>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Grid container spacing={2} alignItems="center">
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TextField
                        fullWidth
                        select
                        label="Продукт"
                        size="small"
                        value={currentBatchItem.ingredientId}
                        onChange={(e) => {
                          const id = e.target.value;
                          const ing = data?.ingredients.find((i: Ingredient) => i.id.toString() === id);
                          setCurrentBatchItem({ 
                            ...currentBatchItem, 
                            ingredientId: id, 
                            storageZoneId: ing?.storageZone?.id?.toString() || '' 
                          });
                        }}
                      >
                        {data?.ingredients.map((i: Ingredient) => (
                          <MenuItem key={i.id} value={i.id}>{i.name}</MenuItem>
                        ))}
                      </TextField>
                      <Tooltip title="Сканирай баркод">
                        <IconButton color="primary" onClick={() => openScannerFor('batch')}>
                          <QrCodeIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 6, md: 2 }}>
                    <TextField
                      fullWidth
                      label="Количество"
                      size="small"
                      type="number"
                      value={currentBatchItem.quantity}
                      onChange={(e) => setCurrentBatchItem({ ...currentBatchItem, quantity: e.target.value })}
                    />
                  </Grid>
                  <Grid size={{ xs: 6, md: 3 }}>
                    <TextField
                      fullWidth
                      label="Срок годност"
                      size="small"
                      type="date"
                      InputLabelProps={{ shrink: true }}
                      value={currentBatchItem.expiryDate}
                      onChange={(e) => setCurrentBatchItem({ ...currentBatchItem, expiryDate: e.target.value })}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 3 }}>
                    <Button 
                      fullWidth 
                      variant="outlined" 
                      startIcon={<AddIcon />} 
                      onClick={handleAddItemToBatch}
                      disabled={!currentBatchItem.ingredientId || !currentBatchItem.quantity}
                    >
                      Добави артикул
                    </Button>
                  </Grid>
                  
                  {/* Extra fields for the item (optional) */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Партиден номер (по избор)"
                      size="small"
                      value={currentBatchItem.batchNumber}
                      onChange={(e) => setCurrentBatchItem({ ...currentBatchItem, batchNumber: e.target.value })}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      select
                      label="Зона за съхранение"
                      size="small"
                      value={currentBatchItem.storageZoneId}
                      onChange={(e) => setCurrentBatchItem({ ...currentBatchItem, storageZoneId: e.target.value })}
                    >
                      {data?.storageZones?.map((z: StorageZone) => (
                        <MenuItem key={z.id} value={z.id}>{z.name} ({z.tempMin}°C - {z.tempMax}°C)</MenuItem>
                      ))}
                    </TextField>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>

            {/* List: Items added */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>Списък артикули ({batchForm.items.length})</Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.100' }}>
                      <TableCell>Продукт</TableCell>
                      <TableCell align="right">К-во</TableCell>
                      <TableCell>Срок годност</TableCell>
                      <TableCell>Партида</TableCell>
                      <TableCell align="right">Действия</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {batchForm.items.map((item, index) => {
                      const ingId = typeof item.ingredientId === 'string' ? parseInt(item.ingredientId) : item.ingredientId;
                      const ing = data?.ingredients?.find((i: Ingredient) => i.id === ingId);
                      return (
                        <TableRow key={index}>
                          <TableCell>{ing?.name || `ID: ${item.ingredientId}`}</TableCell>
                          <TableCell align="right">{item.quantity} {ing?.unit || ''}</TableCell>
                          <TableCell>{item.expiryDate ? new Date(item.expiryDate).toLocaleDateString('bg-BG') : '-'}</TableCell>
                          <TableCell>{item.batchNumber || '-'}</TableCell>
                          <TableCell align="right">
                            <IconButton size="small" color="error" onClick={() => handleRemoveItemFromBatch(index)}>
                              <EditIcon sx={{ transform: 'rotate(45deg)' }} />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                    {batchForm.items.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center">Все още няма добавени артикули</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              {validationErrors.items && (
                <Typography color="error" variant="caption" sx={{ mt: 1, display: 'block' }}>
                  {validationErrors.items}
                </Typography>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setOpenBatchModal(false)}>Отказ</Button>
          <Button 
            onClick={handleAddBatch} 
            variant="contained" 
            color="primary"
            disabled={batchForm.items.length === 0}
            size="large"
          >
            Приключи и зачисли ({batchForm.items.length} артикула)
          </Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Добавяне на Доставчик */}
      <Dialog open={openSupplierModal} onClose={() => { setOpenSupplierModal(false); setValidationErrors({}); }} fullWidth maxWidth="sm">
        <DialogTitle>Нов Доставчик</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <ValidatedTextField
                label="Име на фирмата"
                value={supplierForm.name}
                onChange={(value) => setSupplierForm({ ...supplierForm, name: value })}
                tooltip="Наименование на фирмата"
                error={validationErrors.name}
                required
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <ValidatedTextField
                label="ЕИК"
                value={supplierForm.eik}
                onChange={(value) => setSupplierForm({ ...supplierForm, eik: value })}
                tooltip="Единен идентификационен код"
                error={validationErrors.eik}
                required
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="ДДС Номер"
                value={supplierForm.vatNumber}
                onChange={(e) => setSupplierForm({ ...supplierForm, vatNumber: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Лице за контакт"
                value={supplierForm.contactPerson}
                onChange={(e) => setSupplierForm({ ...supplierForm, contactPerson: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Телефон"
                value={supplierForm.phone}
                onChange={(e) => setSupplierForm({ ...supplierForm, phone: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSupplierModal(false)}>Отказ</Button>
          <Button onClick={handleAddSupplier} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Добавяне на Зона */}
      <Dialog open={openZoneModal} onClose={() => { setOpenZoneModal(false); setValidationErrors({}); }} fullWidth maxWidth="sm">
        <DialogTitle>Нова Зона за съхранение</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <ValidatedTextField
                label="Име на зоната (напр. Хладилник 1)"
                value={zoneForm.name}
                onChange={(value) => setZoneForm({ ...zoneForm, name: value })}
                tooltip="Наименование на зоната за съхранение"
                error={validationErrors.name}
                required
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <ValidatedTextField
                label="Мин. Температура (°C)"
                value={zoneForm.tempMin}
                onChange={(value) => setZoneForm({ ...zoneForm, tempMin: value })}
                tooltip="Минимална температура (може да е отрицателна)"
                type="number"
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <ValidatedTextField
                label="Макс. Температура (°C)"
                value={zoneForm.tempMax}
                onChange={(value) => setZoneForm({ ...zoneForm, tempMax: value })}
                tooltip="Максимална температура"
                type="number"
                error={validationErrors.tempMax}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Описание"
                multiline
                rows={2}
                value={zoneForm.description}
                onChange={(e) => setZoneForm({ ...zoneForm, description: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                select
                label="Тип на актива"
                value={zoneForm.assetType}
                onChange={(e) => setZoneForm({ ...zoneForm, assetType: e.target.value })}
              >
                <MenuItem value="KMA">КМА (Краткотраен материален актив)</MenuItem>
                <MenuItem value="DMA">ДМА (Дълготраен материален актив)</MenuItem>
              </TextField>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                select
                label="Тип на зоната"
                value={zoneForm.zoneType}
                onChange={(e) => setZoneForm({ ...zoneForm, zoneType: e.target.value })}
              >
                <MenuItem value="food">Хранителен</MenuItem>
                <MenuItem value="non_food">Нехранителен</MenuItem>
              </TextField>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={zoneForm.isActive}
                    onChange={(e) => setZoneForm({ ...zoneForm, isActive: e.target.checked })}
                  />
                }
                label="Активна"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenZoneModal(false)}>Отказ</Button>
          <Button onClick={handleAddZone} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Редакция на Доставчик */}
      <Dialog open={!!editingSupplier} onClose={() => setEditingSupplier(null)} fullWidth maxWidth="sm">
        <DialogTitle>Редакция на Доставчик</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Име на фирмата"
                value={editSupplierForm.name}
                onChange={(e) => setEditSupplierForm({ ...editSupplierForm, name: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="ЕИК"
                value={editSupplierForm.eik}
                onChange={(e) => setEditSupplierForm({ ...editSupplierForm, eik: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="ДДС Номер"
                value={editSupplierForm.vatNumber}
                onChange={(e) => setEditSupplierForm({ ...editSupplierForm, vatNumber: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Лице за контакт"
                value={editSupplierForm.contactPerson}
                onChange={(e) => setEditSupplierForm({ ...editSupplierForm, contactPerson: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Телефон"
                value={editSupplierForm.phone}
                onChange={(e) => setEditSupplierForm({ ...editSupplierForm, phone: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Имейл"
                value={editSupplierForm.email}
                onChange={(e) => setEditSupplierForm({ ...editSupplierForm, email: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Адрес"
                value={editSupplierForm.address}
                onChange={(e) => setEditSupplierForm({ ...editSupplierForm, address: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditingSupplier(null)}>Отказ</Button>
          <Button onClick={handleUpdateSupplier} variant="contained" disabled={!editSupplierForm.name}>Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Редакция на Зона */}
      <Dialog open={!!editingZone} onClose={() => setEditingZone(null)} fullWidth maxWidth="sm">
        <DialogTitle>Редакция на Зона за съхранение</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Име на зоната"
                value={editZoneForm.name}
                onChange={(e) => setEditZoneForm({ ...editZoneForm, name: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Мин. Температура (°C)"
                type="number"
                value={editZoneForm.tempMin}
                onChange={(e) => setEditZoneForm({ ...editZoneForm, tempMin: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Макс. Температура (°C)"
                type="number"
                value={editZoneForm.tempMax}
                onChange={(e) => setEditZoneForm({ ...editZoneForm, tempMax: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Описание"
                multiline
                rows={2}
                value={editZoneForm.description}
                onChange={(e) => setEditZoneForm({ ...editZoneForm, description: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={editZoneForm.isActive}
                    onChange={(e) => setEditZoneForm({ ...editZoneForm, isActive: e.target.checked })}
                  />
                }
                label="Активна"
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                select
                label="Тип на актива"
                value={editZoneForm.assetType}
                onChange={(e) => setEditZoneForm({ ...editZoneForm, assetType: e.target.value })}
              >
                <MenuItem value="KMA">КМА (Краткотраен материален актив)</MenuItem>
                <MenuItem value="DMA">ДМА (Дълготраен материален актив)</MenuItem>
              </TextField>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                select
                label="Тип на зоната"
                value={editZoneForm.zoneType}
                onChange={(e) => setEditZoneForm({ ...editZoneForm, zoneType: e.target.value })}
              >
                <MenuItem value="food">Хранителен</MenuItem>
                <MenuItem value="non_food">Нехранителен</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditingZone(null)}>Отказ</Button>
          <Button onClick={handleUpdateZone} variant="contained" disabled={!editZoneForm.name}>Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Редакция на Продукт */}
      <Dialog open={!!editingIngredient} onClose={() => setEditingIngredient(null)} fullWidth maxWidth="sm">
        <DialogTitle>Редакция на продукт</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Име на продукта"
                value={editIngredientForm.name}
                onChange={(e) => setEditIngredientForm({ ...editIngredientForm, name: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                select
                label="Мерна единица"
                value={editIngredientForm.unit}
                onChange={(e) => setEditIngredientForm({ ...editIngredientForm, unit: e.target.value })}
              >
                <MenuItem value="kg">Килограм (kg)</MenuItem>
                <MenuItem value="g">Грам (g)</MenuItem>
                <MenuItem value="l">Литър (l)</MenuItem>
                <MenuItem value="ml">Милилитър (ml)</MenuItem>
                <MenuItem value="br">Брой (br)</MenuItem>
              </TextField>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Мин. наличност"
                type="number"
                value={editIngredientForm.baselineMinStock}
                onChange={(e) => setEditIngredientForm({ ...editIngredientForm, baselineMinStock: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                select
                label="Зона за съхранение"
                value={editIngredientForm.storageZoneId}
                onChange={(e) => setEditIngredientForm({ ...editIngredientForm, storageZoneId: e.target.value })}
              >
                <MenuItem value="">Няма зона</MenuItem>
                {data?.storageZones.map((z: StorageZone) => (
                  <MenuItem key={z.id} value={z.id}>{z.name}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Баркод (EAN)"
                value={editIngredientForm.barcode}
                onChange={(e) => setEditIngredientForm({ ...editIngredientForm, barcode: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                select
                label="Вид на продукта"
                value={editIngredientForm.productType}
                onChange={(e) => setEditIngredientForm({ ...editIngredientForm, productType: e.target.value })}
              >
                <MenuItem value="raw">Суровина</MenuItem>
                <MenuItem value="semi_finished">Заготовка</MenuItem>
                <MenuItem value="finished">Готов продукт</MenuItem>
              </TextField>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={editIngredientForm.isPerishable}
                    onChange={(e) => setEditIngredientForm({ ...editIngredientForm, isPerishable: e.target.checked })}
                  />
                }
                label="Развален продукт"
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Дни за предупреждение"
                type="number"
                value={editIngredientForm.expiryWarningDays}
                onChange={(e) => setEditIngredientForm({ ...editIngredientForm, expiryWarningDays: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditingIngredient(null)}>Отказ</Button>
          <Button onClick={handleUpdateIngredient} variant="contained" disabled={!editIngredientForm.name}>Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Редакция на Партида */}
      <Dialog open={!!editingBatch} onClose={() => setEditingBatch(null)} fullWidth maxWidth="sm">
        <DialogTitle>Редакция на партида</DialogTitle>
        <DialogContent dividers>
            <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                select
                label="Продукт"
                value={editBatchForm.ingredientId}
                onChange={(e) => setEditBatchForm({ ...editBatchForm, ingredientId: e.target.value })}
              >
                {data?.ingredients.map((i: Ingredient) => (
                  <MenuItem key={i.id} value={i.id}>{i.name}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Количество"
                type="number"
                value={editBatchForm.quantity}
                onChange={(e) => setEditBatchForm({ ...editBatchForm, quantity: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Срок на годност"
                type="date"
                InputLabelProps={{ shrink: true }}
                value={editBatchForm.expiryDate}
                onChange={(e) => setEditBatchForm({ ...editBatchForm, expiryDate: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                select
                label="Доставчик"
                value={editBatchForm.supplierId}
                onChange={(e) => setEditBatchForm({ ...editBatchForm, supplierId: e.target.value })}
              >
                <MenuItem value="">Няма</MenuItem>
                {data?.suppliers.map((s: Supplier) => (
                  <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Номер на фактура"
                value={editBatchForm.invoiceNumber}
                onChange={(e) => setEditBatchForm({ ...editBatchForm, invoiceNumber: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Партиден номер"
                value={editBatchForm.batchNumber}
                onChange={(e) => setEditBatchForm({ ...editBatchForm, batchNumber: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                select
                label="Зона за съхранение"
                value={editBatchForm.storageZoneId}
                onChange={(e) => setEditBatchForm({ ...editBatchForm, storageZoneId: e.target.value })}
              >
                <MenuItem value="">Няма зона</MenuItem>
                {data?.storageZones.map((z: StorageZone) => (
                  <MenuItem key={z.id} value={z.id}>{z.name}</MenuItem>
                ))}
              </TextField>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditingBatch(null)}>Отказ</Button>
          <Button onClick={handleUpdateBatch} variant="contained" color="primary">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Нов продукт */}
      <Dialog open={openIngredientModal} onClose={() => { setOpenIngredientModal(false); setValidationErrors({}); }} fullWidth maxWidth="sm">
        <DialogTitle>Добавяне на нов продукт/съставка</DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Име на продукта"
                placeholder="Напр. Брашно, Захар, Краве масло..."
                value={ingredientForm.name}
                onChange={(e) => setIngredientForm({ ...ingredientForm, name: e.target.value })}
                error={!!validationErrors.name}
                helperText={validationErrors.name}
              />
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                select
                label="Мерна единица"
                value={ingredientForm.unit}
                onChange={(e) => setIngredientForm({ ...ingredientForm, unit: e.target.value })}
              >
                <MenuItem value="kg">кг</MenuItem>
                <MenuItem value="l">л</MenuItem>
                <MenuItem value="pcs">бр</MenuItem>
                <MenuItem value="g">г</MenuItem>
                <MenuItem value="ml">мл</MenuItem>
                <MenuItem value="box">кутия</MenuItem>
                <MenuItem value="pack">опаковка</MenuItem>
              </TextField>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <TextField
                fullWidth
                label="Баркод"
                value={ingredientForm.barcode}
                onChange={(e) => setIngredientForm({ ...ingredientForm, barcode: e.target.value })}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                select
                label="Зона на съхранение"
                value={ingredientForm.storageZoneId}
                onChange={(e) => setIngredientForm({ ...ingredientForm, storageZoneId: e.target.value })}
              >
                {data?.storageZones?.map((z: StorageZone) => (
                  <MenuItem key={z.id} value={z.id}>{z.name}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Минимално количество (за警报)"
                type="number"
                value={ingredientForm.baselineMinStock}
                onChange={(e) => setIngredientForm({ ...ingredientForm, baselineMinStock: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenIngredientModal(false)}>Отказ</Button>
          <Button onClick={handleAddIngredient} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      {/* Barcode Scanner Dialog */}
      <Dialog open={scannerOpen} onClose={stopScanner} fullWidth maxWidth="sm">
        <DialogTitle>Сканирай баркод</DialogTitle>
        <DialogContent>
          <Box id="barcode-scanner" sx={{ width: '100%', minHeight: 300 }} />
          <TextField
            fullWidth
            label="Или въведи ръчно баркод"
            sx={{ mt: 2 }}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              handleBarcodeFound(e.target.value);
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={stopScanner}>Затвори</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default WarehousePage;
