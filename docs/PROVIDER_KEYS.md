# In-app LLM / media provider keys

Omnivra can run entirely on **your** provider keys. You can supply them two ways, and you don't
have to restart the backend to change them:

1. **Environment** — set them in `backend/.env` (e.g. `OPENROUTER_API_KEY=...`). Best for
   servers / CI.
2. **In the website** — open **Integrations** and paste a key into a provider card. The key is
   saved on the server and used on the very next call.

## Precedence

For each provider the backend resolves the active key as:

```
stored (saved in the app)  →  env (backend/.env)  →  not configured (offline stub)
```

A key you **save in the app overrides** the env one; **remove** it to fall back to env. If you
never save a key in the app, behavior is exactly as before (env is used verbatim).

## Where keys are stored

In-app keys live in `workspace/.state/provider_keys.json` on the server. That file is
**gitignored** and never leaves the machine. Plaintext-at-rest is acceptable for this
single-admin, offline-first, localhost product — it's the same trust level as `backend/.env`.
The API never returns a raw key: a card only ever shows a **masked hint** (e.g. `sk-o…wxyz`) of a
key you saved, and env keys are never echoed back at all.

## Providers & where to get a key

| Provider | Env var | Get a key |
|----------|---------|-----------|
| Google AI Studio (Gemini) | `GOOGLE_AI_STUDIO_API_KEY` | https://aistudio.google.com/app/apikey |
| OpenRouter | `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| Groq (inference + TTS) | `GROQ_API_KEY` | https://console.groq.com/keys |
| Hugging Face (FLUX images + STT) | `HUGGINGFACE_API_KEY` | https://huggingface.co/settings/tokens |
| Pexels (reel b-roll, optional) | `PEXELS_API_KEY` | https://www.pexels.com/api/new/ |

Each Integrations card has a **How to get a key** guide with the same steps + a direct link.

> **Key pools (env only):** a `.env` var may hold several comma/space-separated keys and the
> provider rotates across them on rate limits. The in-app form intentionally takes a **single**
> clean key (a stray comma/space would split it into a bogus pool), so it rejects those.

## API (behind the app's auth gate)

- `GET /api/system/provider-keys` — per-provider status (`source`, `configured`, masked hint).
- `PUT /api/system/provider-keys/{id}` `{ "value": "<key>" }` — save/replace (422 on invalid).
- `DELETE /api/system/provider-keys/{id}` — remove the stored key (falls back to env).

All three require auth when `AUTH_ENABLED=true` (open in dev). Responses are always masked.
