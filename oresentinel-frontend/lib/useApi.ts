'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

interface UseApiState<T> {
  data: T;
  loading: boolean;
  error: string | null;
  /** True while `data` is still the mock fixture (backend not answering). */
  usingFallback: boolean;
  refetch: () => void;
}

/**
 * One hook every widget uses to fetch its slice of the dashboard.
 *
 * It is deliberately forgiving: if the backend is unreachable, the widget
 * keeps rendering `fallback` (the typed mock fixture) and surfaces
 * `usingFallback` so you can show a "demo data" badge instead of a blank card.
 *
 * TODO(api): nothing to do here — the call site passes the real fetcher,
 * e.g. `useApi(api.dashboardKpis, mockKpis)`.
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  fallback: T,
  deps: unknown[] = [],
): UseApiState<T> {
  const [data, setData] = useState<T>(fallback);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingFallback, setUsingFallback] = useState(false);
  const mounted = useRef(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      if (!mounted.current) return;
      setData(result);
      setUsingFallback(false);
    } catch (err) {
      if (!mounted.current) return;
      // Backend not wired yet / offline -> keep the mock fixture on screen.
      setError(err instanceof Error ? err.message : 'Request failed');
      setData(fallback);
      setUsingFallback(true);
    } finally {
      if (mounted.current) setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mounted.current = true;
    void load();
    return () => {
      mounted.current = false;
    };
  }, [load]);

  return { data, loading, error, usingFallback, refetch: load };
}
