# Omnivra Frontend - AI Company OS (V2.0)

Vite + React 18 + TypeScript + TailwindCSS + shadcn/ui + Framer Motion + React Flow + Recharts.

## Quickstart

    cd frontend
    npm install
    cp .env.example .env.local
    npm run dev

Dev server proxies /api and /ws to FastAPI on :8000. App runs at http://localhost:5173.

## Scripts
- npm run dev / build / preview
- npm run lint / typecheck / format

## Adding shadcn/ui components

    npx shadcn@latest add button card dialog

Components land in src/components/ui per components.json.

## Status
Phase 1 ships the runnable scaffold + design system. Layout shell, dashboard sections, pages, API client, stores and types are defined in the manifest and built in later phases.
