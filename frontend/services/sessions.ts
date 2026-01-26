import { apiFetch } from "@/services/api-client";
import type { Change, CodingSession, Commit, Plan, TestRun } from "@/types/api";

export function createSession(repositoryId: string): Promise<CodingSession> {
  return apiFetch<CodingSession>(`/repositories/${repositoryId}/sessions`, { method: "POST" });
}

export function listSessions(repositoryId: string): Promise<CodingSession[]> {
  return apiFetch<CodingSession[]>(`/repositories/${repositoryId}/sessions`);
}

export function getSession(sessionId: string): Promise<CodingSession> {
  return apiFetch<CodingSession>(`/sessions/${sessionId}`);
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

export function listPlanChanges(planId: string): Promise<Change[]> {
  return apiFetch<Change[]>(`/plans/${planId}/changes`);
}

export function listTestRuns(sessionId: string): Promise<TestRun[]> {
  return apiFetch<TestRun[]>(`/sessions/${sessionId}/tests`);
}

export function listCommits(sessionId: string): Promise<Commit[]> {
  return apiFetch<Commit[]>(`/sessions/${sessionId}/commits`);
}
