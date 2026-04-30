import { ApolloClient, InMemoryCache, createHttpLink, from } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';

const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        globalPayrollConfig: {
          merge(existing, incoming) {
            return incoming;
          },
        },
      },
    },
    Recipe: {
      fields: {
        markupPercentage: {
          read( markupPercentage) {
            if (markupPercentage === null || markupPercentage === undefined) return null;
            return typeof markupPercentage === 'string' ? parseFloat(markupPercentage) : markupPercentage;
          },
        },
        costPrice: {
          read(costPrice) {
            if (costPrice === null || costPrice === undefined) return null;
            return typeof costPrice === 'string' ? parseFloat(costPrice) : costPrice;
          },
        },
        premiumAmount: {
          read(premiumAmount) {
            if (premiumAmount === null || premiumAmount === undefined) return null;
            return typeof premiumAmount === 'string' ? parseFloat(premiumAmount) : premiumAmount;
          },
        },
        sellingPrice: {
          read(sellingPrice) {
            if (sellingPrice === null || sellingPrice === undefined) return null;
            return typeof sellingPrice === 'string' ? parseFloat(sellingPrice) : sellingPrice;
          },
        },
      },
    },
  },
});

const getApiUrl = (path: string = 'graphql') => {
  const envUrl = import.meta.env.VITE_API_URL;
  const baseUrl = envUrl ? (envUrl.endsWith('/') ? envUrl : `${envUrl}/`) : '/';
  
  if (envUrl && envUrl.startsWith('http')) {
      return `${baseUrl}${path}`;
  }

  const isDev = import.meta.env.DEV;
  if (isDev) {
    return `http://localhost:14240/${path}`;
  }
  
  return `/${path}`;
};

// Read CSRF token from cookie (non-HttpOnly)
const getCsrfToken = (): string | null => {
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

const httpLink = createHttpLink({
  uri: getApiUrl('graphql'),
  credentials: 'include', // Send cookies automatically
});

const authLink = setContext((_, { headers }) => {
  // Token is now in HttpOnly cookie - no need to read from localStorage
  // But we still need CSRF token for double-submit pattern
  const csrfToken = getCsrfToken();
  return {
    headers: {
      ...headers,
      'X-CSRFToken': csrfToken || '',
    }
  }
});

const errorLink = onError(({ graphQLErrors, networkError, operation }) => {
  // Check for network errors (like token expiry)
  if (networkError) {
    const errorStr = networkError.toString();
    if (errorStr.includes('expired') || errorStr.includes('500') || errorStr.includes('Internal Server Error')) {
      window.location.href = '/login';
      return;
    }
  }
  
  if (graphQLErrors) {
    for (const err of graphQLErrors) {
      const authErrors = [
        'Could not validate credentials',
        'Not authenticated',
        'Not authorized',
        'expired_token',
        'token is expired',
        'UNAUTHENTICATED',
        'Не сте автентикирани',
        'Not authenticated',
        'AuthenticationException'
      ];
      
      const isAuthError = authErrors.some(e => 
        err.message.includes(e) || err.extensions?.code === 'UNAUTHENTICATED'
      );
      
      if (isAuthError) {
        // Avoid infinite loops if refresh itself fails
        if (operation.operationName === 'RefreshToken') {
          window.location.href = '/login';
          return;
        }

        // Perform async refresh - cookies are sent automatically with credentials: 'include'
        const csrfToken = getCsrfToken();
        fetch(getApiUrl('auth/refresh'), {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken || '',
            },
            credentials: 'include',
        }).then(async (res) => {
            if (res.ok) {
                // Token is refreshed and stored in cookie by backend
                return true;
            }
            throw new Error('Refresh failed');
        }).catch(() => {
            window.location.href = '/login';
            return false;
        });
      }
    }
  }
});

const client = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache: cache,
});

export default client;
