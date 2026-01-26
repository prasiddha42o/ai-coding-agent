import { apiFetch } from "@/services/api-client";
import type { CodingSession, Plan } from "@/types/api";

export function createSession(repositoryId: string): Promise<CodingSession> {
  return apiFetch<CodingSession>(`/repositories/${repositoryId}/sessions`, { method: "POST" });
}

export function listSessions(repositoryId: string): Promise<CodingSession[]> {
  return apiFetch<CodingSession[]>(`/repositories/${repositoryId}/sessions`);
}

export function createPlan(sessionId: string, prompt: string): Promise<Plan> {
  return apiFetch<Plan>(`/sessions/${sessionId}/plans`, { method: "POST", body: { prompt } });
}

export function listPlans(sessionId: string): Promise<Plan[]> {
  return apiFetch<Plan[]>(`/sessions/${sessionId}/plans`);
}

export function approvePlan(planId: string): Promise<Plan> {
  return apiFetch<Plan>(`/plans/${planId}/approve`, { method: "POST" });
}

export function rejectPlan(planId: string): Promise<Plan> {
  return apiFetch<Plan>(`/plans/${planId}/reject`, { method: "POST" });
}
