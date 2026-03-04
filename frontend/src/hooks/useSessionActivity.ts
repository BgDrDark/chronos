import { useEffect, useRef, useCallback, useState } from 'react';

const IDLE_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes
const REFRESH_BEFORE_MS = 5 * 60 * 1000; // 5 minutes before expiry

interface UseSessionActivityOptions {
  idleTimeoutMs?: number;
  refreshBeforeMs?: number;
  onIdleTimeout: () => void;
  onRefreshNeeded?: () => void;
}

export const useSessionActivity = ({
  idleTimeoutMs = IDLE_TIMEOUT_MS,
  refreshBeforeMs = REFRESH_BEFORE_MS,
  onIdleTimeout,
  onRefreshNeeded,
}: UseSessionActivityOptions) => {
  const lastActivityRef = useRef<number>(Date.now());
  const isRefreshingRef = useRef<boolean>(false);
  const [isIdle, setIsIdle] = useState(false);

  const resetIdleTimer = useCallback(() => {
    lastActivityRef.current = Date.now();
    setIsIdle(false);
  }, []);

  const refreshSession = useCallback(async () => {
    if (isRefreshingRef.current) return;
    
    isRefreshingRef.current = true;
    try {
      const csrfToken = getCsrfToken();
      const response = await fetch(getApiUrl('auth/refresh'), {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken || '',
        },
        credentials: 'include',
      });
      
      if (response.ok) {
        // Reset activity timer after successful refresh
        resetIdleTimer();
      } else {
        // Refresh failed - trigger logout
        onIdleTimeout();
      }
    } catch (error) {
      console.error('Session refresh failed:', error);
      onIdleTimeout();
    } finally {
      isRefreshingRef.current = false;
    }
  }, [onIdleTimeout, resetIdleTimer]);

  const shouldRefresh = useCallback((): boolean => {
    // This is a simplified check - in production you might want to 
    // track token expiry more precisely
    const timeSinceLastActivity = Date.now() - lastActivityRef.current;
    // If we're approaching the idle timeout, refresh the session
    return timeSinceLastActivity < idleTimeoutMs - refreshBeforeMs;
  }, [idleTimeoutMs, refreshBeforeMs]);

  // Activity event handlers
  useEffect(() => {
    const activityEvents = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click'];

    const handleActivity = () => {
      const wasIdle = isIdle;
      resetIdleTimer();
      
      // If we were idle and became active, check if we need to refresh
      if (wasIdle) {
        if (shouldRefresh() && onRefreshNeeded) {
          refreshSession();
        }
      }
    };

    // Add event listeners
    activityEvents.forEach(event => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    return () => {
      activityEvents.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
    };
  }, [isIdle, resetIdleTimer, shouldRefresh, onRefreshNeeded, refreshSession]);

  // Idle check interval
  useEffect(() => {
    const checkIdle = () => {
      const timeSinceLastActivity = Date.now() - lastActivityRef.current;
      
      if (timeSinceLastActivity >= idleTimeoutMs) {
        setIsIdle(true);
        onIdleTimeout();
      }
    };

    const intervalId = setInterval(checkIdle, 1000);

    return () => clearInterval(intervalId);
  }, [idleTimeoutMs, onIdleTimeout]);

  return {
    isIdle,
    resetIdleTimer,
    refreshSession,
  };
};

// Helper function to get CSRF token (same as in apolloClient)
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

// Helper function to get API URL (same as in apolloClient)
const getApiUrl = (path: string = 'graphql'): string => {
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

export default useSessionActivity;
