export const getApiUrl = (path: string = ''): string => {
  const envUrl = import.meta.env.VITE_API_URL || '';
  
  if (envUrl.startsWith('http')) {
    return `${envUrl}${path ? '/' + path : ''}`;
  }
  
  if (envUrl === '/' || envUrl === '') {
    const base = typeof window !== 'undefined' ? window.location.origin : '';
    return `${base}${path ? '/' + path : ''}`;
  }
  
  return `${envUrl}${path ? '/' + path : ''}`;
};

export const getCsrfToken = (): string | null => {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrf_token='))
    ?.split('=')[1] || null;
};
