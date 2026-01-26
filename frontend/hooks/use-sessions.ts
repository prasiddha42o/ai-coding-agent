"use client";

import { useMutation } from "@tanstack/react-query";
import * as sessionsService from "@/services/sessions";

export function useCreateSession() {
  return useMutation({
    mutationFn: (repositoryId: string) => sessionsService.createSession(repositoryId),
  });
}

export function useCreatePlan() {
  return useMutation({
    mutationFn: ({ sessionId, prompt }: { sessionId: string; prompt: string }) =>
      sessionsService.createPlan(sessionId, prompt),
  });
}

export function useApprovePlan() {
  return useMutation({
    mutationFn: (planId: string) => sessionsService.approvePlan(planId),
  });
}

export function useRejectPlan() {
  return useMutation({
    mutationFn: (planId: string) => sessionsService.rejectPlan(planId),
  });
}
