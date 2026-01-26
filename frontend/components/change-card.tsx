"use client";

import { useState } from "react";
import { ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { DiffViewer } from "@/components/diff-viewer";
import { cn } from "@/lib/utils";
import type { Change, ChangeType } from "@/types/api";

const CHANGE_TYPE_VARIANT: Record<ChangeType, "default" | "secondary" | "destructive" | "outline"> = {
  create: "default",
  modify: "secondary",
  delete: "destructive",
};

const SEVERITY_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  error: "destructive",
  warning: "secondary",
  info: "outline",
};

export function ChangeCard({ change }: { change: Change }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-lg border">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="hover:bg-muted/50 flex w-full items-center gap-2 p-3 text-left"
      >
        <ChevronRight className={cn("size-3.5 shrink-0 transition-transform", isOpen && "rotate-90")} />
        <Badge variant={CHANGE_TYPE_VARIANT[change.change_type]} className="shrink-0">
          {change.change_type}
        </Badge>
        <span className="truncate font-mono text-xs">{change.file_path}</span>
        {change.review_notes && change.review_notes.length > 0 && (
          <Badge variant="outline" className="ml-auto shrink-0 text-[10px]">
            {change.review_notes.length} note{change.review_notes.length === 1 ? "" : "s"}
          </Badge>
        )}
      </button>

      {isOpen && (
        <div className="flex flex-col gap-3 border-t p-3">
          {change.explanation && <p className="text-muted-foreground text-xs">{change.explanation}</p>}

          {change.review_notes && change.review_notes.length > 0 && (
            <ul className="flex flex-col gap-1.5">
              {change.review_notes.map((note, index) => (
                <li key={index} className="flex items-start gap-1.5 text-xs">
                  <Badge variant={SEVERITY_VARIANT[note.severity] ?? "outline"} className="shrink-0 text-[10px]">
                    {note.severity}
                  </Badge>
                  <span className="text-muted-foreground">
                    {note.message}
                    {note.line != null && ` (line ${note.line})`}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {change.diff && <DiffViewer diff={change.diff} />}
        </div>
      )}
    </div>
  );
}
