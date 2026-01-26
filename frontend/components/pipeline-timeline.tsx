import { CheckCircle2, CircleAlert, Loader2 } from "lucide-react";
import type { PipelineEvent } from "@/types/api";

const STAGE_LABEL: Record<PipelineEvent["stage"], string> = {
  code_generation: "Generating code",
  review: "Reviewing changes",
  apply: "Applying changes",
  testing: "Running tests",
  commit: "Committing",
  pipeline: "Pipeline",
};

export function PipelineTimeline({ events }: { events: PipelineEvent[] }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border p-3">
      <span className="text-muted-foreground text-xs font-medium tracking-wide uppercase">Run</span>
      <ol className="flex flex-col gap-2.5">
        {events.map((event, index) => (
          <li key={index} className="flex items-start gap-2 text-xs">
            <StatusIcon status={event.status} />
            <div className="min-w-0 flex-1">
              <p className="font-medium">
                {STAGE_LABEL[event.stage]} — {event.status.replace(/_/g, " ")}
              </p>
              {event.message && <p className="text-muted-foreground mt-0.5">{event.message}</p>}
              {event.summary && <p className="text-muted-foreground mt-0.5">{event.summary}</p>}
              {event.test_run && (
                <p className="text-muted-foreground mt-0.5">
                  {event.test_run.passed_count} passed, {event.test_run.failed_count} failed,{" "}
                  {event.test_run.skipped_count} skipped ({event.test_run.runner})
                </p>
              )}
              {event.commit && (
                <p className="text-muted-foreground mt-0.5 truncate font-mono">
                  {event.commit.sha?.slice(0, 7)} {event.commit.message}
                </p>
              )}
              {event.changes && (
                <p className="text-muted-foreground mt-0.5">{event.changes.length} file(s) changed</p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function StatusIcon({ status }: { status: PipelineEvent["status"] }) {
  if (status === "started") {
    return <Loader2 className="text-muted-foreground mt-0.5 size-3.5 shrink-0 animate-spin" />;
  }
  if (status === "error") {
    return <CircleAlert className="text-destructive mt-0.5 size-3.5 shrink-0" />;
  }
  if (status === "awaiting_decision") {
    return <CircleAlert className="mt-0.5 size-3.5 shrink-0 text-amber-500" />;
  }
  return <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-emerald-500" />;
}
