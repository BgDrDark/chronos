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

export const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (response.status === 401) {
    const csrfToken = getCsrfToken();
    const refreshRes = await fetch(getApiUrl('auth/refresh'), {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken || '' },
      credentials: 'include',
    });

    if (refreshRes.ok) {
      return fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
    }

    window.location.href = '/login';
    return response;
  }

  return response;
};
