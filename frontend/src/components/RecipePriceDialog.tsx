import React, { useMemo } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, Grid, Divider, Box, Typography
} from '@mui/material';
import { type RecipeWithPrice } from '../types';

interface RecipePriceDialogProps {
  open: boolean;
  recipe: RecipeWithPrice | null;
  onClose: () => void;
  onSave: (data: {
    markupPercentage: number | null;
    premiumAmount: number | null;
    portions: number | null;
    reason: string | null;
  }) => void;
  loading?: boolean;
}

interface PricePreview {
  markupAmount: number;
  finalPrice: number;
  portionPrice: number;
}

const RecipePriceDialog: React.FC<RecipePriceDialogProps> = ({
  open,
  recipe,
  onClose,
  onSave,
  loading = false
}) => {
  const markupPercentage = recipe?.markupPercentage?.toString() ?? '50';
  const premiumAmount = recipe?.premiumAmount?.toString() ?? '0';
  const portions = recipe?.portions?.toString() ?? '1';

  const preview = useMemo((): PricePreview => {
    const costPrice = recipe?.costPrice || 0;
    const markupPct = parseFloat(markupPercentage) || 0;
    const premium = parseFloat(premiumAmount) || 0;
    const portionsNum = parseInt(portions) || 1;

    const markupAmount = costPrice * (markupPct / 100);
    const finalPrice = costPrice + markupAmount + premium;
    const portionPrice = finalPrice / portionsNum;

    return { markupAmount, finalPrice, portionPrice };
  }, [recipe?.costPrice, markupPercentage, premiumAmount, portions]);

  const handleSave = () => {
    onSave({
      markupPercentage: markupPercentage ? parseFloat(markupPercentage) : null,
      premiumAmount: premiumAmount ? parseFloat(premiumAmount) : null,
      portions: portions ? parseInt(portions) : null,
      reason: null
    });
  };

  const formatPrice = (value: number | string | null | undefined): string => {
    if (value === null || value === undefined) return '0.00';
    const num = typeof value === 'string' ? parseFloat(value) : Number(value);
    if (isNaN(num)) return '0.00';
    return num.toFixed(2);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Редактиране на цена - {recipe?.name}</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Текуща себестойност: <strong>{formatPrice(recipe?.costPrice || 0)} лв.</strong>
              </Typography>
            </Grid>

            <Grid size={{ xs: 6 }}>
              <TextField
                label="Markup %"
                type="number"
                fullWidth
                size="small"
                defaultValue={markupPercentage}
                slotProps={{ htmlInput: { min: 0, step: 0.1 } }}
              />
            </Grid>

            <Grid size={{ xs: 6 }}>
              <TextField
                label="Надценка (лв.)"
                type="number"
                fullWidth
                size="small"
                defaultValue={premiumAmount}
                slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
              />
            </Grid>

            <Grid size={{ xs: 6 }}>
              <TextField
                label="Брой порции"
                type="number"
                fullWidth
                size="small"
                defaultValue={portions}
                slotProps={{ htmlInput: { min: 1, step: 1 } }}
              />
            </Grid>

            <Grid size={{ xs: 6 }}>
              <TextField
                label="Причина за промяна"
                fullWidth
                size="small"
                placeholder="напр. Поскъпване на продукти"
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          <Box
            sx={{
              p: 2,
              backgroundColor: 'grey.50',
              borderRadius: 1,
              border: '1px solid',
              borderColor: 'grey.300'
            }}
          >
            <Typography variant="subtitle2" gutterBottom>
              Преглед на цената:
            </Typography>
            <Grid container spacing={1}>
              <Grid size={{ xs: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Markup сума:
                </Typography>
              </Grid>
              <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                <Typography variant="body2">
                  {formatPrice(preview.markupAmount)} лв.
                </Typography>
              </Grid>

              <Grid size={{ xs: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Финална цена:
                </Typography>
              </Grid>
              <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                <Typography variant="body1" fontWeight="bold">
                  {formatPrice(preview.finalPrice)} лв.
                </Typography>
              </Grid>

              <Grid size={{ xs: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Цена/порция:
                </Typography>
              </Grid>
              <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                <Typography variant="body1" fontWeight="bold" color="primary">
                  {formatPrice(preview.portionPrice)} лв.
                </Typography>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Отказ
        </Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={loading}
        >
          {loading ? 'Запис...' : 'Запиши'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RecipePriceDialog;
