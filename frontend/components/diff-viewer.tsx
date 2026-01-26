import { cn } from "@/lib/utils";

/**
 * Renders a unified diff (as produced by backend/agents/code_generation_agent.py
 * via difflib) with per-line coloring. No parsing library needed — difflib's
 * output format is stable and simple enough to color line-by-line.
 */
export function DiffViewer({ diff }: { diff: string }) {
  const lines = diff.split("\n");

  return (
    <pre className="bg-muted/30 overflow-x-auto rounded-md border p-3 font-mono text-xs leading-5">
      {lines.map((line, index) => (
        <div key={index} className={cn("whitespace-pre", lineClassName(line))}>
          {line.length > 0 ? line : " "}
        </div>
      ))}
    </pre>
  );
}

function lineClassName(line: string): string {
  if (line.startsWith("+++") || line.startsWith("---")) {
    return "text-muted-foreground font-medium";
  }
  if (line.startsWith("@@")) {
    return "text-sky-600 dark:text-sky-400";
  }
  if (line.startsWith("+")) {
    return "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";
  }
  if (line.startsWith("-")) {
    return "bg-red-500/10 text-red-700 dark:text-red-400";
  }
  return "text-muted-foreground";
}
