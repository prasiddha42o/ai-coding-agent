"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import * as authService from "@/services/auth";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/token-storage";
import type { User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  /** True until the initial "am I already logged in?" check resolves. */
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string | null) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      if (!getAccessToken()) {
        setIsLoading(false);
        return;
      }
      try {
        const current = await authService.fetchCurrentUser();
        if (!cancelled) setUser(current);
      } catch {
        clearTokens();
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadUser();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authService.login(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    setUser(await authService.fetchCurrentUser());
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName: string | null) => {
      await authService.register(email, password, fullName);
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken();
    clearTokens();
    setUser(null);
    if (refreshToken) {
      // Best-effort: if the token's already expired/invalid server-side,
      // there's nothing left to revoke — the client-side clear is what matters.
      await authService.logout(refreshToken).catch(() => undefined);
    }
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
