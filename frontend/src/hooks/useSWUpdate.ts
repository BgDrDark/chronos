import { useRegisterSW } from 'virtual:pwa-register/react';

export function useSWUpdate() {
  const {
    offlineReady: [offlineReady, setOfflineReady],
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r) {
      console.log('SW registered:', r);
    },
    onRegisterError(error) {
      console.error('SW registration error:', error);
    },
  });

  const update = () => updateServiceWorker(true);
  const dismiss = () => {
    setOfflineReady(false);
    setNeedRefresh(false);
  };

  return { offlineReady, needRefresh, update, dismiss };
}
