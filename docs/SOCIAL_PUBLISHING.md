# Social Publishing Setup

The Social Studio (`/social`) drafts reels + posts, renders them, and — after **human
approval** — publishes to the target platforms. Publishing is **stub-safe**: with no
credentials it records a stub result, so the whole draft → render → approve flow works
offline. Wire a platform's credentials to publish for real.

| Platform | Kind | Status | Credential(s) |
|---|---|---|---|
| **YouTube** | reels | ✅ real upload (cp-0020) | `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` |
| Instagram | reels | stub | `INSTAGRAM_ACCESS_TOKEN` |
| Facebook | posts | stub | `FACEBOOK_PAGE_TOKEN` |
| LinkedIn | posts | stub | `LINKEDIN_ACCESS_TOKEN` |
| Twitter / X | posts | stub | `TWITTER_BEARER_TOKEN` |

> Rendering a real `.mp4` (for YouTube) requires the optional engine:
> `pip install -r backend/requirements-render.txt` (see [the render note](../backend/requirements-render.txt)).
> Without it the reel stays a storyboard and YouTube publish reports "render first".

## YouTube (real upload)

Uploads the rendered reel `.mp4` via the YouTube Data API v3 (resumable upload),
authenticated with an OAuth2 **refresh token** (no interactive flow at runtime).
**Videos upload as `private`** — review on YouTube, then set to Public yourself.

### One-time setup
1. **Google Cloud project** → enable the **YouTube Data API v3**.
2. **OAuth consent screen**: External; add your Google account as a Test user.
3. **Credentials → OAuth client ID → Desktop app**. Note the **Client ID** + **Client secret**.
4. **Get a refresh token** for the `https://www.googleapis.com/auth/youtube.upload` scope
   (the [OAuth 2.0 Playground](https://developers.google.com/oauthplayground) is easiest:
   gear icon → "Use your own OAuth credentials" → enter the client id/secret → authorize
   the `youtube.upload` scope → exchange for tokens → copy the **refresh token**).
5. Put them in `backend/.env`:
   ```
   YOUTUBE_CLIENT_ID=...apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=...
   YOUTUBE_REFRESH_TOKEN=1//0...
   ```
6. Restart the backend. Draft a reel → **Render video** → **Approve & publish** → the
   publish result links to the (private) YouTube video.

### Quotas / notes
- An upload costs ~**1600** quota units; the default daily quota (10,000) allows ~6/day.
- The refresh token is long-lived; the app exchanges it for short-lived access tokens
  per upload (retried with backoff on 429/5xx). Failures never crash a run — the publish
  result shows `ok=false` + a note, and you can retry just that platform.

## Configure credentials in the app (cp-0063)

You no longer have to edit `backend/.env` — open **Integrations → Publishing & Social** and
paste each platform's credentials into its card. Tokens are stored on the server
(`workspace/.state/provider_keys.json`, gitignored), masked in the UI, and used on the next
publish. A credential saved in-app **overrides** the matching `.env` value; clear it to fall back.

API (behind the app's auth gate; responses are always masked):
- `GET /api/system/social-connectors` — per-platform status + required fields.
- `PUT /api/system/social-connectors/{id}` `{ "values": { "<field>": "<value>" } }` — save/replace
  (a field set to `""` is cleared). Only fields belonging to that connector are accepted.
- `DELETE /api/system/social-connectors/{id}` — disconnect (clear all its fields).

### Credential fields per platform
| Platform | Fields | Where to get them |
|----------|--------|-------------------|
| **YouTube** *(publishes now)* | Client ID, Client secret, Refresh token | Google Cloud Console → OAuth client → a refresh token with the `youtube.upload` scope |
| **LinkedIn** | Access token | linkedin.com/developers → app with `w_member_social` → OAuth2 access token |
| **Facebook Page** | Page ID, Page access token | developers.facebook.com → app + Page → Graph API Explorer → Page access token |
| **Instagram** | IG Business account ID, Access token | Requires an IG **Business/Creator** account linked to a FB Page; long-lived Graph token |
| **X (Twitter)** | API key, API secret, Access token, Access token secret | developer.twitter.com → app → **OAuth 1.0a** user keys (the read-only bearer token can't post) |

## Real publishing status
- **YouTube** *(reel)* — real resumable upload as PRIVATE; honors in-app tokens.
- **LinkedIn** *(post)* — real UGC text share to your feed (PUBLIC). Resolves your author URN
  from the token (needs the `openid` + `profile` scopes) then posts the caption/brief + hashtags.
- **Facebook Page** *(post)* — real text post to the Page feed via the Graph API.
- **X / Twitter** *(post)* — real tweet via API v2 with **OAuth 1.0a** signing (stdlib HMAC-SHA1;
  the read-only bearer token can't post).
- **Instagram** *(reel)* — real publish via the Graph API container flow: the rendered `.mp4` is
  uploaded to **Supabase Storage** (a temporary signed URL), then `media` (REELS) → poll
  `status_code` until FINISHED → `media_publish` → permalink. Requires an IG **Business/Creator**
  account **and** Supabase Storage configured; with creds but no Storage it returns a clear note
  (no network). Publishing waits up to ~60s for Instagram to transcode — if it's still processing,
  approve → publish again to finish.

Every real publisher is **guarded + stub-safe**: with no credentials it records a stub so the
approve → publish flow still completes offline, and it **never raises** — a failure returns
`ok=false` with a generic note (tokens are never echoed) and you can retry just that platform.
Posts currently publish **text** (caption/brief + hashtags); image/video attachment for the
post platforms is a follow-up.

### Supabase Storage (needed for Instagram)
Instagram fetches the reel from a URL, so set Storage up:
1. Create a bucket (default name `omnivra-artifacts`, or set `SUPABASE_STORAGE_BUCKET`).
2. Set `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (backend only). The reel is uploaded and
   handed to Instagram as a **short-lived signed URL** — the bucket does **not** need to be public.
