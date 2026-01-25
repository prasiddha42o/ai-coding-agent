"use client";

import Link from "next/link";
import { RefreshCw, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Repository, RepositoryStatus } from "@/types/api";

const STATUS_VARIANT: Record<RepositoryStatus, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "outline",
  cloning: "secondary",
  indexing: "secondary",
  ready: "default",
  error: "destructive",
};

const STATUS_LABEL: Record<RepositoryStatus, string> = {
  pending: "Pending",
  cloning: "Cloning…",
  indexing: "Indexing…",
  ready: "Ready",
  error: "Error",
};

interface RepositoryCardProps {
  repository: Repository;
  onRefresh: () => void;
  onDelete: () => void;
  isRefreshing: boolean;
  isDeleting: boolean;
}

export function RepositoryCard({
  repository,
  onRefresh,
  onDelete,
  isRefreshing,
  isDeleting,
}: RepositoryCardProps) {
  const metadata = repository.metadata_json;
  const isSettling = repository.status === "pending" || repository.status === "cloning" || repository.status === "indexing";

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
        <div className="min-w-0">
          <CardTitle className="truncate text-base">
            <Link href={`/repositories/${repository.id}`} className="hover:underline">
              {repository.name}
            </Link>
          </CardTitle>
          <p className="text-muted-foreground mt-1 truncate text-xs">
            {repository.source_type === "github" ? repository.source_url : "Uploaded ZIP archive"}
          </p>
        </div>
        <Badge variant={STATUS_VARIANT[repository.status]} className="shrink-0">
          {STATUS_LABEL[repository.status]}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="flex min-h-6 flex-wrap gap-1.5">
          {metadata.language && <Badge variant="outline">{metadata.language}</Badge>}
          {metadata.framework && <Badge variant="outline">{metadata.framework}</Badge>}
          {metadata.package_manager && <Badge variant="outline">{metadata.package_manager}</Badge>}
        </div>

        {repository.status === "error" && repository.error_message && (
          <p className="text-destructive mt-3 line-clamp-2 text-xs">{repository.error_message}</p>
        )}

        <div className="mt-4 flex justify-end gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={onRefresh}
            disabled={isRefreshing || isSettling || repository.source_type !== "github"}
            title={
              repository.source_type !== "github"
                ? "Only GitHub-sourced repositories can be refreshed"
                : undefined
            }
          >
            <RefreshCw className={isRefreshing ? "size-3.5 animate-spin" : "size-3.5"} />
            Refresh
          </Button>
          <Button size="sm" variant="outline" onClick={onDelete} disabled={isDeleting}>
            <Trash2 className="size-3.5" />
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
