import React, { useState } from 'react';
import {
  Container, Typography, Box, Paper, Button, IconButton, Dialog, DialogTitle,
  DialogContent, DialogActions, Grid, Divider, Table, TableBody,
  TableCell, TableHead, TableRow, CircularProgress, Tabs, Tab, Tooltip,
  Chip, Card, CardContent, Alert
} from '@mui/material';
import {
  Edit as EditIcon,
  History as HistoryIcon,
  Calculate as CalculateIcon,
  Refresh as RefreshIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_RECIPES_WITH_PRICES,
  GET_PRICE_HISTORY,
  UPDATE_RECIPE_PRICE,
  CALCULATE_RECIPE_COST,
  RECALCULATE_ALL_RECIPE_COSTS
} from '../graphql/confectioneryMutations';
import { type RecipeWithPrice, type PriceHistory, getErrorMessage } from '../types';
import RecipePriceDialog from '../components/RecipePriceDialog';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const MenuPricingPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState<RecipeWithPrice | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { data, loading, refetch } = useQuery(GET_RECIPES_WITH_PRICES, {
    fetchPolicy: 'cache-and-network',
    onError: (err) => setError(getErrorMessage(err))
  });

  const { data: historyData, refetch: refetchHistory } = useQuery(GET_PRICE_HISTORY, {
    variables: { recipeId: selectedRecipe?.id },
    skip: !selectedRecipe?.id || !historyDialogOpen,
    fetchPolicy: 'cache-and-network',
    onError: (err) => setError(getErrorMessage(err))
  });

  const [updatePrice, { loading: updatingPrice }] = useMutation(UPDATE_RECIPE_PRICE, {
    onCompleted: () => {
      setSuccessMessage('Цената е обновена успешно');
      setEditDialogOpen(false);
      refetch();
      setTimeout(() => setSuccessMessage(null), 3000);
    },
    onError: (err) => setError(getErrorMessage(err))
  });

  const [calculateCost, { loading: calculatingCost }] = useMutation(CALCULATE_RECIPE_COST, {
    onCompleted: (result) => {
      const finalPrice = Number(result.calculateRecipeCost.finalPrice);
      setSuccessMessage(`Себестойността е преизчислена: ${finalPrice.toFixed(2)} лв.`);
      refetch();
      setTimeout(() => setSuccessMessage(null), 3000);
    },
    onError: (err) => setError(getErrorMessage(err))
  });

  const [recalculateAll, { loading: recalculatingAll }] = useMutation(RECALCULATE_ALL_RECIPE_COSTS, {
    onCompleted: (result) => {
      const count = result.recalculateAllRecipeCosts.length;
      setSuccessMessage(`Преизчислени са ${count} рецепти`);
      refetch();
      setTimeout(() => setSuccessMessage(null), 3000);
    },
    onError: (err) => setError(getErrorMessage(err))
  });

  const recipes: RecipeWithPrice[] = data?.recipesWithPrices || [];
  const priceHistory: PriceHistory[] = historyData?.priceHistory || [];

  const handleOpenEdit = (recipe: RecipeWithPrice) => {
    setSelectedRecipe(recipe);
    setEditDialogOpen(true);
    setError(null);
  };

  const handleOpenHistory = (recipe: RecipeWithPrice) => {
    setSelectedRecipe(recipe);
    setHistoryDialogOpen(true);
    refetchHistory();
  };

  const handleSavePrice = (formData: {
    markupPercentage: number | null;
    premiumAmount: number | null;
    portions: number | null;
    reason: string | null;
  }) => {
    if (!selectedRecipe) return;

    updatePrice({
      variables: {
        recipeId: selectedRecipe.id,
        input: {
          markupPercentage: formData.markupPercentage,
          premiumAmount: formData.premiumAmount,
          portions: formData.portions,
          reason: formData.reason
        }
      }
    });
  };

  const handleCalculateCost = (recipeId: number) => {
    calculateCost({ variables: { recipeId } });
  };

  const handleRecalculateAll = () => {
    recalculateAll();
  };

  const formatPrice = (value: number | string | null | undefined): string => {
    if (value === null || value === undefined) return '-';
    const num = typeof value === 'string' ? parseFloat(value) : Number(value);
    if (isNaN(num)) return '-';
    return num.toFixed(2) + ' лв.';
  };

  const formatDate = (dateStr: string | null | undefined): string => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('bg-BG');
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          <MoneyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Цени на Рецепти
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Управление на ценообразуване и себестойност на рецепти
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" onClose={() => setSuccessMessage(null)} sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Всички рецепти" />
          <Tab label="Без цена" />
          <Tab label="Актуални" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ p: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={handleRecalculateAll}
              disabled={recalculatingAll || loading}
            >
              {recalculatingAll ? 'Преизчисляване...' : 'Преизчисли всички'}
            </Button>
            <Button
              variant="outlined"
              onClick={() => refetch()}
              disabled={loading}
            >
              Обнови
            </Button>
          </Box>

          {loading && !data ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow sx={{ backgroundColor: 'grey.100' }}>
                  <TableCell><strong>Рецепта</strong></TableCell>
                  <TableCell><strong>Категория</strong></TableCell>
                  <TableCell align="right"><strong>Себестойност</strong></TableCell>
                  <TableCell align="right"><strong>Markup %</strong></TableCell>
                  <TableCell align="right"><strong>Надценка</strong></TableCell>
                  <TableCell align="right"><strong>Финална цена</strong></TableCell>
                  <TableCell align="right"><strong>Бр. парчета</strong></TableCell>
                  <TableCell align="right"><strong>Цена/бр.</strong></TableCell>
                  <TableCell><strong>Последна промяна</strong></TableCell>
                  <TableCell align="center"><strong>Действия</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recipes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={10} align="center">
                      Няма намерени рецепти
                    </TableCell>
                  </TableRow>
                ) : (
                  recipes.map((recipe) => (
                    <TableRow key={recipe.id} hover>
                      <TableCell>{recipe.name}</TableCell>
                      <TableCell>
                        {recipe.category && <Chip label={recipe.category} size="small" />}
                      </TableCell>
                      <TableCell align="right">{formatPrice(recipe.costPrice)}</TableCell>
                      <TableCell align="right">{typeof recipe.markupPercentage === 'number' ? recipe.markupPercentage.toFixed(1) + '%' : '-'}</TableCell>
                      <TableCell align="right">{formatPrice(recipe.markupAmount)}</TableCell>
                      <TableCell align="right">
                        <strong>{formatPrice(recipe.finalPrice)}</strong>
                      </TableCell>
                      <TableCell align="right">{recipe.defaultPieces || '-'}</TableCell>
                      <TableCell align="right">{formatPrice(recipe.portionPrice)}</TableCell>
                      <TableCell>{formatDate(recipe.lastPriceUpdate)}</TableCell>
                      <TableCell align="center">
                        <Tooltip title="История на цените">
                          <IconButton size="small" onClick={() => handleOpenHistory(recipe)}>
                            <HistoryIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Редактирай цена">
                          <IconButton size="small" onClick={() => handleOpenEdit(recipe)}>
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Преизчисли себестойност">
                          <IconButton size="small" onClick={() => handleCalculateCost(recipe.id)} disabled={calculatingCost}>
                            <CalculateIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell><strong>Рецепта</strong></TableCell>
                <TableCell align="center"><strong>Действия</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recipes.filter(r => !r.costPrice || r.costPrice === 0).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={2} align="center">Всички рецепти имат изчислена себестойност</TableCell>
                </TableRow>
              ) : (
                recipes.filter(r => !r.costPrice || r.costPrice === 0).map((recipe) => (
                  <TableRow key={recipe.id}>
                    <TableCell>{recipe.name}</TableCell>
                    <TableCell align="center">
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<CalculateIcon />}
                        onClick={() => handleCalculateCost(recipe.id)}
                        disabled={calculatingCost}
                      >
                        Изчисли
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box sx={{ p: 2 }}>
            <Grid container spacing={3}>
              {recipes.filter(r => r.finalPrice && r.finalPrice > 0).map((recipe) => (
                <Grid size={{ xs: 12, sm: 6, md: 4 }} key={recipe.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6">{recipe.name}</Typography>
                      {recipe.category && (
                        <Chip label={recipe.category} size="small" sx={{ mt: 1 }} />
                      )}
                      <Divider sx={{ my: 1 }} />
                      <Grid container>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="body2" color="text.secondary">Себестойност:</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                          <Typography variant="body2">{formatPrice(recipe.costPrice)}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="body2" color="text.secondary">Markup:</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                          <Typography variant="body2">{typeof recipe.markupPercentage === 'number' ? recipe.markupPercentage.toFixed(1) + '%' : '-'}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="body2" color="text.secondary">Надценка:</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                          <Typography variant="body2">{formatPrice(recipe.markupAmount)}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="body2" color="text.secondary">Финална цена:</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                          <Typography variant="h6" color="primary">{formatPrice(recipe.finalPrice)}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="body2" color="text.secondary">Бр. парчета:</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                          <Typography variant="body2">{recipe.defaultPieces || '-'}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="body2" color="text.secondary">Цена/бр.:</Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                          <Typography variant="body2" fontWeight="bold">{formatPrice(recipe.portionPrice)}</Typography>
                        </Grid>
                      </Grid>
                      <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                        <Button size="small" onClick={() => handleOpenEdit(recipe)}>
                          Редактирай
                        </Button>
                        <Button size="small" onClick={() => handleOpenHistory(recipe)}>
                          История
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        </TabPanel>
      </Paper>

      <RecipePriceDialog
        open={editDialogOpen}
        recipe={selectedRecipe}
        onClose={() => setEditDialogOpen(false)}
        onSave={handleSavePrice}
        loading={updatingPrice}
      />

      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>История на цени - {selectedRecipe?.name}</DialogTitle>
        <DialogContent>
          {historyData ? (
            priceHistory.length === 0 ? (
              <Typography sx={{ p: 3 }} align="center" color="text.secondary">
                Няма история на цени за тази рецепта
              </Typography>
            ) : (
              <Table size="small" sx={{ mt: 2 }}>
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'grey.100' }}>
                    <TableCell><strong>Дата</strong></TableCell>
                    <TableCell><strong>Предишна цена</strong></TableCell>
                    <TableCell><strong>Нова цена</strong></TableCell>
                    <TableCell><strong>Markup % (преди/след)</strong></TableCell>
                    <TableCell><strong>Надценка (преди/след)</strong></TableCell>
                    <TableCell><strong>Потребител</strong></TableCell>
                    <TableCell><strong>Причина</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {priceHistory.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>{formatDate(entry.createdAt)}</TableCell>
                      <TableCell>{formatPrice(entry.oldSellingPrice)}</TableCell>
                      <TableCell>{formatPrice(entry.newSellingPrice)}</TableCell>
                      <TableCell>
                        {typeof entry.oldMarkupPercentage === 'number' ? entry.oldMarkupPercentage.toFixed(1) : '-'}% → {typeof entry.newMarkupPercentage === 'number' ? entry.newMarkupPercentage.toFixed(1) : '-'}%
                      </TableCell>
                      <TableCell>
                        {formatPrice(entry.oldPremiumAmount)} → {formatPrice(entry.newPremiumAmount)}
                      </TableCell>
                      <TableCell>
                        {entry.user ? `${entry.user.firstName || ''} ${entry.user.lastName || ''}`.trim() || entry.user.email : '-'}
                      </TableCell>
                      <TableCell>{entry.reason || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Затвори</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MenuPricingPage;
