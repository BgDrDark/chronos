import React, { useState, useRef, useEffect } from 'react';
import {
  Container, Typography, Box, Paper, Button, IconButton, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, Grid, Divider, List, ListItem, ListItemText,
  CircularProgress, Tabs, Tab, Table, TableBody, TableCell, TableHead, TableRow, Autocomplete,
  Tooltip, Select, MenuItem, FormControl, InputLabel, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Factory as FactoryIcon,
  RestaurantMenu as RecipeIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, gql } from '@apollo/client';
import { CREATE_RECIPE, CREATE_WORKSTATION, DELETE_RECIPE } from '../graphql/confectioneryMutations';
import { ME_QUERY } from '../graphql/queries';

interface ValidatedTextFieldProps {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  tooltip?: string;
  placeholder?: string;
  error?: string;
  required?: boolean;
  type?: 'text' | 'number';
  select?: boolean;
  children?: React.ReactNode;
  size?: 'small' | 'medium';
  fullWidth?: boolean;
  disabled?: boolean;
  multiline?: boolean;
  rows?: number;
  InputProps?: any;
  sx?: any;
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

const GET_RECIPES_AND_DATA = gql`
  query GetRecipesAndData {
    recipes {
      id
      name
      yieldQuantity
      yieldUnit
      shelfLifeDays
      shelfLifeFrozenDays
      productionDeadlineDays
      defaultPieces
      standardQuantity
      sections {
        id
        sectionType
        name
        shelfLifeDays
        wastePercentage
        sectionOrder
        ingredients {
          id
          quantityGross
          ingredient {
            id
            name
            unit
          }
        }
        steps {
          id
          name
          stepOrder
          estimatedDurationMinutes
          workstation {
            id
            name
          }
        }
      }
    }
    ingredients {
      id
      name
      unit
      barcode
    }
    workstations {
      id
      name
      description
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

const RecipesPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [openRecipeModal, setOpenRecipeModal] = useState(false);
  const [openStationModal, setOpenStationModal] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { data, loading, error, refetch } = useQuery(GET_RECIPES_AND_DATA);
  const [createRecipe] = useMutation(CREATE_RECIPE);
  const [createWorkstation] = useMutation(CREATE_WORKSTATION);
  const [deleteRecipe] = useMutation(DELETE_RECIPE);

  // Export recipes to JSON
  const handleExportRecipes = () => {
    const recipesData = data?.recipes?.map((r: any) => ({
      name: r.name,
      yieldQuantity: r.yieldQuantity,
      yieldUnit: r.yieldUnit,
      shelfLifeDays: r.shelfLifeDays,
      instructions: r.instructions,
      ingredients: r.ingredients?.map((i: any) => ({
        ingredientName: i.ingredient?.name,
        quantityGross: i.quantityGross,
        quantityNet: i.quantityNet,
        wastePercentage: i.wastePercentage,
      })),
      steps: r.steps?.map((s: any) => ({
        name: s.name,
        estimatedDurationMinutes: s.estimatedDurationMinutes,
      })),
    })) || [];

    const blob = new Blob([JSON.stringify(recipesData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `recipes_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Copy recipe
  const handleCopyRecipe = (recipe: any) => {
    const copiedSections = recipe.sections?.map((section: any) => ({
      type: section.sectionType || 'dough',
      name: section.name || '',
      shelfLifeDays: section.shelfLifeDays || null,
      wastePercentage: section.wastePercentage || 0,
      ingredients: section.ingredients?.map((i: any) => ({
        ingredientId: i.ingredient?.id?.toString() || '',
        quantityGross: i.quantityGross?.toString() || '',
      })) || [],
      steps: section.steps?.map((s: any) => ({
        workstationId: s.workstation?.id?.toString() || '',
        name: s.name || '',
        stepOrder: s.stepOrder || 1,
        estimatedDurationMinutes: s.estimatedDurationMinutes?.toString() || '',
      })) || []
    })) || [
      { type: 'dough', name: 'Блат - ', shelfLifeDays: null, wastePercentage: 10, ingredients: [], steps: [] },
      { type: 'cream', name: 'Крем - ', shelfLifeDays: null, wastePercentage: 5, ingredients: [], steps: [] },
      { type: 'decoration', name: 'Декор - ', shelfLifeDays: null, wastePercentage: 15, ingredients: [], steps: [] }
    ];

    setRecipeForm({
      name: `${recipe.name} (копие)`,
      description: recipe.description || '',
      yieldQuantity: recipe.yieldQuantity?.toString() || '1',
      yieldUnit: recipe.yieldUnit || 'br',
      shelfLifeDays: recipe.shelfLifeDays?.toString() || '7',
      shelfLifeFrozenDays: recipe.shelfLifeFrozenDays?.toString() || '30',
      productionDeadlineDays: recipe.productionDeadlineDays?.toString() || '',
      defaultPieces: recipe.defaultPieces || 12,
      currentPieces: recipe.defaultPieces || 12,
      standardQuantity: recipe.standardQuantity?.toString() || '1',
      instructions: recipe.instructions || '',
      sections: copiedSections
    });
    setOpenRecipeModal(true);
  };

