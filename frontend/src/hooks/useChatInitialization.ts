/**
 * Hook for initializing the shopping API
 */
import { useState, useEffect } from 'react';
import { shoppingAPI } from '@/lib/shopping-api';

export function useChatInitialization() {
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        await shoppingAPI.initialize();
        setIsInitialized(true);
        setError(null);
      } catch (err) {
        console.error('Failed to initialize:', err);
        setIsInitialized(false);
        setError(err instanceof Error ? err.message : 'Failed to connect to the shopping assistant');
      }
    };

    init();
  }, []);

  return {
    isInitialized,
    error,
  };
}

