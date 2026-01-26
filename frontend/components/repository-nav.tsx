"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function RepositoryNav({ repositoryId }: { repositoryId: string }) {
  const pathname = usePathname();
  const workspaceHref = `/repositories/${repositoryId}`;
  const sessionsHref = `/repositories/${repositoryId}/sessions`;
  const isSessionsActive = pathname.startsWith(sessionsHref);

  return (
    <nav className="flex items-center gap-1 text-sm">
      <Link
        href={workspaceHref}
        className={cn(
          "rounded-md px-2.5 py-1",
          !isSessionsActive ? "bg-muted font-medium" : "text-muted-foreground hover:text-foreground",
        )}
      >
        Workspace
      </Link>
      <Link
        href={sessionsHref}
        className={cn(
          "rounded-md px-2.5 py-1",
          isSessionsActive ? "bg-muted font-medium" : "text-muted-foreground hover:text-foreground",
        )}
      >
        Sessions
      </Link>
    </nav>
  );
}
