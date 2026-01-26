"use client";

import { PlanDetail } from "@/components/plan-detail";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useSession,
  useSessionCommits,
  useSessionPlans,
  useSessionTestRuns,
} from "@/hooks/use-session-history";

const TEST_STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  passed: "default",
  failed: "destructive",
  error: "destructive",
  skipped: "outline",
};

export function SessionDetailView({ sessionId }: { sessionId: string }) {
  const { data: session, isLoading: isSessionLoading } = useSession(sessionId);
  const { data: plans, isLoading: isPlansLoading } = useSessionPlans(sessionId);
  const { data: testRuns } = useSessionTestRuns(sessionId);
  const { data: commits } = useSessionCommits(sessionId);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 overflow-y-auto px-6 py-8">
      <div>
        <h1 className="text-lg font-semibold tracking-tight">
          {isSessionLoading || !session ? (
            <Skeleton className="h-6 w-48" />
          ) : (
            (session.title ?? "Session")
          )}
        </h1>
        {session && (
          <p className="text-muted-foreground mt-1 text-xs">
            Started {new Date(session.created_at).toLocaleString()} · {session.status}
          </p>
        )}
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">Plans</h2>
        {isPlansLoading && <Skeleton className="h-24 w-full rounded-lg" />}
        {plans?.length === 0 && (
          <p className="text-muted-foreground text-sm">No plans in this session yet.</p>
        )}
        {plans?.map((plan) => (
          <PlanDetail key={plan.id} plan={plan} />
        ))}
      </section>

      {testRuns && testRuns.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
            Test runs
          </h2>
          {testRuns.map((run) => (
            <div key={run.id} className="flex items-center justify-between rounded-lg border p-3 text-xs">
              <span>
                {run.runner} · {run.command}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">
                  {run.passed_count} passed, {run.failed_count} failed, {run.skipped_count} skipped
                </span>
                <Badge variant={TEST_STATUS_VARIANT[run.status] ?? "outline"}>{run.status}</Badge>
              </div>
            </div>
          ))}
        </section>
      )}

      {commits && commits.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">Commits</h2>
          {commits.map((commit) => (
            <div key={commit.id} className="rounded-lg border p-3 text-xs">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono">{commit.sha ? commit.sha.slice(0, 7) : "(uncommitted)"}</span>
                <Badge variant="outline">{commit.status}</Badge>
              </div>
              <p className="mt-1 font-medium">{commit.message}</p>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
