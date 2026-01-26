"use client";

import { ChangeCard } from "@/components/change-card";
import { Badge } from "@/components/ui/badge";
import { usePlanChanges } from "@/hooks/use-session-history";
import type { ComplexityLevel, Plan, PlanStatus } from "@/types/api";

const COMPLEXITY_VARIANT: Record<ComplexityLevel, "default" | "secondary" | "destructive" | "outline"> = {
  trivial: "outline",
  moderate: "secondary",
  complex: "destructive",
};

const STATUS_VARIANT: Record<PlanStatus, "default" | "secondary" | "destructive" | "outline"> = {
  pending_approval: "outline",
  approved: "secondary",
  rejected: "destructive",
  executing: "secondary",
  completed: "default",
  failed: "destructive",
};

export function PlanDetail({ plan }: { plan: Plan }) {
  const { data: changes, isLoading } = usePlanChanges(plan.id);

  return (
    <div className="flex flex-col gap-3 rounded-lg border p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium">{plan.user_prompt}</p>
          {plan.summary && <p className="text-muted-foreground mt-1 text-xs">{plan.summary}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <Badge variant={COMPLEXITY_VARIANT[plan.complexity]}>{plan.complexity}</Badge>
          <Badge variant={STATUS_VARIANT[plan.status]}>{plan.status.replace(/_/g, " ")}</Badge>
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground text-xs">Loading changes…</p>}
      {changes && changes.length > 0 && (
        <div className="flex flex-col gap-2">
          {changes.map((change) => (
            <ChangeCard key={change.id} change={change} />
          ))}
        </div>
      )}
    </div>
  );
}
