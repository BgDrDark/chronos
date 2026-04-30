import React, { useState, useMemo } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, Grid, Divider, Box, Typography, InputAdornment
} from '@mui/material';
import { type RecipeWithPrice } from '../types';
import { useCurrency, formatCurrencyValue, getCurrencySymbolForCurrency } from '../currencyContext';
import { InfoIcon } from './ui/InfoIcon';
import { recipeFieldsHelp, commonFieldsHelp } from './ui/fieldsHelpText';

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
  const { currency } = useCurrency();
  const currencySymbol = getCurrencySymbolForCurrency(currency);
  
  const [markupPercentage, setMarkupPercentage] = useState(() => recipe?.markupPercentage?.toString() ?? '50');
  const [premiumAmount, setPremiumAmount] = useState(() => recipe?.premiumAmount?.toString() ?? '0');
  const [portions, setPortions] = useState(() => recipe?.portions?.toString() ?? '12');
  const [reason, setReason] = useState('');

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
      reason: reason || null
    });
  };

  const formatPrice = (value: number | string | null | undefined): string => {
    return formatCurrencyValue(value, currency);
  };

  return (
    <Dialog key={open ? 'open' : 'closed'} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Редактиране на цена - {recipe?.name}</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Текуща себестойност: <strong>{formatPrice(recipe?.costPrice || 0)}</strong>
              </Typography>
            </Grid>

            <Grid size={{ xs: 6 }}>
              <TextField
                label="Марж %"
                type="number"
                fullWidth
                size="small"
                value={markupPercentage}
                onChange={(e) => setMarkupPercentage(e.target.value)}
                slotProps={{ htmlInput: { min: 0, step: 0.1 }, input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={recipeFieldsHelp.markupPercentage} /></InputAdornment> } }}
              />
            </Grid>

            <Grid size={{ xs: 6 }}>
              <TextField
                label={`Надценка (${currencySymbol})`}
                type="number"
                fullWidth
                size="small"
                value={premiumAmount}
                onChange={(e) => setPremiumAmount(e.target.value)}
                slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
              />
            </Grid>

            <Grid size={{ xs: 6 }}>
              <TextField
                label="Брой порции"
                type="number"
                fullWidth
                size="small"
                value={portions}
                onChange={(e) => setPortions(e.target.value)}
                slotProps={{ htmlInput: { min: 1, step: 1 }, input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={recipeFieldsHelp.defaultPieces} /></InputAdornment> } }}
              />
            </Grid>

            <Grid size={{ xs: 6 }}>
              <TextField
                label="Причина за промяна"
                fullWidth
                size="small"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="напр. Поскъпване на продукти"
                slotProps={{ input: { endAdornment: <InputAdornment position="end"><InfoIcon helpText={commonFieldsHelp.notes} /></InputAdornment> } }}
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
                  {formatPrice(preview.markupAmount)}
                </Typography>
              </Grid>

              <Grid size={{ xs: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Финална цена:
                </Typography>
              </Grid>
              <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                <Typography variant="body1" fontWeight="bold">
                  {formatPrice(preview.finalPrice)}
                </Typography>
              </Grid>

              <Grid size={{ xs: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Цена/порция:
                </Typography>
              </Grid>
              <Grid size={{ xs: 6 }} sx={{ textAlign: 'right' }}>
                <Typography variant="body1" fontWeight="bold" color="primary">
                  {formatPrice(preview.portionPrice)}
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