  // Import recipes from JSON - simplified for now
  const handleImportRecipes = () => {
    // Placeholder - to be implemented with new section structure
    alert('Импортът на рецепти ще бъде обновен за новата структура');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Form States - New 3-section structure
  const [recipeForm, setRecipeForm] = useState({
    name: '',
    description: '',
    yieldQuantity: '1',
    yieldUnit: 'br',
    shelfLifeDays: '7',
    shelfLifeFrozenDays: '30',
    productionDeadlineDays: '',
    defaultPieces: 12,
    currentPieces: 12,
    standardQuantity: '1',
    instructions: '',
    sections: [
      { type: 'dough', name: 'Блат - ', shelfLifeDays: null, wastePercentage: 10, ingredients: [], steps: [] },
      { type: 'cream', name: 'Крем - ', shelfLifeDays: null, wastePercentage: 5, ingredients: [], steps: [] },
      { type: 'decoration', name: 'Декор - ', shelfLifeDays: null, wastePercentage: 15, ingredients: [], steps: [] }
    ] as any[]
  });

  // Validation
  const validateRecipe = (): Record<string, string> => {
    const errors: Record<string, string> = {};
    
    if (!recipeForm.name || recipeForm.name.trim().length < 2) {
      errors.name = 'Името трябва да е поне 2 символа';
    }
    
    if (!recipeForm.yieldQuantity || parseFloat(recipeForm.yieldQuantity) <= 0) {
      errors.yieldQuantity = 'Добивът трябва да е > 0';
    }
    
    if (recipeForm.shelfLifeDays && (parseInt(recipeForm.shelfLifeDays) < 1 || parseInt(recipeForm.shelfLifeDays) > 365)) {
      errors.shelfLifeDays = 'Срокът трябва да е между 1 и 365 дни';
    }
    
    if (recipeForm.shelfLifeFrozenDays && (parseInt(recipeForm.shelfLifeFrozenDays) < 1 || parseInt(recipeForm.shelfLifeFrozenDays) > 730)) {
      errors.shelfLifeFrozenDays = 'Срокът трябва да е между 1 и 730 дни';
    }
    
    if (recipeForm.productionDeadlineDays && (parseInt(recipeForm.productionDeadlineDays) < 0 || parseInt(recipeForm.productionDeadlineDays) > 30)) {
      errors.productionDeadlineDays = 'Срокът за производство трябва да е между 0 и 30 дни';
    }
    
    recipeForm.sections.forEach((section: any, idx: number) => {
      if (section.name && section.name.trim().length < 2) {
        errors[`section_${idx}_name`] = 'Името трябва да е поне 2 символа';
      }
      
      if (section.ingredients && section.ingredients.length > 0) {
        section.ingredients.forEach((ing: any, ingIdx: number) => {
          if (!ing.ingredientId) {
            errors[`section_${idx}_ing_${ingIdx}`] = 'Избери съставка';
          }
          if (!ing.quantityGross || parseFloat(ing.quantityGross) <= 0) {
            errors[`section_${idx}_qty_${ingIdx}`] = 'Теглото трябва да е > 0';
          }
        });
      }
    });
    
    return errors;
  };

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Handle pieces change (+/-) with recalculation
  const handlePiecesChange = (newPieces: number) => {
    if (newPieces <= 0) return;
    const oldPieces = recipeForm.currentPieces;
    const ratio = newPieces / oldPieces;
    
    const updatedSections = recipeForm.sections.map((section: any) => ({
      ...section,
      ingredients: section.ingredients.map((ing: any) => ({
        ...ing,
        quantityGross: ing.originalQuantity 
          ? Math.round(ing.originalQuantity * ratio * 1000) / 1000
          : (parseFloat(ing.quantityGross || '0') * ratio)
      }))
    }));
    
    setRecipeForm({
      ...recipeForm,
      currentPieces: newPieces,
      sections: updatedSections
    });
  };

  // Reset to default pieces
  const handleResetPieces = () => {
    handlePiecesChange(recipeForm.defaultPieces);
  };

  // Update section name when recipe name changes
  const handleNameChange = (newName: string) => {
    const updatedSections = recipeForm.sections.map((section: any) => ({
      ...section,
      name: `${section.type === 'dough' ? 'Блат' : section.type === 'cream' ? 'Крем' : 'Декор'} - ${newName}`
    }));
    setRecipeForm({
      ...recipeForm,
      name: newName,
      sections: updatedSections
    });
  };

  // Add ingredient to section
  const handleAddIngredient = (sectionIdx: number) => {
    const newSections = [...recipeForm.sections];
    newSections[sectionIdx].ingredients.push({
      ingredientId: '',
      quantityGross: '',
      originalQuantity: null
    });
    setRecipeForm({ ...recipeForm, sections: newSections });
  };

  // Remove ingredient from section
  const handleRemoveIngredient = (sectionIdx: number, ingIdx: number) => {
    const newSections = [...recipeForm.sections];
    newSections[sectionIdx].ingredients.splice(ingIdx, 1);
    setRecipeForm({ ...recipeForm, sections: newSections });
  };

  // Add step to section
  const handleAddStep = (sectionIdx: number) => {
    const newSections = [...recipeForm.sections];
    newSections[sectionIdx].steps.push({
      workstationId: '',
      name: '',
      stepOrder: newSections[sectionIdx].steps.length + 1,
      estimatedDurationMinutes: ''
    });
    setRecipeForm({ ...recipeForm, sections: newSections });
  };

  // Remove step from section
  const handleRemoveStep = (sectionIdx: number, stepIdx: number) => {
    const newSections = [...recipeForm.sections];
    newSections[sectionIdx].steps.splice(stepIdx, 1);
    setRecipeForm({ ...recipeForm, sections: newSections });
  };

  // Calculate totals for a section
  const calculateSectionTotals = (section: any) => {
    const totalGross = section.ingredients.reduce((sum: number, ing: any) => 
      sum + (parseFloat(ing.quantityGross) || 0), 0);
    const wastePct = section.wastePercentage || 0;
    const totalNet = totalGross - (totalGross * wastePct / 100);
    return { totalGross, totalNet };
  };

  const [stationForm, setStationForm] = useState({
    name: '',
    description: ''
  });

  const [scannerOpen, setScannerOpen] = useState(false);
  const [scannedBarcode, setScannedBarcode] = useState('');

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      
      switch (e.key) {
        case 'F5':
          e.preventDefault();
          setOpenRecipeModal(true);
          break;
        case 'F6':
          e.preventDefault();
          setOpenStationModal(true);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const { data: userData } = useQuery(ME_QUERY);
  const user = userData?.me;

  const handleAddRecipe = async () => {
    const errors = validateRecipe();
    setValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      return;
    }
    
    if (!user?.companyId) return;
    try {
      const sections = recipeForm.sections.map((section: any, idx: number) => ({
        sectionType: section.type,
        name: section.name || `${section.type === 'dough' ? 'Блат' : section.type === 'cream' ? 'Крем' : 'Декор'} - ${recipeForm.name}`,
        shelfLifeDays: section.shelfLifeDays ? parseInt(section.shelfLifeDays) : null,
        wastePercentage: parseFloat(section.wastePercentage) || 0,
        sectionOrder: idx + 1,
        ingredients: section.ingredients
          .filter((i: any) => i.ingredientId && i.quantityGross)
          .map((i: any) => ({
            ingredientId: parseInt(i.ingredientId),
            quantityGross: parseFloat(i.quantityGross)
          })),
        steps: section.steps
          .filter((s: any) => s.workstationId && s.name)
          .map((s: any, sIdx: number) => ({
            workstationId: parseInt(s.workstationId),
            name: s.name,
            stepOrder: s.stepOrder || sIdx + 1,
            estimatedDurationMinutes: s.estimatedDurationMinutes ? parseInt(s.estimatedDurationMinutes) : null
          }))
      }));

      await createRecipe({
        variables: {
          input: {
            name: recipeForm.name,
            description: recipeForm.description,
            yieldQuantity: parseFloat(recipeForm.yieldQuantity),
            yieldUnit: recipeForm.yieldUnit,
            shelfLifeDays: parseInt(recipeForm.shelfLifeDays),
            shelfLifeFrozenDays: parseInt(recipeForm.shelfLifeFrozenDays),
            productionDeadlineDays: recipeForm.productionDeadlineDays ? parseInt(recipeForm.productionDeadlineDays) : null,
            defaultPieces: recipeForm.defaultPieces,
            standardQuantity: parseFloat(recipeForm.standardQuantity),
            instructions: recipeForm.instructions,
            companyId: user.companyId,
            sections: sections
          }
        }
      });
      setOpenRecipeModal(false);
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddStation = async () => {
    if (!user?.companyId) return;
    try {
      await createWorkstation({
        variables: {
          name: stationForm.name,
          description: stationForm.description,
          companyId: user.companyId
        }
      });
      setOpenStationModal(false);
      setStationForm({ name: '', description: '' });
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  if (error) return <Typography color="error">Грешка: {error.message}</Typography>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Производство и Рецепти
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<ExportIcon />} 
            onClick={handleExportRecipes}
            sx={{ mr: 1 }}
          >
            Експорт
          </Button>
          <Tooltip title="Импортирай рецепти от JSON файл" arrow>
            <Button 
              variant="outlined" 
              startIcon={<ImportIcon />} 
              onClick={() => fileInputRef.current?.click()}
              sx={{ mr: 1 }}
            >
              Импорт
            </Button>
          </Tooltip>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".json"
            onChange={handleImportRecipes}
          />
          <Tooltip title="Добави работна станция (Ctrl+F6)" arrow>
            <Button 
              variant="outlined" 
              startIcon={<FactoryIcon />} 
              onClick={() => setOpenStationModal(true)}
              sx={{ mr: 1 }}
            >
              Нова Станция
            </Button>
          </Tooltip>
          <Tooltip title="Създай нова рецепта (Ctrl+F5)" arrow>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />} 
              onClick={() => setOpenRecipeModal(true)}
            >
              Нова Рецепта
            </Button>
          </Tooltip>
        </Box>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} centered indicatorColor="primary" textColor="primary">
          <Tab icon={<RecipeIcon />} label="Рецептурник" />
          <Tab icon={<FactoryIcon />} label="Работни Станции (Терминали)" />
        </Tabs>

        {/* ТАБ: РЕЦЕПТИ */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {data?.recipes.map((recipe: any) => (
              <Grid size={{ xs: 12, md: 6 }} key={recipe.id}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box>
                      <Typography variant="h6" color="primary">{recipe.name}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        Добив: {recipe.yieldQuantity} {recipe.yieldUnit} | Срок: {recipe.shelfLifeDays} дни
                      </Typography>
                    </Box>
                    <Tooltip title="Копирай рецептата като основа за нова" arrow>
                      <IconButton size="small" color="primary" onClick={() => handleCopyRecipe(recipe)}>
                        <CopyIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="subtitle2">Съставки:</Typography>
                  <List>
                    {recipe.ingredients.slice(0, 3).map((ri: any, idx: number) => (
                      <ListItem key={idx} sx={{ py: 0, px: 1 }}>
                        <ListItemText 
                          primary={`${ri.ingredient.name}: ${ri.quantityGross} ${ri.ingredient.unit}`} 
                          primaryTypographyProps={{ variant: 'caption' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                  <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button size="small" onClick={() => setSelectedRecipe(recipe)}>Виж пълна рецепта</Button>
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* ТАБ: РАБОТНИ СТАНЦИИ */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={2}>
            {data?.workstations.map((ws: any) => (
              <Grid size={{ xs: 12, sm: 4 }} key={ws.id}>
                <Paper variant="outlined" sx={{ p: 3, textAlign: 'center', borderRadius: 4 }}>
                  <FactoryIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{ws.name}</Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    {ws.description || 'Няма описание'}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Typography variant="caption" display="block">
                    ID за вход: <b>{ws.id}</b>
                  </Typography>
                  <Button variant="text" size="small" sx={{ mt: 1 }}>Настройки</Button>
                </Paper>
              </Grid>
            ))}
            {data?.workstations.length === 0 && (
              <Box sx={{ width: '100%', textAlign: 'center', py: 5 }}>
                <Typography color="textSecondary">Няма добавени работни станции.</Typography>
              </Box>
            )}
          </Grid>
        </TabPanel>
      </Paper>

      {/* Modal: Нова Станция */}
      <Dialog open={openStationModal} onClose={() => setOpenStationModal(false)} fullWidth maxWidth="xs">
        <DialogTitle>Добавяне на работна станция</DialogTitle>
        <DialogContent dividers>
          <TextField
            fullWidth
            label="Име на станцията (напр. Пекарна)"
            sx={{ mb: 2, mt: 1 }}
            value={stationForm.name}
            onChange={e => setStationForm({ ...stationForm, name: e.target.value })}
          />
          <TextField
            fullWidth
            label="Описание / Локация"
            multiline
            rows={2}
            value={stationForm.description}
            onChange={e => setStationForm({ ...stationForm, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenStationModal(false)}>Отказ</Button>
          <Button onClick={handleAddStation} variant="contained" disabled={!stationForm.name}>Създай Станция</Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Нова Рецепта */}
      <Dialog open={openRecipeModal} onClose={() => { setOpenRecipeModal(false); setValidationErrors({}); }} fullWidth maxWidth="lg">
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            Създаване на нова рецепта
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {/* Header Section */}
          <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: '#f5f5f5' }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <ValidatedTextField
                  label="Име на продукта"
                  value={recipeForm.name}
                  onChange={(value) => handleNameChange(value)}
                  placeholder="Торта Шоколад..."
                  tooltip="Въведете името на крайния продукт"
                  error={validationErrors.name}
                  required
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ValidatedTextField
                    label="Бр. парчета"
                    value={recipeForm.currentPieces.toString()}
                    onChange={(value) => handlePiecesChange(parseInt(value) || 1)}
                    tooltip="Брой парчета/бройки от продукта"
                    type="number"
                  />
                  <Button 
                    variant="outlined" 
                    size="small"
                    onClick={() => handlePiecesChange(recipeForm.currentPieces - 1)}
                  >-</Button>
                  <Button 
                    variant="outlined" 
                    size="small"
                    onClick={() => handlePiecesChange(recipeForm.currentPieces + 1)}
                  >+</Button>
                  <Button 
                    variant="contained" 
                    size="small"
                    onClick={handleResetPieces}
                  >Default</Button>
                </Box>
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <ValidatedTextField
                  label="Срок (хладилник)"
                  value={recipeForm.shelfLifeDays}
                  onChange={(value) => setRecipeForm({...recipeForm, shelfLifeDays: value})}
                  tooltip="Срок на годност в хладилник (дни)"
                  type="number"
                  error={validationErrors.shelfLifeDays}
                  InputProps={{ endAdornment: 'дни' }}
                />
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <ValidatedTextField
                  label="Срок за производство"
                  value={recipeForm.productionDeadlineDays}
                  onChange={(value) => setRecipeForm({...recipeForm, productionDeadlineDays: value})}
                  tooltip="Колко дни преди expiry да се произведе (незадължително)"
                  type="number"
                  error={validationErrors.productionDeadlineDays}
                  InputProps={{ endAdornment: 'дни' }}
                />
              </Grid>
            </Grid>
          </Paper>

          {/* 3 Sections with Accordion */}
          {recipeForm.sections.map((section: any, sectionIdx: number) => {
            const totals = calculateSectionTotals(section);
            const sectionTitle = section.type === 'dough' ? 'ПЕКАРНА' : section.type === 'cream' ? 'КРЕМОВЕ' : 'ДЕКОРАЦИЯ';
            return (
              <Accordion key={section.type} defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    ЧАСТ {sectionIdx + 1}: {sectionTitle} - {section.name || 'Нова част'}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, sm: 6 }}>
                      <ValidatedTextField
                        label="Име на заготовката"
                        value={section.name || ''}
                        onChange={(value) => {
                          const newSections = [...recipeForm.sections];
                          newSections[sectionIdx].name = value;
                          setRecipeForm({ ...recipeForm, sections: newSections });
                        }}
                        tooltip="Име на заготовката (напр. Блат пандишпан)"
                        error={validationErrors[`section_${sectionIdx}_name`]}
                      />
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <ValidatedTextField
                        label="Срок на заготовката"
                        value={section.shelfLifeDays?.toString() || ''}
                        onChange={(value) => {
                          const newSections = [...recipeForm.sections];
                          newSections[sectionIdx].shelfLifeDays = value ? parseInt(value) : null;
                          setRecipeForm({ ...recipeForm, sections: newSections });
                        }}
                        tooltip="Срок на годност на заготовката (дни)"
                        type="number"
                        InputProps={{ endAdornment: 'дни' }}
                      />
                    </Grid>
                    <Grid size={{ xs: 6, sm: 3 }}>
                      <ValidatedTextField
                        label="Фира"
                        value={section.wastePercentage?.toString() || '0'}
                        onChange={(value) => {
                          const newSections = [...recipeForm.sections];
                          newSections[sectionIdx].wastePercentage = parseFloat(value) || 0;
                          setRecipeForm({ ...recipeForm, sections: newSections });
                        }}
                        tooltip="Процент фира/загуба при обработка"
                        type="number"
                        InputProps={{ endAdornment: '%' }}
                      />
                    </Grid>

                    {/* Ingredients */}
                    <Grid size={{ xs: 12 }}>
                      <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                        СЪСТАВКИ:
                      </Typography>
                      {section.ingredients.map((ing: any, ingIdx: number) => (
                        <Box key={ingIdx} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                          <Autocomplete
                            size="small"
                            options={data?.ingredients || []}
                            getOptionLabel={(option: any) => `${option.name} (${option.unit})`}
                            value={data?.ingredients?.find((i: any) => i.id === parseInt(ing.ingredientId)) || null}
                            onChange={(_, newValue) => {
                              const newSections = [...recipeForm.sections];
                              newSections[sectionIdx].ingredients[ingIdx].ingredientId = newValue ? newValue.id.toString() : '';
                              setRecipeForm({ ...recipeForm, sections: newSections });
                            }}
                            renderInput={(params) => (
                              <TextField 
                                {...params} 
                                label="Съставка" 
                                sx={{ flexGrow: 1, minWidth: 200 }}
                                error={!!validationErrors[`section_${sectionIdx}_ing_${ingIdx}`]}
                                helperText={validationErrors[`section_${sectionIdx}_ing_${ingIdx}`]}
                              />
                            )}
                            isOptionEqualToValue={(option, value) => option.id === value.id}
                          />
                          <ValidatedTextField
                            size="small"
                            label="Количество"
                            value={ing.quantityGross?.toString() || ''}
                            onChange={(value) => {
                              const newSections = [...recipeForm.sections];
                              newSections[sectionIdx].ingredients[ingIdx].quantityGross = value;
                              setRecipeForm({ ...recipeForm, sections: newSections });
                            }}
                            tooltip="Количество в грамове (брутно)"
                            type="number"
                            error={validationErrors[`section_${sectionIdx}_qty_${ingIdx}`]}
                            sx={{ width: 100 }}
                          />
                          <IconButton size="small" color="error" onClick={() => handleRemoveIngredient(sectionIdx, ingIdx)}>
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      ))}
                      <Button startIcon={<AddIcon />} size="small" onClick={() => handleAddIngredient(sectionIdx)}>
                        Добави съставка
                      </Button>
                    </Grid>

                    {/* Totals */}
                    <Grid size={{ xs: 12 }}>
                      <Box sx={{ mt: 2, p: 1, bgcolor: '#e3f2fd', borderRadius: 1 }}>
                        <Typography variant="body2">
                          ОБЩО: {totals.totalGross.toFixed(1)}g | НЕТО: {totals.totalNet.toFixed(1)}g
                        </Typography>
                      </Box>
                    </Grid>

                    {/* Steps */}
                    <Grid size={{ xs: 12 }}>
                      <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                        СТЪПКИ:
                      </Typography>
                      {section.steps.map((step: any, stepIdx: number) => (
                        <Box key={stepIdx} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                          <TextField
                            size="small"
                            label={`Стъпка ${stepIdx + 1}`}
                            value={step.name}
                            onChange={(e) => {
                              const newSections = [...recipeForm.sections];
                              newSections[sectionIdx].steps[stepIdx].name = e.target.value;
                              setRecipeForm({ ...recipeForm, sections: newSections });
                            }}
                            sx={{ flexGrow: 1 }}
                            placeholder="Описание на стъпката..."
                          />
                          <FormControl size="small" sx={{ minWidth: 120 }}>
                            <InputLabel>Станция</InputLabel>
                            <Select
                              value={step.workstationId}
                              label="Станция"
                              onChange={(e) => {
                                const newSections = [...recipeForm.sections];
                                newSections[sectionIdx].steps[stepIdx].workstationId = e.target.value;
                                setRecipeForm({ ...recipeForm, sections: newSections });
                              }}
                            >
                              {data?.workstations?.map((w: any) => (
                                <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                          <IconButton size="small" color="error" onClick={() => handleRemoveStep(sectionIdx, stepIdx)}>
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      ))}
                      <Button startIcon={<AddIcon />} size="small" onClick={() => handleAddStep(sectionIdx)}>
                        Добави стъпка
                      </Button>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRecipeModal(false)}>Отказ</Button>
          <Button onClick={handleAddRecipe} variant="contained" disabled={!recipeForm.name}>Запази Рецепта</Button>
        </DialogActions>
      </Dialog>

      {/* Modal: Детайли на Рецепта */}
      <Dialog open={!!selectedRecipe} onClose={() => setSelectedRecipe(null)} fullWidth maxWidth="md" PaperProps={{ sx: { maxHeight: '80vh' } }}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <RecipeIcon color="primary" />
          {selectedRecipe?.name}
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" color="textSecondary">Добив</Typography>
              <Typography variant="h6">{selectedRecipe?.yieldQuantity} {selectedRecipe?.yieldUnit}</Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" color="textSecondary">Срок на годност</Typography>
              <Typography variant="h6">{selectedRecipe?.shelfLifeDays} дни</Typography>
            </Grid>
            
            <Grid size={{ xs: 12 }}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>Съставки</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Съставка</TableCell>
                    <TableCell align="right">Брутно</TableCell>
                    <TableCell align="right">Нетно</TableCell>
                    <TableCell align="right">% Отпадък</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedRecipe?.ingredients?.map((ing: any, idx: number) => {
                    const waste = ing.quantityGross > 0 ? ((ing.quantityGross - ing.quantityNet) / ing.quantityGross * 100).toFixed(1) : '0';
                    return (
                      <TableRow key={idx}>
                        <TableCell>{ing.ingredient.name}</TableCell>
                        <TableCell align="right">{ing.quantityGross} {ing.ingredient.unit}</TableCell>
                        <TableCell align="right">{ing.quantityNet} {ing.ingredient.unit}</TableCell>
                        <TableCell align="right">{waste}%</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, mt: 2 }}>Стъпки</Typography>
              {selectedRecipe?.steps?.length > 0 ? (
                <List>
                  {selectedRecipe.steps.map((step: any, idx: number) => (
                    <ListItem key={idx} sx={{ borderBottom: '1px solid #eee' }}>
                      <ListItemText 
                        primary={`${idx + 1}. ${step.name}`} 
                        secondary={step.estimatedDurationMinutes ? `~${step.estimatedDurationMinutes} мин` : ''}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">Няма дефинирани стъпки</Typography>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button color="error" onClick={async () => {
            if (confirm('Сигурни ли сте, че искате да изтриете тази рецепта?')) {
              try {
                await deleteRecipe({ variables: { id: selectedRecipe.id } });
                setSelectedRecipe(null);
                refetch();
              } catch (err) {
                console.error(err);
              }
            }
          }}>
            Изтрий
          </Button>
          <Button onClick={() => setSelectedRecipe(null)}>Затвори</Button>
        </DialogActions>
      </Dialog>

      {/* Barcode Scanner Dialog */}
      <Dialog open={scannerOpen} onClose={() => setScannerOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Сканирай баркод</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Въведи баркод"
            sx={{ mt: 1 }}
            value={scannedBarcode}
            autoFocus
            onChange={(e) => setScannedBarcode(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && scannedBarcode) {
                const found = data?.ingredients?.find((i: any) => i.barcode === scannedBarcode);
                if (found) {
                  const newSections = [...recipeForm.sections];
                  newSections[0].ingredients = [...(newSections[0].ingredients || []), { 
                    ingredientId: found.id.toString(), 
                    quantityGross: '' 
                  }];
                  setRecipeForm({
                    ...recipeForm,
                    sections: newSections
                  });
                  setScannedBarcode('');
                  setScannerOpen(false);
                } else {
                  alert('Продукт с този баркод не е намерен в склада!');
                }
              }
            }}
          />
          <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
            Сканирай баркода или го въведи ръчно и натисни Enter
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScannerOpen(false)}>Затвори</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default RecipesPage;
