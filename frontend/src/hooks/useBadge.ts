export function useBadge() {
  const setBadge = async (count: number) => {
    if ('setAppBadge' in navigator) {
      try {
        await navigator.setAppBadge(count);
      } catch (e) {
        console.error('Failed to set app badge:', e);
      }
    }
  };

  const clearBadge = async () => {
    if ('clearAppBadge' in navigator) {
      try {
        await navigator.clearAppBadge();
      } catch (e) {
        console.error('Failed to clear app badge:', e);
      }
    }
  };

  return { setBadge, clearBadge };
}
