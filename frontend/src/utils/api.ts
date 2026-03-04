export const getApiUrl = (path: string = '') => {
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
