"use client";

import { useQuery } from "@tanstack/react-query";
import * as filesService from "@/services/files";

export function useFileTree(repositoryId: string) {
  return useQuery({
    queryKey: ["repositories", repositoryId, "files", "tree"],
    queryFn: () => filesService.getFileTree(repositoryId),
  });
}

export function useFileContent(repositoryId: string, path: string | null) {
  return useQuery({
    queryKey: ["repositories", repositoryId, "files", "content", path],
    queryFn: () => filesService.getFileContent(repositoryId, path as string),
    enabled: Boolean(path),
  });
}
