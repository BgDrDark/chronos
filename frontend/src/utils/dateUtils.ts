import { format, parseISO, isValid } from 'date-fns';
import { bg } from 'date-fns/locale';

export const formatDate = (date: string | Date | null | undefined, formatStr: string = 'dd-MM-yyyy'): string => {
  if (!date) return '';
  
  let d: Date;
  
  if (typeof date === 'string') {
    // Check if it looks like a date string before parsing
    if (!date.trim()) return '';
    d = parseISO(date);
  } else {
    d = date;
  }

  if (!isValid(d)) {
    return date.toString(); // Fallback to original string if invalid
  }

  try {
    return format(d, formatStr, { locale: bg });
  } catch (e) {
    console.error("Date formatting error", e);
    return '';
  }
};
