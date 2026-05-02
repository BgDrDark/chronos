import React from 'react';
import { TextField, InputAdornment, TextFieldProps } from '@mui/material';
import { InfoIcon } from './InfoIcon';

export interface ValidatedTextFieldProps extends Omit<TextFieldProps, 'onChange'> {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  tooltip?: string;
  error?: any;
}

export const ValidatedTextField: React.FC<ValidatedTextFieldProps> = ({
  label, value, onChange, tooltip, error, type = 'text', ...props
}) => {
  const showError = !!error;
  const helperText = typeof error === 'string' ? error : error?.message;
  const hasValue = value !== '' && value !== null && value !== undefined;

  return (
    <TextField
      label={label}
      value={value}
      onChange={(e) => {
        const val = e.target.value;
        if (type === 'number') {
          onChange(val.replace(/[^0-9.]/g, ''));
        } else {
          onChange(val);
        }
      }}
      error={showError}
      helperText={helperText}
      type={type === 'number' ? 'text' : type}
      size="small"
      fullWidth
      slotProps={{
        input: {
          endAdornment: tooltip ? (
            <InputAdornment position="end">
              <InfoIcon helpText={tooltip} />
            </InputAdornment>
          ) : undefined
        }
      }}
      InputProps={{
        sx: {
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
      {...props}
    />
  );
};
