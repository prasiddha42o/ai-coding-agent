"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/contexts/auth-context";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <header className="border-border/60 flex items-center justify-between border-b px-6 py-3">
        <Link href="/dashboard" className="text-sm font-semibold tracking-tight">
          AI Coding Agent
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground text-sm">{user.email}</span>
          <Button variant="ghost" size="sm" onClick={() => logout()}>
            Sign out
          </Button>
        </div>
      </header>
      <main className="flex flex-1 flex-col">{children}</main>
    </div>
  );
}
