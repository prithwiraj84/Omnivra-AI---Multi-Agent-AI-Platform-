"""In-browser SPA preview — runs a generated Vite/React SOURCE app with no server build.

The static preview (cp-0070) covers plain html, but most CEO-generated frontends are Vite/React
SOURCE — an index.html referencing /src/main.jsx that only a dev server or a build resolves. On
a shared host neither is possible: launching processes is disabled and the container has no
Node. What IS possible: the visitor's own browser. This module serves a harness page that

  1. fetches the app's source files through the existing (path-jailed, cookie-authed) preview
     file route — the harness lives INSIDE the app dir, so relative fetches just work;
  2. transpiles JSX/TSX with Babel standalone (CDN) in the browser;
  3. resolves the app's RELATIVE imports recursively into ES-module blob URLs, injects CSS
     imports as <style>, and maps BARE imports (react, axios, …) to esm.sh with React pinned
     so every package shares one React instance (mixed copies break hooks);
  4. imports the entry — the generated app renders in the tab, executed entirely CLIENT-side.

Nothing generated ever runs on the server: the backend only serves files. Apps that need more
than this (custom bundler plugins, Node APIs, a real backend) get a readable overlay pointing
at Download-as-ZIP instead of a blank page.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.workspace_fs.paths import project_root, safe_project_id

# The reserved harness filename: requesting {app_dir}/__app__.html serves the harness when the
# dir has a runnable SPA shape (the file never exists on disk).
HARNESS_NAME = "__app__.html"

# Entry files a generated Vite/CRA app plausibly uses, most conventional first.
_ENTRY_CANDIDATES = (
    "src/main.tsx", "src/main.jsx", "src/main.ts", "src/main.js",
    "src/index.tsx", "src/index.jsx", "src/index.ts", "src/index.js",
    "main.jsx", "main.tsx", "index.jsx", "index.tsx",
)
_MODULE_SCRIPT_RE = re.compile(r"<script[^>]*type=[\"']module[\"'][^>]*src=[\"']([^\"']+)[\"']", re.IGNORECASE)


def spa_entry(app_dir: Path) -> tuple[Path, str] | None:
    """The (spa_root, entry_rel) of a runnable SPA source app under ``app_dir``, or None.

    A dir qualifies when it holds a package.json AND an entry file that actually EXISTS —
    an index.html pointing at a src/main.tsx that was never generated has nothing to run,
    and detecting it would promise a preview that renders an error.
    """
    roots = [app_dir] + sorted(d for d in app_dir.iterdir() if d.is_dir() and not d.name.startswith("."))
    for root in roots:
        if not (root / "package.json").is_file():
            continue
        # 1) the entry its own index.html names (the authoritative one when present)
        index = root / "index.html"
        if index.is_file():
            try:
                m = _MODULE_SCRIPT_RE.search(index.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                m = None
            if m:
                rel = m.group(1).lstrip("/").lstrip("./")
                if (root / rel).is_file():
                    return root, rel
        # 2) conventional entry locations
        for rel in _ENTRY_CANDIDATES:
            if (root / rel).is_file():
                return root, rel
    return None


def harness_rel(project_id: str | None, root_rel: str) -> str | None:
    """The workspace-relative harness path for ``root_rel``, or None if it has no SPA shape."""
    pid = safe_project_id(project_id)
    root = project_root(pid).resolve()
    try:
        app_dir = (root / root_rel).resolve()
        app_dir.relative_to(root)
    except (ValueError, OSError):
        return None
    if not app_dir.is_dir():
        return None
    found = spa_entry(app_dir)
    if found is None:
        return None
    spa_root, _entry = found
    return f"{spa_root.relative_to(root).as_posix()}/{HARNESS_NAME}"


def build_harness(project_id: str | None, dir_rel: str) -> str | None:
    """The harness html for ``dir_rel`` (the dir the __app__.html was requested in), or None."""
    pid = safe_project_id(project_id)
    root = project_root(pid).resolve()
    try:
        spa_root = (root / dir_rel).resolve()
        spa_root.relative_to(root)
    except (ValueError, OSError):
        return None
    if not spa_root.is_dir():
        return None
    found = spa_entry(spa_root)
    if found is None or found[0] != spa_root:
        return None
    _spa_root, entry = found
    return _HARNESS_TEMPLATE.replace("__ENTRY_JSON__", json.dumps("./" + entry)).replace(
        "__TITLE__", spa_root.name.replace("<", "").replace(">", "").replace("&", "")
    )


# ---------------------------------------------------------------------------- the harness
# Kept dependency-light on purpose: native import maps are NOT needed (every bare specifier is
# rewritten to esm.sh directly), so the only CDN loads are Babel standalone + the packages the
# app itself imports. React is pinned so react-dom and every ?deps= package share one instance.
_HARNESS_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__TITLE__ — preview</title>
<style>
 :root{color-scheme:dark}
 body{margin:0;background:#0b0b0e;color:#e4e4e7;font:400 14px/1.6 ui-sans-serif,system-ui,sans-serif}
 #__boot{position:fixed;inset:0;display:grid;place-items:center;background:#0b0b0e;transition:opacity .3s}
 #__boot .s{width:32px;height:32px;border-radius:50%;border:2px solid rgba(255,255,255,.12);
   border-top-color:#22d3ee;animation:r .8s linear infinite;margin:0 auto 1rem}
 @keyframes r{to{transform:rotate(360deg)}}
 #__err{display:none;position:fixed;inset:0;overflow:auto;background:#0b0b0e;padding:2rem;z-index:9999}
 #__err h1{font-size:1rem;color:#f87171;margin:0 0 .75rem}
 #__err pre{white-space:pre-wrap;word-break:break-word;font:11px/1.6 ui-monospace,monospace;color:#a1a1aa;
   background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:1rem}
 #__err p{color:#a1a1aa;font-size:12px}
</style>
</head>
<body>
<div id="__boot"><div style="text-align:center"><div class="s"></div><div>Building the app in your browser…</div></div></div>
<div id="__err"><h1>This app could not run in the browser preview</h1><pre id="__errmsg"></pre>
<p>The preview transpiles the generated source right here in your browser — no server build. Apps that
need Node APIs, bundler plugins, or a backend of their own can’t run this way: use <b>Download ZIP</b>
in Omnivra’s Workspace and run it locally instead.</p></div>
<div id="root"></div><div id="app"></div>
<script src="https://unpkg.com/@babel/standalone@7.26.4/babel.min.js"></script>
<script>
'use strict';
const ENTRY = __ENTRY_JSON__;
const REACT_PIN = '18.3.1';
const CDN = {
  'react': 'https://esm.sh/react@' + REACT_PIN,
  'react-dom': 'https://esm.sh/react-dom@' + REACT_PIN,
  'react-dom/client': 'https://esm.sh/react-dom@' + REACT_PIN + '/client',
  'react/jsx-runtime': 'https://esm.sh/react@' + REACT_PIN + '/jsx-runtime',
  'react/jsx-dev-runtime': 'https://esm.sh/react@' + REACT_PIN + '/jsx-dev-runtime',
};
// Every other package rides esm.sh with React pinned as a shared dep — two React copies is the
// classic silent "Invalid hook call" failure.
const bareUrl = (spec) => CDN[spec] || ('https://esm.sh/' + spec + '?deps=react@' + REACT_PIN);
const isBare = (spec) => !spec.startsWith('.') && !spec.startsWith('/') && !/^https?:/.test(spec);

window.process = window.process || { env: { NODE_ENV: 'production' } };

const EXTS = ['', '.tsx', '.ts', '.jsx', '.js', '.mjs', '.css', '.json',
              '/index.tsx', '/index.ts', '/index.jsx', '/index.js'];
const cache = new Map(); // absolute path -> Promise<moduleUrl>

function fail(err) {
  document.getElementById('__boot').style.display = 'none';
  document.getElementById('__err').style.display = 'block';
  document.getElementById('__errmsg').textContent = String(err && err.stack || err);
}
window.addEventListener('error', (e) => fail(e.error || e.message));
window.addEventListener('unhandledrejection', (e) => fail(e.reason));

async function fetchFirst(absPath) {
  for (const ext of EXTS) {
    const url = absPath + ext;
    const res = await fetch(url, { credentials: 'same-origin' });
    if (res.ok) return { url, text: await res.text() };
  }
  throw new Error('Preview could not load module: ' + absPath);
}

const resolveFrom = (fromAbs, spec) => new URL(spec, location.origin + fromAbs).pathname;

// Vite-isms the browser doesn't know. Coarse but effective for generated apps.
function shimViteGlobals(code) {
  return code
    .replace(/import\.meta\.env\.MODE/g, '"production"')
    .replace(/import\.meta\.env\.DEV/g, 'false')
    .replace(/import\.meta\.env\.PROD/g, 'true')
    .replace(/import\.meta\.env\.BASE_URL/g, '"./"')
    .replace(/import\.meta\.env/g, '({MODE:"production",DEV:false,PROD:true,BASE_URL:"./"})');
}

function collectImports(code, filename) {
  const specs = new Set();
  const collector = () => ({
    visitor: {
      ImportDeclaration: (p) => specs.add(p.node.source.value),
      ExportNamedDeclaration: (p) => { if (p.node.source) specs.add(p.node.source.value); },
      ExportAllDeclaration: (p) => specs.add(p.node.source.value),
      CallExpression: (p) => {
        if (p.node.callee.type === 'Import' && p.node.arguments[0] && p.node.arguments[0].type === 'StringLiteral')
          specs.add(p.node.arguments[0].value);
      },
    },
  });
  transpile(code, filename, [collector]); // discard output; we only want the specifiers
  return [...specs];
}

function rewriteImports(code, filename, map) {
  const rewriter = () => ({
    visitor: {
      ImportDeclaration: (p) => { const v = map[p.node.source.value]; if (v) p.node.source.value = v; },
      ExportNamedDeclaration: (p) => { if (p.node.source) { const v = map[p.node.source.value]; if (v) p.node.source.value = v; } },
      ExportAllDeclaration: (p) => { const v = map[p.node.source.value]; if (v) p.node.source.value = v; },
      CallExpression: (p) => {
        if (p.node.callee.type === 'Import' && p.node.arguments[0] && p.node.arguments[0].type === 'StringLiteral') {
          const v = map[p.node.arguments[0].value]; if (v) p.node.arguments[0].value = v;
        }
      },
    },
  });
  return transpile(code, filename, [rewriter]);
}

function transpile(code, filename, plugins) {
  return Babel.transform(code, {
    filename,
    presets: [
      [Babel.availablePresets.typescript, { isTSX: /\.[jt]sx$/.test(filename) || filename.endsWith('.js'), allExtensions: true }],
      [Babel.availablePresets.react, { runtime: 'automatic' }],
    ],
    plugins,
    sourceMaps: false,
  }).code;
}

const blobModule = (code, name) =>
  URL.createObjectURL(new Blob([code + '\n//# sourceURL=' + name], { type: 'text/javascript' }));

async function loadModule(absPath) {
  if (cache.has(absPath)) return cache.get(absPath);
  const p = (async () => {
    const { url, text } = await fetchFirst(absPath);
    if (url.endsWith('.css')) {
      const style = document.createElement('style');
      style.textContent = text;
      document.head.appendChild(style);
      return blobModule('export default undefined;', url);
    }
    if (url.endsWith('.json')) return blobModule('export default ' + text + ';', url);
    if (/\.(svg|png|jpe?g|gif|webp|ico)$/i.test(url)) {
      return blobModule('export default ' + JSON.stringify(url) + ';', url);
    }
    const code = shimViteGlobals(text);
    const specs = collectImports(code, url);
    const map = {};
    for (const spec of specs) {
      map[spec] = isBare(spec) ? bareUrl(spec) : await loadModule(resolveFrom(url, spec));
    }
    return blobModule(rewriteImports(code, url, map), url);
  })();
  cache.set(absPath, p);
  return p;
}

(async () => {
  try {
    const entryAbs = resolveFrom(location.pathname, ENTRY);
    const mod = await loadModule(entryAbs);
    await import(mod);
    document.getElementById('__boot').style.opacity = '0';
    setTimeout(() => document.getElementById('__boot').remove(), 350);
  } catch (err) {
    fail(err);
  }
})();
</script>
</body>
</html>
"""
