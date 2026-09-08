# DataPilot AI Frontend

## Prerequisites

- Node.js 20 or newer
- npm
- The DataPilot-AI FastAPI backend running at `http://127.0.0.1:8000`

## Installation

From this directory:

```bash
npm install
```

Copy `.env.example` to `.env` if you need to change the API base URL. The default `/api` value works with the Vite development proxy.

## Development

```bash
npm run dev
```

Open the URL printed by Vite. Requests made to `/api` are proxied to `http://127.0.0.1:8000` and the `/api` prefix is removed before forwarding, so the browser does not require backend CORS changes.

## Production Docker

From the repository root:

```bash
docker compose up -d --build
```

The production frontend is available at `http://127.0.0.1:3000`. Nginx serves the Vite build and proxies same-origin `/api/*` requests to the internal FastAPI `api:8000` service, stripping the `/api` prefix. The browser does not receive or use the Docker service hostname.

## Production build

```bash
npm run build
```

## Tests and lint

```bash
npm test -- --run
npm run lint
```

## Environment

`VITE_API_BASE_URL` controls the API prefix. It defaults to `/api`; local Vite development uses the configured Vite proxy, while the production Docker build fixes it to `/api` for the Nginx proxy. No API keys or backend secrets are included in the frontend bundle.

## Screens

The MVP includes CSV upload and persisted dataset selection, profile and quality overview, asynchronous analysis-job monitoring, validated cleaning workflows with download history, and persisted rules/OpenAI insight reports. All displayed dataset content comes from the backend API.
