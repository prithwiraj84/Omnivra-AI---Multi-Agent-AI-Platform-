# Omnivra AI Company OS — backend as a Hugging Face Docker Space (also runs on any Docker host).
# HF reads README.md frontmatter (sdk: docker, app_port: 7860). Set provider keys + the production
# vars in the Space's "Settings → Variables and secrets" (NEVER bake .env into the image).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ffmpeg: only needed for REAL reel rendering (optional); curl: lightweight liveness checks.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl \
 && rm -rf /var/lib/apt/lists/*

# HF Spaces run the container as a non-root user (uid 1000). Create it + own the app dir.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app

# Deps first for layer caching. requirements-docs.txt enables Document Studio (PPTX/DOCX/PDF).
# requirements-render.txt (moviepy/ffmpeg) is heavy + optional -> omitted so the image stays lean
# (reels run in stub mode). To enable real .mp4 reels, add it to the pip line below.
COPY --chown=user:user requirements.txt requirements-docs.txt ./
RUN pip install --user -r requirements.txt -r requirements-docs.txt

COPY --chown=user:user . .

# Production defaults — OVERRIDE the keys + any of these via Space variables/secrets.
ENV APP_ENV=production \
    DEBUG=false \
    LOG_JSON=true \
    WORKSPACE_ROOT=/home/user/app/workspace \
    APP_RUNNER_ENABLED=false \
    SECURITY_HEADERS_ENABLED=true \
    RATE_LIMIT_ENABLED=true \
    PORT=7860

EXPOSE 7860

# ONE worker on purpose: the in-memory stores (usage counters, realtime hub, app-runner registry)
# must not be duplicated across workers. --proxy-headers / --forwarded-allow-ips so the client scheme
# and IP are correct behind the HF (and Vercel) proxy.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1 --proxy-headers --forwarded-allow-ips='*' --no-server-header"]
