import { API_BASE_URL } from "@/lib/config";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

let accessTokenGetter: () => string | null = () => null;

/**
 * Wired up by the auth context once it exists (see app/providers.tsx / the
 * auth provider added alongside the login flow) — kept as an injectable
 * getter rather than importing the auth context here, so this module has
 * no dependency on React and can be used from plain functions too.
 */
export function setAccessTokenGetter(getter: () => string | null): void {
  accessTokenGetter = getter;
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean;
}

function buildHeaders(auth: boolean, provided?: HeadersInit): Headers {
  const headers = new Headers(provided);
  if (auth) {
    const token = accessTokenGetter();
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

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, auth = true, headers, ...rest } = options;
  const requestHeaders = buildHeaders(auth, headers);

  let requestBody: BodyInit | undefined;
  if (body instanceof FormData) {
    requestBody = body;
  } else if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
    requestBody = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    body: requestBody,
  });

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
  const { body, auth = true, headers, ...rest } = options;
  const requestHeaders = buildHeaders(auth, headers);
  if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    method: rest.method ?? "POST",
    headers: requestHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

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
