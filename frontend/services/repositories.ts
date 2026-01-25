import { apiFetch } from "@/services/api-client";
import type { KnowledgeGraph, Repository } from "@/types/api";

export function listRepositories(): Promise<Repository[]> {
  return apiFetch<Repository[]>("/repositories");
}

export function getRepository(id: string): Promise<Repository> {
  return apiFetch<Repository>(`/repositories/${id}`);
}

export function importFromGithub(
  sourceUrl: string,
  name: string | null,
  branch: string | null,
): Promise<Repository> {
  return apiFetch<Repository>("/repositories/github", {
    method: "POST",
    body: { source_url: sourceUrl, name, branch },
  });
}

export function importFromZip(file: File, name: string | null): Promise<Repository> {
  const formData = new FormData();
  formData.append("file", file);
  if (name) formData.append("name", name);
  return apiFetch<Repository>("/repositories/zip", { method: "POST", body: formData });
}

export function refreshRepository(id: string): Promise<Repository> {
  return apiFetch<Repository>(`/repositories/${id}/refresh`, { method: "POST" });
}

export function deleteRepository(id: string): Promise<void> {
  return apiFetch<void>(`/repositories/${id}`, { method: "DELETE" });
}

export function getKnowledgeGraph(id: string): Promise<KnowledgeGraph> {
  return apiFetch<KnowledgeGraph>(`/repositories/${id}/graph`);
}
