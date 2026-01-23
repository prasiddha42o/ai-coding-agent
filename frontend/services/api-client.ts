import { API_BASE_URL } from "@/lib/config";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/token-storage";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Attach the stored access token. Default true — pass false for
   * register/login/refresh themselves. */
  auth?: boolean;
}

function buildHeaders(auth: boolean, provided?: HeadersInit): Headers {
  const headers = new Headers(provided);
  if (auth) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return data.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

let refreshPromise: Promise<boolean> | null = null;

/**
 * Rotates the refresh token exactly once even if several requests 401 at
 * the same moment — refresh tokens are single-use (see
 * backend/services/auth_service.py), so firing off a separate refresh call
 * per failed request would invalidate all but one of them.
 */
async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (response) => {
        if (!response.ok) return false;
        const data = await response.json();
        setTokens(data.access_token, data.refresh_token);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

function buildRequestInit(options: RequestOptions): RequestInit {
  const { body, auth = true, headers, ...rest } = options;
  const requestHeaders = buildHeaders(auth, headers);

  let requestBody: BodyInit | undefined;
  if (body instanceof FormData) {
    requestBody = body;
  } else if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
    requestBody = JSON.stringify(body);
  }

  return { ...rest, headers: requestHeaders, body: requestBody };
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const auth = options.auth ?? true;

  let response = await fetch(`${API_BASE_URL}${path}`, buildRequestInit(options));

  if (response.status === 401 && auth && !path.startsWith("/auth/")) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await fetch(`${API_BASE_URL}${path}`, buildRequestInit(options));
    } else {
      clearTokens();
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/**
 * Consumes a `data: {...}\n\n` event stream (see POST /plans/{id}/run) via
 * fetch + ReadableStream rather than EventSource — EventSource only
 * supports GET and can't set the Authorization header this API requires.
 */
export async function apiStream(
  path: string,
  onEvent: (event: Record<string, unknown>) => void,
  options: RequestOptions = {},
): Promise<void> {
  const requestInit = buildRequestInit({ method: "POST", ...options });
  let response = await fetch(`${API_BASE_URL}${path}`, requestInit);

  if (response.status === 401 && (options.auth ?? true)) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await fetch(`${API_BASE_URL}${path}`, buildRequestInit({ method: "POST", ...options }));
    }
  }

  if (!response.ok || !response.body) {
    throw new ApiError(response.status, await readErrorDetail(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      const dataLine = rawEvent.split("\n").find((line) => line.startsWith("data:"));
      if (dataLine) {
        const payload = dataLine.slice("data:".length).trim();
        if (payload) {
          try {
            onEvent(JSON.parse(payload));
          } catch {
            // malformed chunk — skip rather than abort the whole stream
          }
        }
      }
      boundary = buffer.indexOf("\n\n");
    }
  }
}
