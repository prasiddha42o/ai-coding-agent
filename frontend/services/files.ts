import { apiFetch } from "@/services/api-client";
import type { FileContent, FileTreeNode } from "@/types/api";

export function getFileTree(repositoryId: string): Promise<FileTreeNode> {
  return apiFetch<FileTreeNode>(`/repositories/${repositoryId}/files/tree`);
}

export function getFileContent(repositoryId: string, path: string): Promise<FileContent> {
  return apiFetch<FileContent>(
    `/repositories/${repositoryId}/files/content?path=${encodeURIComponent(path)}`,
  );
}
