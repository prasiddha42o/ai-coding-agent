import { apiFetch } from "@/services/api-client";
import type { Token, User } from "@/types/api";

export function register(email: string, password: string, fullName: string | null): Promise<User> {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    auth: false,
    body: { email, password, full_name: fullName },
  });
}

export function login(email: string, password: string): Promise<Token> {
  return apiFetch<Token>("/auth/login", {
    method: "POST",
    auth: false,
    body: { email, password },
  });
}

export function fetchCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function logout(refreshToken: string): Promise<void> {
  return apiFetch<void>("/auth/logout", {
    method: "POST",
    body: { refresh_token: refreshToken },
  });
}
