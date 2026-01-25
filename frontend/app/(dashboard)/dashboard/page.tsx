"use client";

import { toast } from "sonner";
import { ImportRepositoryDialog } from "@/components/import-repository-dialog";
import { RepositoryCard } from "@/components/repository-card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useDeleteRepository,
  useRefreshRepository,
  useRepositories,
} from "@/hooks/use-repositories";
import { ApiError } from "@/services/api-client";

export default function DashboardPage() {
  const { data: repositories, isLoading, isError } = useRepositories();
  const refreshRepository = useRefreshRepository();
  const deleteRepository = useDeleteRepository();

  async function handleRefresh(id: string) {
    try {
      await refreshRepository.mutateAsync(id);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Couldn't refresh that repository.");
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!window.confirm(`Delete "${name}"? This removes its workspace, sessions, and history.`)) {
      return;
    }
    try {
      await deleteRepository.mutateAsync(id);
      toast.success(`Deleted ${name}`);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Couldn't delete that repository.");
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Repositories</h1>
          <p className="text-muted-foreground text-sm">
            Import a repository to start a coding session against it.
          </p>
        </div>
        <ImportRepositoryDialog />
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-40 rounded-xl" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-destructive text-sm">
          Couldn&apos;t load your repositories. Try refreshing the page.
        </p>
      )}

      {!isLoading && !isError && repositories?.length === 0 && (
        <div className="border-border/60 flex flex-col items-center gap-2 rounded-xl border border-dashed px-6 py-16 text-center">
          <p className="text-sm font-medium">No repositories yet</p>
          <p className="text-muted-foreground max-w-sm text-sm">
            Import a public GitHub repository or upload a ZIP archive to build its knowledge graph
            and start your first coding session.
          </p>
        </div>
      )}

      {repositories && repositories.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {repositories.map((repository) => (
            <RepositoryCard
              key={repository.id}
              repository={repository}
              onRefresh={() => handleRefresh(repository.id)}
              onDelete={() => handleDelete(repository.id, repository.name)}
              isRefreshing={refreshRepository.isPending && refreshRepository.variables === repository.id}
              isDeleting={deleteRepository.isPending && deleteRepository.variables === repository.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
