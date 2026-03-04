/**
 * Formats decimal hours into a "X часа и Y минути" string.
 * Example: 9.89 -> "9 часа и 53 минути"
 */
export const formatHours = (decimalHours: number | string): string => {
  const hoursNum = typeof decimalHours === 'string' ? parseFloat(decimalHours) : decimalHours;
  if (isNaN(hoursNum)) return '0 часа и 0 минути';

  const hours = Math.floor(hoursNum);
  const minutes = Math.round((hoursNum - hours) * 60);

  // Handle case where rounding minutes leads to 60
  if (minutes === 60) {
    return `${hours + 1} часа и 0 минути`;
  }

  return `${hours} часа и ${minutes} минути`;
};

/**
 * Formats total minutes into a "Xд Xч Xм" string.
 */
export const formatDuration = (totalMinutes: number): string => {
  const days = Math.floor(totalMinutes / (24 * 60));
  const hours = Math.floor((totalMinutes % (24 * 60)) / 60);
  const minutes = Math.round(totalMinutes % 60);

  const parts = [];
  if (days > 0) parts.push(`${days}д`);
  if (hours > 0 || days > 0) parts.push(`${hours}ч`);
  parts.push(`${minutes}м`);

  return parts.join(' ');
};

/**
 * Formats total minutes into a "HH:MM" string.
 */
export const formatDurationHHMM = (totalMinutes: number): string => {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = Math.round(totalMinutes % 60);
  
  if (minutes === 60) {
      return `${(hours + 1).toString().padStart(2, '0')}:00`;
  }

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
};