"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as repositoriesService from "@/services/repositories";
import type { Repository } from "@/types/api";

const REPOSITORIES_KEY = ["repositories"] as const;

const SETTLING_STATUSES: Repository["status"][] = ["pending", "cloning", "indexing"];

export function useRepositories() {
  return useQuery({
    queryKey: REPOSITORIES_KEY,
    queryFn: repositoriesService.listRepositories,
    // Repos pass through pending -> cloning -> indexing right after import;
    // poll gently while any are still settling so status updates without a
    // manual page refresh, and stop once everything's settled.
    refetchInterval: (query) => {
      const stillWorking = query.state.data?.some((repo) => SETTLING_STATUSES.includes(repo.status));
      return stillWorking ? 2000 : false;
    },
  });
}

export function useRepository(id: string | undefined) {
  return useQuery({
    queryKey: [...REPOSITORIES_KEY, id],
    queryFn: () => repositoriesService.getRepository(id as string),
    enabled: Boolean(id),
    refetchInterval: (query) => (query.state.data && SETTLING_STATUSES.includes(query.state.data.status) ? 2000 : false),
  });
}

export function useImportGithubRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { sourceUrl: string; name: string | null; branch: string | null }) =>
      repositoriesService.importFromGithub(input.sourceUrl, input.name, input.branch),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: REPOSITORIES_KEY }),
  });
}

export function useImportZipRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { file: File; name: string | null }) =>
      repositoriesService.importFromZip(input.file, input.name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: REPOSITORIES_KEY }),
  });
}

export function useRefreshRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => repositoriesService.refreshRepository(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: REPOSITORIES_KEY }),
  });
}

export function useDeleteRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => repositoriesService.deleteRepository(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: REPOSITORIES_KEY }),
  });
}
