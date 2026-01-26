"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { PipelineTimeline } from "@/components/pipeline-timeline";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { usePipelineRun } from "@/hooks/use-pipeline-run";
import {
  useApprovePlan,
  useCreatePlan,
  useCreateSession,
  useRejectPlan,
} from "@/hooks/use-sessions";
import { ApiError } from "@/services/api-client";
import type { CodingSession, ComplexityLevel, Plan } from "@/types/api";

const COMPLEXITY_VARIANT: Record<ComplexityLevel, "default" | "secondary" | "destructive" | "outline"> = {
  trivial: "outline",
  moderate: "secondary",
  complex: "destructive",
};

export function AgentPanel({ repositoryId }: { repositoryId: string }) {
  const [session, setSession] = useState<CodingSession | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [prompt, setPrompt] = useState("");

  const createSession = useCreateSession();
  const createPlan = useCreatePlan();
  const approvePlan = useApprovePlan();
  const rejectPlan = useRejectPlan();
  const pipeline = usePipelineRun();

  const isSubmittingPrompt = createSession.isPending || createPlan.isPending;
  const isPlanPending = plan?.status === "pending_approval";
  const inputDisabled = isSubmittingPrompt || isPlanPending || pipeline.isRunning;

  async function handleSubmitPrompt(event: FormEvent) {
    event.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) return;

    try {
      let activeSession = session;
      if (!activeSession) {
        activeSession = await createSession.mutateAsync(repositoryId);
        setSession(activeSession);
      }
      const newPlan = await createPlan.mutateAsync({ sessionId: activeSession.id, prompt: trimmed });
      setPlan(newPlan);
      setPrompt("");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Couldn't create a plan for that request.");
    }
  }

  async function handleApprove() {
    if (!plan) return;
    try {
      setPlan(await approvePlan.mutateAsync(plan.id));
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Couldn't approve the plan.");
    }
  }

  async function handleReject() {
    if (!plan) return;
    try {
      setPlan(await rejectPlan.mutateAsync(plan.id));
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Couldn't reject the plan.");
    }
  }

  function handleRun() {
    if (plan) pipeline.run(plan.id);
  }

  function handleStartOver() {
    setSession(null);
    setPlan(null);
    setPrompt("");
    pipeline.reset();
  }

  const canRun = plan?.status === "approved" && pipeline.events.length === 0 && !pipeline.isRunning;

  return (
    <aside className="border-border/60 flex w-96 shrink-0 flex-col border-l">
      <div className="border-border/60 flex items-center justify-between border-b px-4 py-2.5">
        <span className="text-sm font-medium">Agent</span>
        {(session || plan) && (
          <Button variant="ghost" size="sm" onClick={handleStartOver}>
            New session
          </Button>
        )}
      </div>

      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-4 p-4">
          {!plan && (
            <p className="text-muted-foreground text-sm">
              Describe a change below. The Planning Agent will read this repository&apos;s structure and
              propose concrete steps for you to review before anything happens.
            </p>
          )}

          {plan && (
            <div className="flex flex-col gap-3 rounded-lg border p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
                  Plan
                </span>
                <div className="flex items-center gap-1.5">
                  <Badge variant={COMPLEXITY_VARIANT[plan.complexity]}>{plan.complexity}</Badge>
                  <Badge variant="outline">{plan.status.replace(/_/g, " ")}</Badge>
                </div>
              </div>

              {plan.summary && <p className="text-sm">{plan.summary}</p>}

              <ol className="flex flex-col gap-2">
                {plan.steps.map((step, index) => (
                  <li key={index} className="bg-muted/50 rounded-md p-2 text-xs">
                    <p className="font-medium">
                      {index + 1}. {step.title}
                    </p>
                    <p className="text-muted-foreground mt-0.5">{step.description}</p>
                    {step.affected_files.length > 0 && (
                      <div className="mt-1.5 flex flex-wrap gap-1">
                        {step.affected_files.map((file) => (
                          <Badge key={file} variant="outline" className="font-mono text-[10px]">
                            {file}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
              </ol>

              {isPlanPending && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleApprove} disabled={approvePlan.isPending}>
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleReject}
                    disabled={rejectPlan.isPending}
                  >
                    Reject
                  </Button>
                </div>
              )}

              {plan.status === "rejected" && (
                <p className="text-muted-foreground text-xs">
                  Plan rejected. Describe what you&apos;d like instead below.
                </p>
              )}

              {canRun && (
                <Button size="sm" onClick={handleRun}>
                  Run pipeline
                </Button>
              )}
            </div>
          )}

          {pipeline.events.length > 0 && <PipelineTimeline events={pipeline.events} />}

          {pipeline.error && <p className="text-destructive text-xs">{pipeline.error}</p>}
        </div>
      </ScrollArea>

      <form onSubmit={handleSubmitPrompt} className="border-border/60 flex flex-col gap-2 border-t p-3">
        <Textarea
          placeholder={
            isPlanPending
              ? "Approve or reject the plan above first"
              : 'Describe a change, e.g. "add input validation to the login form"'
          }
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          disabled={inputDisabled}
          rows={3}
        />
        <Button type="submit" size="sm" disabled={inputDisabled || !prompt.trim()}>
          {isSubmittingPrompt ? "Thinking…" : "Send"}
        </Button>
      </form>
    </aside>
  );
}
