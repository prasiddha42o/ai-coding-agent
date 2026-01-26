"use client";

import { useQuery } from "@tanstack/react-query";
import * as sessionsService from "@/services/sessions";

export function useSessionsList(repositoryId: string) {
  return useQuery({
    queryKey: ["repositories", repositoryId, "sessions"],
    queryFn: () => sessionsService.listSessions(repositoryId),
  });
}

export function useSession(sessionId: string) {
  return useQuery({
    queryKey: ["sessions", sessionId],
    queryFn: () => sessionsService.getSession(sessionId),
  });
}

export function useSessionPlans(sessionId: string) {
  return useQuery({
    queryKey: ["sessions", sessionId, "plans"],
    queryFn: () => sessionsService.listPlans(sessionId),
  });
}

export function usePlanChanges(planId: string) {
  return useQuery({
    queryKey: ["plans", planId, "changes"],
    queryFn: () => sessionsService.listPlanChanges(planId),
  });
}

export function useSessionTestRuns(sessionId: string) {
  return useQuery({
    queryKey: ["sessions", sessionId, "tests"],
    queryFn: () => sessionsService.listTestRuns(sessionId),
  });
}

export function useSessionCommits(sessionId: string) {
  return useQuery({
    queryKey: ["sessions", sessionId, "commits"],
    queryFn: () => sessionsService.listCommits(sessionId),
  });
}
