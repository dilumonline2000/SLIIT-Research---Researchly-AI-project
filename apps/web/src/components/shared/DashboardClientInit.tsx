'use client';

import { useEffect } from 'react';
import { useAIProviderStore } from '@/stores/aiProviderStore';

export function DashboardClientInit({ children }: { children: React.ReactNode }) {
  const checkLocalAvailability = useAIProviderStore((s) => s.checkLocalAvailability);

  useEffect(() => {
    checkLocalAvailability();
  }, [checkLocalAvailability]);

  return <>{children}</>;
}
