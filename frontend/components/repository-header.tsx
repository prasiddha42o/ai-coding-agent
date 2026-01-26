"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { RepositoryNav } from "@/components/repository-nav";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useRepository } from "@/hooks/use-repositories";
import type { RepositoryStatus } from "@/types/api";

const STATUS_VARIANT: Record<RepositoryStatus, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "outline",
  cloning: "secondary",
  indexing: "secondary",
  ready: "default",
  error: "destructive",
};

export function RepositoryHeader({ repositoryId }: { repositoryId: string }) {
  const { data: repository, isLoading } = useRepository(repositoryId);

  return (
    <header className="border-border/60 flex items-center gap-3 border-b px-4 py-2.5">
      <Link href="/dashboard" className="text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" />
      </Link>
      {isLoading || !repository ? (
        <Skeleton className="h-5 w-40" />
      ) : (
        <>
          <span className="text-sm font-medium">{repository.name}</span>
          <Badge variant={STATUS_VARIANT[repository.status]} className="text-xs">
            {repository.status}
          </Badge>
        </>
      )}
      <div className="ml-4">
        <RepositoryNav repositoryId={repositoryId} />
      </div>
    </header>
  );
}
