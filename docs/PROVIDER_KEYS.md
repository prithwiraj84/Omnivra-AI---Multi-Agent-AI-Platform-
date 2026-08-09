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

## Keys are PER USER

In per-user mode (`PER_USER_WORKSPACES=true`) every signed-in user configures **their own**
providers — you never see anyone else's keys, and agent runs use **the key of whoever owns the
project**. In single-admin/open mode there's one owner (the admin), exactly as before.

## Where keys are stored

| Backend | When | Durable? |
|---|---|---|
| **Supabase** (`provider_keys` table) | `SUPABASE_URL` + service-role key are set | ✅ yes |
| `workspace/.state/provider_keys.json` | otherwise (local dev) | only as long as the disk lives |

> ⚠️ **Hosted deployments must use Supabase.** Container filesystems on Hugging Face Spaces,
> Render and Fly are **ephemeral** — anything written to disk is wiped on the next restart, so
> file-stored keys silently revert to *"Not configured."* Run **`supabase/provider_keys.sql`**
> once in the Supabase SQL Editor to create the table.

The table is locked down with RLS and no permissive policy, so only the backend (service-role,
which bypasses RLS) can read or write it — the browser never can. The API never returns a raw
key either: a card only ever shows a **masked hint** (e.g. `sk-o…wxyz`) of a key you saved, and
env keys are never echoed back at all.

## Providers & where to get a key

| Provider | Env var | Get a key |
|----------|---------|-----------|
| Google AI Studio (Gemini) | `GOOGLE_AI_STUDIO_API_KEY` | https://aistudio.google.com/app/apikey |
| OpenRouter | `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| Groq (inference + TTS) | `GROQ_API_KEY` | https://console.groq.com/keys |
| Hugging Face (stable-diffusion images) | `HUGGINGFACE_API_KEY` | https://huggingface.co/settings/tokens |
| Pexels (reel b-roll + stock photo fallback) | `PEXELS_API_KEY` | https://www.pexels.com/api/new/ |
| ElevenLabs (natural reel narration, optional) | `ELEVENLABS_API_KEY` | https://elevenlabs.io/app/settings/api-keys |

Each Integrations card has a **How to get a key** guide with the same steps + a direct link.

> **Key pools (env only):** a `.env` var may hold several comma/space-separated keys and the
> provider rotates across them on rate limits. The in-app form intentionally takes a **single**
> clean key (a stray comma/space would split it into a bogus pool), so it rejects those.

## API (behind the app's auth gate)

- `GET /api/system/provider-keys` — per-provider status (`source`, `configured`, masked hint).
- `PUT /api/system/provider-keys/{id}` `{ "value": "<key>" }` — save/replace (422 on invalid).
- `DELETE /api/system/provider-keys/{id}` — remove the stored key (falls back to env).

All three require auth when `AUTH_ENABLED=true` (open in dev). Responses are always masked.

## Voice quality for reels

Reel narration walks a chain of speech engines and takes the first that produces audio:

1. **ElevenLabs** — `ELEVENLABS_API_KEY`. Closest to a real person; optional and metered.
2. **Google Gemini TTS** — no extra key, it reuses `GOOGLE_AI_STUDIO_API_KEY`. Free, natural,
   and **multilingual** — this is what makes Hindi work at all.
3. **Groq** — `playai-tts` / Orpheus. Free and fast, more synthetic, **English only**.

Each step falls through on failure rather than rendering silent. `ELEVENLABS_VOICE_ID` is optional — leave it blank and the first
voice on your account is used; set it to pin a specific one. `ELEVENLABS_MODEL` defaults to
`eleven_multilingual_v2`.

### Hindi

Social Studio lets you pick **English or हिन्दी** per reel/post; the choice drives the written
script *and* the voice. The engine chain differs because **Groq's voices are English-only
models** — they don't reject Devanagari, they "read" it as mangled phonetics, so Hindi never
routes there:

| Language | Engine order |
|---|---|
| English | ElevenLabs → Gemini → Groq |
| हिन्दी | ElevenLabs → Gemini |

So a Hindi reel works out of the box on the **Google AI key you already have** for the agents —
no paid account needed. With no Google or ElevenLabs key the reel still drafts and renders,
silently, and the render note names the key that would fix it.

> **Hugging Face is not in the chain.** Its serverless tier no longer hosts *any* text-to-speech
> model — `facebook/mms-tts-hin` and every other TTS model now return
> `Model not supported by provider hf-inference`. The HF key remains image-generation only.

**Free-plan ElevenLabs gotcha:** voices added from the Voice Library are rejected with
`402 paid_plan_required` ("Free users cannot use library voices"). Omnivra now walks the
account's *premade* voices and the global defaults until one works, so this recovers by itself —
but if you pinned `ELEVENLABS_VOICE_ID` to a library voice, clear it. Set
`ELEVENLABS_VOICE_ID_HI` / `GOOGLE_TTS_VOICE_HI` to give Hindi its own narrator.

## Image generation

hf-inference retires models without warning (FLUX.1-schnell now answers `410 deprecated`), so
image generation walks a chain: the configured `HUGGINGFACE_IMAGE_MODEL` (default
`stabilityai/stable-diffusion-3-medium-diffusers`, verified working on the free tier) → known
fallbacks → **Gemini image** on your Google AI key → a **licensed Pexels stock photo** → a stub
with the reasons. A retired model rolls on to the next instead of degrading every post to a
placeholder.

The stock-photo step is what keeps a post publishable when every generator is down. The prompt
is distilled to a 2–4 word search (a full styled prompt matches nothing), broadened if it's too
specific, and the result is labelled **"Stock photo via Pexels — <photographer>"** in the note,
because a photograph is not generated art and you should never have to guess which you got.

> **Why not scrape Google Images?** Those results are third-party copyrighted works, and this
> pipeline publishes to Instagram/LinkedIn/YouTube — the rights exposure is real, not
> theoretical. Pexels' license explicitly permits commercial use, it needs no browser engine
> (so it works on a shared host), and it doesn't break when a search page changes its markup.
