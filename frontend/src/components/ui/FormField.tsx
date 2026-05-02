import { TextField, type TextFieldProps } from '@mui/material';
import { useState, useCallback } from 'react';
import { InfoIcon } from './InfoIcon';
import { fieldsHelp } from './fieldsHelpText';

interface FormFieldProps extends Omit<TextFieldProps, 'label'> {
  fieldId: string;
  label: string;
  helpText?: string;
  onNumberChange?: (value: string) => void;
}

export const FormField: React.FC<FormFieldProps> = ({
  fieldId,
  label,
  helpText,
  value,
  onChange,
  type = 'text',
  onNumberChange,
  ...props
}) => {
  const resolvedHelpText = helpText || fieldsHelp[fieldId as keyof typeof fieldsHelp] || '';
  const [localValue, setLocalValue] = useState(value || '');

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      let newValue = e.target.value;
      
      if (type === 'number') {
        newValue = newValue.replace(/[^0-9.]/g, '');
      }
      
      setLocalValue(newValue);
      
      if (onChange) {
        onChange(e as any);
      }
      
      if (onNumberChange) {
        onNumberChange(newValue);
      }
    },
    [onChange, onNumberChange, type]
  );

  return (
    <TextField
      label={
        resolvedHelpText ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            {label}
            <InfoIcon helpText={resolvedHelpText} />
          </span>
        ) : (
          label
        )
      }
      value={value !== undefined ? value : localValue}
      onChange={handleChange}
      type={type}
      {...props}
    />
  );
};

export default FormField;
