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

## Other platforms (stubbed)
The Instagram / Facebook / LinkedIn / Twitter publishers are implemented as guarded
stubs today. Each needs its own OAuth app + app review; Instagram additionally requires
a Business/Creator account and a **publicly-hosted** video URL (it pulls the file rather
than accepting an upload), so the rendered `.mp4` must be exposed via Supabase Storage /
S3 first. These are wired one at a time in later phases, following the same real +
stub-safe pattern as YouTube.
