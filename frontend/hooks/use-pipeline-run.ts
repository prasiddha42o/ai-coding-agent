"use client";

import { useCallback, useRef, useState } from "react";
import { apiStream, ApiError } from "@/services/api-client";
import type { PipelineEvent } from "@/types/api";

export function usePipelineRun() {
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Guards against a stale run's late-arriving events landing after reset()
  // or a fresh run has started (fetch has no cancel-and-forget primitive
  // we're using here, so we filter by run identity instead).
  const runIdRef = useRef(0);

  const run = useCallback(async (planId: string) => {
    const runId = ++runIdRef.current;
    setEvents([]);
    setError(null);
    setIsRunning(true);

    try {
      await apiStream(`/plans/${planId}/run`, (raw) => {
        if (runIdRef.current !== runId) return;
        setEvents((previous) => [...previous, raw as unknown as PipelineEvent]);
      });
    } catch (err) {
      if (runIdRef.current === runId) {
        setError(err instanceof ApiError ? err.detail : "The pipeline run failed unexpectedly.");
      }
    } finally {
      if (runIdRef.current === runId) {
        setIsRunning(false);
      }
    }
  }, []);

  const reset = useCallback(() => {
    runIdRef.current += 1;
    setEvents([]);
    setError(null);
    setIsRunning(false);
  }, []);

  return { events, isRunning, error, run, reset };
}
