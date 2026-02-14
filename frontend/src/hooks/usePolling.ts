"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { POLL_INTERVAL } from "@/lib/constants";

interface UsePollingOptions<T> {
  fetcher: (signal: AbortSignal) => Promise<T>;
  interval?: number;
  enabled?: boolean;
}

interface UsePollingResult<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refetch: () => void;
}

export function usePolling<T>({
  fetcher,
  interval = POLL_INTERVAL,
  enabled = true,
}: UsePollingOptions<T>): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  const triggerRef = useRef(0);

  // Keep fetcher ref updated without triggering re-fetches
  fetcherRef.current = fetcher;

  const refetch = useCallback(() => {
    triggerRef.current += 1;
    // Force a state update to trigger the effect
    setLoading((prev) => {
      // We need a fresh trigger, so toggle to ensure effect fires
      return prev;
    });
    // Use a custom event to trigger refetch
    triggerRef.current += 1;
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const controller = new AbortController();
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const doFetch = async () => {
      try {
        const result = await fetcherRef.current(controller.signal);
        if (!controller.signal.aborted) {
          setData(result);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err : new Error(String(err)));
          setLoading(false);
        }
      }
    };

    doFetch();
    intervalId = setInterval(doFetch, interval);

    return () => {
      controller.abort();
      if (intervalId) clearInterval(intervalId);
    };
  }, [interval, enabled]);

  // Refetch mechanism: separate effect watching trigger
  const [refetchCount, setRefetchCount] = useState(0);
  const realRefetch = useCallback(() => {
    setRefetchCount((c) => c + 1);
  }, []);

  useEffect(() => {
    if (refetchCount === 0 || !enabled) return;
    const controller = new AbortController();

    const doFetch = async () => {
      try {
        const result = await fetcherRef.current(controller.signal);
        if (!controller.signal.aborted) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      }
    };

    doFetch();
    return () => controller.abort();
  }, [refetchCount, enabled]);

  return { data, error, loading, refetch: realRefetch };
}
