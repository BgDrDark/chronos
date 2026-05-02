import dayjs from 'dayjs';
import 'dayjs/locale/bg';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.locale('bg');

export const formatDate = (date: string | Date | null | undefined, formatStr: string = 'DD-MM-YYYY'): string => {
  if (!date) return '';
  
  let d: dayjs.Dayjs;
  
  if (typeof date === 'string') {
    if (!date.trim()) return '';
    d = dayjs(date);
  } else {
    d = dayjs(date);
  }

  if (!d.isValid()) {
    return date.toString();
  }

  try {
    return d.format(formatStr);
  } catch (e) {
    console.error("Date formatting error", e);
    return '';
  }
};

export const dayjsInstance = dayjs;