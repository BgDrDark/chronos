export const getCsrfToken = (): string | null => {
  const name = 'csrf_token=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return null;
};

export const fetchWithCsrf = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const csrfToken = getCsrfToken();
  
  const headers = {
    ...options.headers,
  };
  
  if (csrfToken) {
    (headers as Record<string, string>)['X-CSRFToken'] = csrfToken;
  }
  
  return fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });
};
