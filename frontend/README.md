# AI Coding Agent — Frontend

Next.js (App Router) + TypeScript + Tailwind + shadcn/ui frontend for the
[AI Coding Agent](../README.md) project: a dashboard for importing
repositories, a Monaco-based workspace, a chat-style agent panel with plan
approval, and a diff/session-history viewer.

```bash
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_BASE_URL
npm run dev
```

Requires the [backend](../backend) running (or a deployed instance) at the
URL configured in `.env.local`. See [`../docs/setup.md`](../docs/setup.md)
for full setup instructions, including running the whole stack via Docker
Compose.

## Notable choices

- **shadcn/ui on Base UI** (not Radix) — its `Button`/`Dialog` etc. use a
  `render` prop for polymorphic composition rather than `asChild`.
- **App Router route groups**: `(auth)` for the unauthenticated login/
  register pages, `(dashboard)` for everything behind the client-side auth
  guard in `app/(dashboard)/layout.tsx`.
- **Streaming**: `services/api-client.ts`'s `apiStream` consumes the
  backend's `POST /plans/{id}/run` event stream via `fetch` +
  `ReadableStream`, not `EventSource` — `EventSource` can only send GET
  requests and can't set the `Authorization` header this API requires.
