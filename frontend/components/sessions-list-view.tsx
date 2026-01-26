"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useSessionsList } from "@/hooks/use-session-history";
import type { SessionStatus } from "@/types/api";

const STATUS_VARIANT: Record<SessionStatus, "default" | "secondary" | "destructive" | "outline"> = {
  active: "secondary",
  completed: "default",
  failed: "destructive",
};

export function SessionsListView({ repositoryId }: { repositoryId: string }) {
  const { data: sessions, isLoading, isError } = useSessionsList(repositoryId);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 overflow-y-auto px-6 py-8">
      <h1 className="text-lg font-semibold tracking-tight">Sessions</h1>

      {isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-20 rounded-lg" />
          ))}
        </div>
      )}

      {isError && <p className="text-destructive text-sm">Couldn&apos;t load sessions.</p>}

      {sessions?.length === 0 && (
        <p className="text-muted-foreground text-sm">
          No sessions yet — start one from the Workspace tab by describing a change to the Agent.
        </p>
      )}

      <div className="flex flex-col gap-2">
        {sessions?.map((session) => (
          <Link key={session.id} href={`/repositories/${repositoryId}/sessions/${session.id}`}>
            <Card className="hover:bg-muted/50 transition-colors">
              <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
                <CardTitle className="truncate text-sm font-medium">
                  {session.title ?? new Date(session.created_at).toLocaleString()}
                </CardTitle>
                <Badge variant={STATUS_VARIANT[session.status]} className="shrink-0">
                  {session.status}
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-xs">
                  Started {new Date(session.created_at).toLocaleString()}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
