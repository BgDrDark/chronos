import { Box, FormLabel, FormControl, FormHelperText, TextFieldProps } from '@mui/material';
import { InfoIcon } from './InfoIcon';

interface FieldTooltipProps {
  label: string;
  helpText: string;
  children: React.ReactNode;
  required?: boolean;
  error?: string | boolean;
  helperText?: string;
  disabled?: boolean;
}

export const FieldTooltip: React.FC<FieldTooltipProps> = ({
  label,
  helpText,
  children,
  required,
  error,
  helperText,
  disabled,
}) => {
  return (
    <FormControl fullWidth error={!!error} disabled={disabled}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
        <FormLabel
          sx={{
            fontSize: '0.875rem',
            color: disabled ? 'text.disabled' : 'text.primary',
            fontWeight: 500,
          }}
        >
          {label}
          {required && <span style={{ color: 'red', marginLeft: 2 }}>*</span>}
        </FormLabel>
        {helpText && <InfoIcon helpText={helpText} />}
      </Box>
      {children}
      {(error || helperText) && (
        <FormHelperText sx={{ color: error ? 'error.main' : 'text.secondary' }}>
          {error || helperText}
        </FormHelperText>
      )}
    </FormControl>
  );
};

export default FieldTooltip;
