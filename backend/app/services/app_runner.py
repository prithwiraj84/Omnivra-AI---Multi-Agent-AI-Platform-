"""Universal app runner (cp-0054) — set up and run a WHOLE generated project (not just one file).

The single-file ``code_runner`` can't run a real app: it executes ``main.py`` with the server's own
interpreter, so a generated FastAPI app dies with ``ModuleNotFoundError: No module named 'sqlmodel'``
because nothing installs its dependencies. This module fixes that:

  * DISCOVERS the runnable targets inside a generated project dir (a Python backend with
    requirements.txt + an entry; a Node/Vite frontend with package.json).
  * SETS UP each target in ISOLATION (a per-app ``.venv`` + ``pip install -r requirements.txt`` for
    Python; ``npm install`` for Node) — NO Docker, venv only, all inside the workspace sandbox.
  * SELF-HEALS missing deps: installs any third-party import the requirements file forgot, and on a
    runtime ``ModuleNotFoundError`` pip-installs the missing package and relaunches once.
  * LAUNCHES the long-running server on a free 127.0.0.1 port (uvicorn / flask / django / npm dev),
    tracks it in a process registry, streams logs, health-checks the port, and exposes a real STOP
    (process-tree kill) + a kill-all on shutdown.

Hard constraints honored: path-jailed to workspace/projects/<id>/, bound to localhost, minimal env
(no app/provider secrets leak), single-admin/opt-in, NEVER raises out to the request.
"""
from __future__ import annotations

import io
import os
import re
import socket
import subprocess
import sys
import threading
import time
import zipfile
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging import logger
from app.services.code_runner import _kill_tree, _minimal_env, shutil_which
from app.workspace_fs.paths import project_root, safe_project_id

# ---------------------------------------------------------------------------- config
_LOG_CAP = 2000                  # lines kept per target (ring buffer)
_INSTALL_TIMEOUT = 600.0         # pip / npm install wall-clock cap
_HEALTH_TIMEOUT = 45.0           # seconds to wait for the server port to come up
_PY_ENTRIES = ("main.py", "app.py", "asgi.py", "wsgi.py", "manage.py", "server.py", "run.py", "__main__.py")
# import name -> PyPI package, where they differ (so self-heal installs the right thing).
_IMPORT_TO_PKG = {
    "cv2": "opencv-python", "PIL": "pillow", "sklearn": "scikit-learn", "yaml": "pyyaml",
    "dotenv": "python-dotenv", "jose": "python-jose", "bs4": "beautifulsoup4", "jwt": "pyjwt",
    "Crypto": "pycryptodome", "OpenSSL": "pyopenssl", "dateutil": "python-dateutil", "attr": "attrs",
    "psycopg2": "psycopg2-binary", "MySQLdb": "mysqlclient", "slugify": "python-slugify",
    "multipart": "python-multipart", "magic": "python-magic", "serial": "pyserial",
}
# dirs/files never included in the downloadable zip (build output, deps, caches, agent transcripts).
_ZIP_SKIP_DIRS = {".venv", "venv", "env", "node_modules", "__pycache__", ".git", "dist", "build",
                  ".run", ".pytest_cache", ".mypy_cache", ".next", ".turbo", ".cache", ".idea", ".vscode"}
_ZIP_SKIP_SUFFIX = (".pyc", ".pyo", ".log", ".sqlite3-journal")


# ---------------------------------------------------------------------------- registry
@dataclass
class AppProc:
    """One runnable target (a backend or a frontend) and its live process state."""
    key: str
    project_id: str
    rel: str                      # workspace-relative dir of THIS target
    kind: str                     # "python" | "node"
    name: str                     # display name (backend / frontend / dir name)
    framework: str = ""           # fastapi | flask | django | script | vite | node
    status: str = "idle"          # idle|installing|starting|running|exited|error|stopped
    port: int | None = None
    url: str | None = None
    note: str = ""
    exit_code: int | None = None
    started_at: float = 0.0
    proc: subprocess.Popen | None = None
    logs: deque[str] = field(default_factory=lambda: deque(maxlen=_LOG_CAP))
    thread: threading.Thread | None = None


_REG: dict[str, AppProc] = {}
_LOCK = threading.Lock()
_TERMINAL = {"idle", "exited", "error", "stopped"}


def _log(entry: AppProc, line: str) -> None:
    entry.logs.append(line.rstrip("\n"))


# ---------------------------------------------------------------------------- jail + helpers
def _jail_dir(project_id: str | None, rel_dir: str) -> Path:
    """Resolve a workspace-relative DIRECTORY, jailed to the project's sandbox. Raises on escape."""
    root = project_root(project_id)
    target = (root / Path(rel_dir or "")).resolve()
    if target != root and root.resolve() not in target.parents:
        raise ValueError(f"Path {rel_dir!r} escapes the workspace sandbox")
    if not target.is_dir():
        raise FileNotFoundError(rel_dir)
    return target


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        try:
            return s.connect_ex(("127.0.0.1", port)) == 0
        except OSError:
            return False


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _spawn_kwargs() -> dict:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _read_into(proc: subprocess.Popen, entry: AppProc) -> None:
    """Pump a process's merged stdout/stderr into the target's ring buffer until EOF."""
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            _log(entry, line)
    except Exception:  # noqa: BLE001 - reader must never crash the supervisor
        pass


def _run_step(cmd: list[str], cwd: Path, entry: AppProc, *, env: dict[str, str] | None = None,
              timeout: float = _INSTALL_TIMEOUT) -> int:
    """Run a blocking setup step (venv/pip/npm install), streaming output into the log. Returns exit code."""
    _log(entry, f"$ {' '.join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))}")
    try:
        proc = subprocess.Popen(  # noqa: S603 - argv list, no shell, jailed cwd, minimal env
            cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            env=env or _minimal_env(), bufsize=1, **_spawn_kwargs(),
        )
    except FileNotFoundError:
        _log(entry, f"! {Path(cmd[0]).name} not found on this machine")
        return 127
    reader = threading.Thread(target=_read_into, args=(proc, entry), daemon=True)
    reader.start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        _log(entry, f"! step timed out after {timeout:.0f}s")
        return 124
    reader.join(timeout=2)
    return proc.returncode if proc.returncode is not None else 1


# ---------------------------------------------------------------------------- discovery
def _stdlib() -> frozenset[str]:
    return getattr(sys, "stdlib_module_names", frozenset())


def _third_party_imports(app_dir: Path) -> set[str]:
    """Top-level third-party imports across the target's .py files (excludes stdlib + local modules)."""
    local = {p.stem for p in app_dir.rglob("*.py")} | {d.name for d in app_dir.iterdir() if d.is_dir()}
    pat = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z_][\w]*)", re.MULTILINE)
    found: set[str] = set()
    stdlib = _stdlib()
    for py in list(app_dir.rglob("*.py"))[:200]:
        try:
            text = py.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        for mod in pat.findall(text):
            if mod and mod not in stdlib and mod not in local and not mod.startswith("_"):
                found.add(mod)
    return found


def _detect_python(entry_file: Path) -> tuple[str, str]:
    """Return (framework, app_var) for a Python entry — drives the launch command."""
    try:
        text = entry_file.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        text = ""
    if entry_file.name == "manage.py" or "django" in text.lower():
        return "django", "app"
    m = re.search(r"(\w+)\s*=\s*FastAPI\s*\(", text)
    if m or "fastapi" in text.lower() or "starlette" in text.lower():
        return "fastapi", (m.group(1) if m else "app")
    m = re.search(r"(\w+)\s*=\s*Flask\s*\(", text)
    if m or "flask" in text.lower():
        return "flask", (m.group(1) if m else "app")
    return "script", "app"


def _detect_node(app_dir: Path) -> str:
    """Classify a Node project from its package.json: vite | next | cra | node (a plain server).

    This is what stops an Express backend from being run with Vite's --strictPort/--host flags (which
    it ignores, so it never binds the expected port and the runner hangs at 'starting')."""
    import json

    try:
        pkg = json.loads((app_dir / "package.json").read_text(encoding="utf-8", errors="replace"))
    except Exception:  # noqa: BLE001
        return "node"
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    scripts = pkg.get("scripts") or {}
    blob = " ".join(str(v) for v in scripts.values()).lower()
    if "next" in deps or "next " in blob:
        return "next"
    if "vite" in deps or "vite" in blob:
        return "vite"
    if "react-scripts" in deps:
        return "cra"
    return "node"  # express/koa/fastify/plain server -> run its start script / main entry, scan for its port


def discover_targets(project_id: str | None, root_rel: str) -> list[dict]:
    """Find runnable targets in ``root_rel`` and its immediate subdirs (a python backend / node front)."""
    pid = safe_project_id(project_id)
    abs_root = _jail_dir(pid, root_rel)
    root = project_root(pid).resolve()
    dirs = [abs_root] + [d for d in sorted(abs_root.iterdir()) if d.is_dir() and d.name not in _ZIP_SKIP_DIRS]
    targets: list[dict] = []
    seen: set[str] = set()
    for d in dirs:
        rel = d.resolve().relative_to(root).as_posix()
        if rel in seen:
            continue
        # Python target: a requirements/pyproject + a runnable entry file.
        if (d / "requirements.txt").exists() or (d / "pyproject.toml").exists():
            entry = next((e for e in _PY_ENTRIES if (d / e).exists()), None)
            if entry:
                fw, var = _detect_python(d / entry)
                targets.append({"kind": "python", "rel": rel, "name": d.name, "entry": entry,
                                "framework": fw, "app_var": var})
                seen.add(rel)
                continue
        # Node target: a package.json. Classify it so we launch it correctly (vite/next/cra/server).
        if (d / "package.json").exists():
            targets.append({"kind": "node", "rel": rel, "name": d.name, "entry": "package.json",
                            "framework": _detect_node(d)})
            seen.add(rel)
    return targets


# ---------------------------------------------------------------------------- python supervisor
def _ensure_venv(app_dir: Path, entry: AppProc) -> Path | None:
    venv_dir = app_dir / ".venv"
    py = _venv_python(venv_dir)
    if not py.exists():
        entry.status = "installing"
        _log(entry, "Creating virtual environment (.venv)…")
        if _run_step([sys.executable, "-m", "venv", str(venv_dir)], app_dir, entry) != 0 or not py.exists():
            entry.status = "error"
            entry.note = "Could not create the .venv"
            return None
    return py


def _pip_install_requirements(py: Path, app_dir: Path, entry: AppProc) -> None:
    pip_base = [str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-input"]
    if (app_dir / "requirements.txt").exists():
        _log(entry, "Installing requirements.txt…")
        _run_step([*pip_base, "-r", "requirements.txt"], app_dir, entry)
    # Self-heal: install any third-party import the requirements file missed.
    try:
        req_text = (app_dir / "requirements.txt").read_text(encoding="utf-8", errors="replace").lower() \
            if (app_dir / "requirements.txt").exists() else ""
        missing = []
        for mod in sorted(_third_party_imports(app_dir)):
            pkg = _IMPORT_TO_PKG.get(mod, mod)
            if pkg.lower() not in req_text and mod.lower() not in req_text:
                missing.append(pkg)
        if missing:
            _log(entry, f"Installing imports missing from requirements: {', '.join(missing)}")
            _run_step([*pip_base, *missing], app_dir, entry)
    except Exception as exc:  # noqa: BLE001 - self-heal is best-effort
        _log(entry, f"(dependency self-heal skipped: {type(exc).__name__})")


def _python_command(py: Path, target: dict, port: int) -> list[str]:
    module = Path(target["entry"]).stem
    fw, var = target["framework"], target.get("app_var", "app")
    if fw == "fastapi":
        return [str(py), "-m", "uvicorn", f"{module}:{var}", "--host", "127.0.0.1", "--port", str(port)]
    if fw == "flask":
        return [str(py), "-m", "flask", "--app", f"{module}:{var}", "run", "--host", "127.0.0.1", "--port", str(port)]
    if fw == "django":
        return [str(py), "manage.py", "runserver", f"127.0.0.1:{port}"]
    return [str(py), target["entry"]]  # plain script — controls its own port


def _supervise_python(entry: AppProc, app_dir: Path, target: dict) -> None:
    try:
        py = _ensure_venv(app_dir, entry)
        if py is None:
            return
        _pip_install_requirements(py, app_dir, entry)
        if target["framework"] == "fastapi":  # uvicorn must be present to serve an ASGI app
            _run_step([str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "uvicorn[standard]"],
                      app_dir, entry)
        _launch_python(entry, app_dir, target, py, heal=True)
    except Exception as exc:  # noqa: BLE001 - a supervisor crash must never escape the thread
        entry.status = "error"
        entry.note = f"{type(exc).__name__}: {str(exc)[:160]}"
        _log(entry, f"! supervisor error: {entry.note}")


def _launch_python(entry: AppProc, app_dir: Path, target: dict, py: Path, *, heal: bool) -> None:
    port = _free_port()
    entry.port, entry.status = port, "starting"
    entry.url = f"http://127.0.0.1:{port}"
    env = _minimal_env()
    env["PORT"] = str(port)
    env["PYTHONUNBUFFERED"] = "1"
    cmd = _python_command(py, target, port)
    _log(entry, f"Starting: {' '.join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))}")
    proc = subprocess.Popen(  # noqa: S603 - argv list, no shell, jailed cwd, minimal env
        cmd, cwd=str(app_dir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        env=env, bufsize=1, **_spawn_kwargs(),
    )
    entry.proc = proc
    threading.Thread(target=_read_into, args=(proc, entry), daemon=True).start()
    # Only the plain-script fallback picks its own port; framework apps bind the port we assigned,
    # so don't scan other ports (that could latch onto an unrelated process listening on 8000/8080).
    if _await_running(entry, proc, port, scan_others=target["framework"] == "script"):
        return
    # Did not come up. If it crashed on a missing module, heal once and relaunch.
    if heal and proc.poll() is not None:
        miss = _missing_module(entry)
        if miss:
            pkg = _IMPORT_TO_PKG.get(miss, miss)
            _log(entry, f"Detected ModuleNotFoundError -> installing {pkg} and retrying…")
            _run_step([str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", pkg], app_dir, entry)
            _launch_python(entry, app_dir, target, py, heal=False)
            return
    if proc.poll() is not None:
        entry.status, entry.exit_code = "exited", proc.returncode
        entry.note = f"Process exited (code {proc.returncode}) before serving."


def _missing_module(entry: AppProc) -> str | None:
    for line in reversed(entry.logs):
        m = re.search(r"ModuleNotFoundError: No module named ['\"]([\w.]+)['\"]", line)
        if m:
            return m.group(1).split(".")[0]
    return None


def _detect_port_from_logs(entry: AppProc) -> int | None:
    """Parse the port the server announced in its own output (e.g. 'Server started on port 3000',
    'Local: http://localhost:5173'). This is reliable — unlike blindly scanning common ports, which
    can latch onto an UNRELATED process already listening on 8080/3000."""
    pat = re.compile(r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0|port)[:\s]+(\d{2,5})", re.IGNORECASE)
    for line in reversed(entry.logs):
        m = pat.search(line)
        if m:
            p = int(m.group(1))
            if 1024 <= p <= 65535:
                return p
    return None


def _await_running(entry: AppProc, proc: subprocess.Popen, port: int, *, scan_others: bool = False) -> bool:
    """Poll until the server is reachable (running) or the process dies. Deterministic apps bind the
    exact port we assigned; apps that pick their own port (node servers / CRA) are found via the port
    THEY announce in their logs — never a blind common-port scan (which mis-detects other processes)."""
    deadline = time.monotonic() + _HEALTH_TIMEOUT
    while time.monotonic() < deadline:
        if _port_open(port):  # the app honored the port we assigned (PORT env / --port)
            entry.port, entry.url, entry.status = port, f"http://127.0.0.1:{port}", "running"
            entry.note = "Running."
            return True
        if scan_others:  # the app chose its own port — trust only what it printed
            lp = _detect_port_from_logs(entry)
            if lp and lp != port and _port_open(lp):
                entry.port, entry.url, entry.status = lp, f"http://127.0.0.1:{lp}", "running"
                entry.note = f"Running (the app chose port {lp})."
                return True
        if proc.poll() is not None:
            return False
        time.sleep(0.5)
    if proc.poll() is None:  # still alive but never answered — surface it as up, port unknown
        lp = _detect_port_from_logs(entry) if scan_others else None
        if lp:
            entry.port, entry.url = lp, f"http://127.0.0.1:{lp}"
        entry.status = "running"
        entry.note = "Started (port not detected — open from the logs if needed)." if not lp else f"Running (port {lp})."
        return True
    return False


# ---------------------------------------------------------------------------- node supervisor
def _node_launch(entry: AppProc, app_dir: Path, npm: str, fw: str, port: int) -> tuple[list[str], bool]:
    """Build the launch command for a Node app by framework, plus whether to port-SCAN for it.

    vite/next bind the exact port we pass (deterministic, no scan). cra/plain-server pick their own
    port (from $PORT or a hardcoded value), so we pass PORT and scan a few common ports to find it —
    THIS is what makes an Express/server.js backend run instead of hanging on a Vite-style port."""
    import json

    has_dev = _has_npm_script(app_dir, "dev")
    has_start = _has_npm_script(app_dir, "start")
    if fw == "vite":
        script = "dev" if has_dev else "start"
        return _node_argv(npm, ["run", script, "--", "--host", "127.0.0.1", "--port", str(port), "--strictPort"]), False
    if fw == "next":
        script = "dev" if has_dev else "start"
        return _node_argv(npm, ["run", script, "--", "-p", str(port), "-H", "127.0.0.1"]), False
    if fw == "cra":  # react-scripts reads $PORT/$HOST; scan in case it lands elsewhere
        return _node_argv(npm, ["start"]), True
    # plain Node server (express/koa/fastify/…): prefer its start script, else `node <main/server file>`.
    if has_start:
        return _node_argv(npm, ["start"]), True
    main = None
    try:
        main = (json.loads((app_dir / "package.json").read_text(encoding="utf-8", errors="replace")) or {}).get("main")
    except Exception:  # noqa: BLE001
        pass
    entry_file = main or next((f for f in ("server.js", "app.js", "index.js", "src/index.js", "src/server.js")
                               if (app_dir / f).exists()), "index.js")
    node = shutil_which("node") or "node"
    return [node, entry_file], True


def _supervise_node(entry: AppProc, app_dir: Path) -> None:
    try:
        npm = shutil_which("npm")
        if npm is None:
            entry.status = "error"
            entry.note = "Node/npm not found — install Node.js 20+ to run this app."
            _log(entry, entry.note)
            return
        if not (app_dir / "node_modules").exists():
            entry.status = "installing"
            _log(entry, "Installing npm dependencies…")
            if _run_step(_node_argv(npm, ["install", "--no-audit", "--no-fund"]), app_dir, entry) != 0:
                entry.status = "error"
                entry.note = "npm install failed — see logs."
                return
        port = _free_port()
        entry.port, entry.status = port, "starting"
        entry.url = f"http://127.0.0.1:{port}"
        cmd, scan = _node_launch(entry, app_dir, npm, entry.framework, port)
        env = _minimal_env()
        env["PORT"] = str(port)
        env["HOST"] = "127.0.0.1"
        env["BROWSER"] = "none"
        _log(entry, f"Starting ({entry.framework}): {' '.join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))}")
        proc = subprocess.Popen(  # noqa: S603 - argv list, no shell, jailed cwd, minimal env
            cmd, cwd=str(app_dir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            env=env, bufsize=1, **_spawn_kwargs(),
        )
        entry.proc = proc
        threading.Thread(target=_read_into, args=(proc, entry), daemon=True).start()
        _await_running(entry, proc, port, scan_others=scan)
        if proc.poll() is not None and entry.status != "running":  # crashed before binding -> surface it
            entry.status, entry.exit_code = "exited", proc.returncode
            entry.note = f"Process exited (code {proc.returncode}) before serving — see logs."
    except Exception as exc:  # noqa: BLE001
        entry.status = "error"
        entry.note = f"{type(exc).__name__}: {str(exc)[:160]}"
        _log(entry, f"! supervisor error: {entry.note}")


def _node_argv(npm: str, args: list[str]) -> list[str]:
    """Build a launch argv for an npm command. On Windows npm is a ``.cmd`` batch file, which
    CreateProcess can't run from a bare argv — route it through the command interpreter. All args
    here are controlled constants (no user input), so there's no shell-injection surface."""
    if os.name == "nt":
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", npm, *args]
    return [npm, *args]


def _has_npm_script(app_dir: Path, name: str) -> bool:
    import json

    try:
        pkg = json.loads((app_dir / "package.json").read_text(encoding="utf-8", errors="replace"))
        return name in (pkg.get("scripts") or {})
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------- public API
def _entry_view(e: AppProc) -> dict:
    tail = list(e.logs)[-250:]
    return {
        "runKey": e.key, "rel": e.rel, "kind": e.kind, "name": e.name, "framework": e.framework,
        "status": e.status, "port": e.port, "url": e.url if e.status == "running" else None,
        "exitCode": e.exit_code, "note": e.note, "logsTail": "\n".join(tail),
    }


def start_app(project_id: str | None, root_rel: str) -> dict:
    """Discover targets in ``root_rel`` and (re)launch any not already running. Returns the aggregate
    status immediately (setup + serving happen on a background thread). Never raises."""
    pid = safe_project_id(project_id)
    try:
        targets = discover_targets(pid, root_rel)
    except (ValueError, FileNotFoundError) as exc:
        return {"dir": root_rel, "targets": [], "note": f"Cannot run {root_rel!r}: {type(exc).__name__}"}
    if not targets:
        return {"dir": root_rel, "targets": [], "note": "No runnable backend/frontend found in this project."}
    for t in targets:
        key = f"{pid}::{t['rel']}"
        with _LOCK:
            existing = _REG.get(key)
            if existing and existing.status not in _TERMINAL:
                continue  # already installing/starting/running — leave it
            entry = AppProc(key=key, project_id=pid, rel=t["rel"], kind=t["kind"], name=t["name"],
                            framework=t["framework"], status="installing", started_at=time.monotonic())
            _REG[key] = entry
        app_dir = _jail_dir(pid, t["rel"])
        fn = (lambda e=entry, d=app_dir, tt=t: _supervise_python(e, d, tt)) if t["kind"] == "python" \
            else (lambda e=entry, d=app_dir: _supervise_node(e, d))
        th = threading.Thread(target=fn, daemon=True)
        entry.thread = th
        th.start()
    return app_status(pid, root_rel)


_CATEGORY_PREF = {"docs": 0, "backend": 1, "frontend": 2, "presentations": 3, "reports": 4}


def list_apps(project_id: str | None) -> list[dict]:
    """One entry per generated app (workflow), de-duplicating the same wf_* that the artifact filer
    scatters across category dirs (docs/backend/frontend/reports). For each workflow we pick the BEST
    root — the one exposing the most runnable targets, preferring docs (the architect's full tree) —
    so the UI shows ONE card per app pointed at the right directory, not four fragments."""
    pid = safe_project_id(project_id)
    root = project_root(pid)
    if not root.is_dir():
        return []
    candidates: dict[str, list[tuple[int, str]]] = {}
    for cat in sorted(root.iterdir()):
        if not cat.is_dir() or cat.name.startswith("."):
            continue
        pref = _CATEGORY_PREF.get(cat.name, 9)
        for wf in sorted(cat.iterdir()):
            if wf.is_dir() and wf.name.startswith("wf_"):
                candidates.setdefault(wf.name, []).append((pref, f"{cat.name}/{wf.name}"))
    apps: list[dict] = []
    for wf_id, opts in candidates.items():
        best_rel, best_score = None, (-1, 99)
        for pref, rel in opts:
            try:
                n = len(discover_targets(pid, rel))
            except Exception:  # noqa: BLE001
                n = 0
            score = (n, -pref)  # most targets first; tie -> lowest category pref (docs)
            if score > best_score:
                best_score, best_rel = score, rel
        if best_rel:
            apps.append({"wf_id": wf_id, "dir": best_rel, "name": wf_id})
    apps.sort(key=lambda a: a["wf_id"])
    return apps


def app_status(project_id: str | None, root_rel: str) -> dict:
    """Aggregate status for a project dir: every running/known target plus any not-yet-run target
    (shown as ``idle``). Never raises."""
    pid = safe_project_id(project_id)
    prefix = root_rel.rstrip("/")
    out: list[dict] = []
    seen: set[str] = set()
    with _LOCK:
        for e in _REG.values():
            if e.project_id == pid and (e.rel == prefix or e.rel.startswith(prefix + "/")):
                out.append(_entry_view(e))
                seen.add(e.rel)
    try:  # include not-yet-run targets so the UI can show "2 apps detected"
        for t in discover_targets(pid, root_rel):
            if t["rel"] not in seen:
                out.append({"runKey": f"{pid}::{t['rel']}", "rel": t["rel"], "kind": t["kind"],
                            "name": t["name"], "framework": t["framework"], "status": "idle",
                            "port": None, "url": None, "exitCode": None, "note": "", "logsTail": ""})
    except (ValueError, FileNotFoundError):
        pass
    out.sort(key=lambda v: (v["kind"] != "python", v["rel"]))  # backend first
    return {"dir": root_rel, "targets": out, "note": ""}


def stop_app(project_id: str | None, run_key: str) -> dict:
    """Stop one target by its runKey (process-tree kill). Returns the target's new status."""
    pid = safe_project_id(project_id)
    with _LOCK:
        entry = _REG.get(run_key)
    if entry is None or entry.project_id != pid:
        return {"runKey": run_key, "status": "idle", "note": "No such running target."}
    if entry.proc is not None and entry.proc.poll() is None:
        _kill_tree(entry.proc)
    entry.status, entry.note = "stopped", "Stopped."
    _log(entry, "Stopped by user.")
    return _entry_view(entry)


def stop_dir(project_id: str | None, root_rel: str) -> dict:
    """Stop every running target under a project dir."""
    pid = safe_project_id(project_id)
    prefix = root_rel.rstrip("/")
    with _LOCK:
        keys = [k for k, e in _REG.items()
                if e.project_id == pid and (e.rel == prefix or e.rel.startswith(prefix + "/"))]
    for k in keys:
        stop_app(pid, k)
    return app_status(pid, root_rel)


def stop_all() -> None:
    """Kill every tracked process — wired to app shutdown and usable as a global kill switch."""
    with _LOCK:
        entries = list(_REG.values())
    for e in entries:
        try:
            if e.proc is not None and e.proc.poll() is None:
                _kill_tree(e.proc)
                e.status = "stopped"
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------- download (zip)
def zip_app(project_id: str | None, root_rel: str) -> tuple[str, bytes]:
    """Zip ONLY the real application files of ``root_rel`` (excludes .venv/node_modules/caches and the
    agent transcript .md files). Returns (filename, zip_bytes). Raises ValueError/FileNotFoundError on
    a bad path."""
    pid = safe_project_id(project_id)
    abs_root = _jail_dir(pid, root_rel)
    # agent transcript files sit at the project root as "<agent-id>.md" — exclude those, keep README.
    agent_md = {p.name for p in abs_root.glob("*.md") if p.name.lower() != "readme.md"}
    buf = io.BytesIO()
    arc_root = abs_root.name or "app"
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in abs_root.rglob("*"):
            if not path.is_file():
                continue
            rel_parts = path.resolve().relative_to(abs_root.resolve()).parts
            if any(part in _ZIP_SKIP_DIRS for part in rel_parts):
                continue
            if path.suffix.lower() in _ZIP_SKIP_SUFFIX:
                continue
            if len(rel_parts) == 1 and path.name in agent_md:  # top-level agent transcript
                continue
            try:
                zf.write(path, arcname=f"{arc_root}/{'/'.join(rel_parts)}")
            except Exception as exc:  # noqa: BLE001 - skip an unreadable file, never fail the zip
                logger.debug("zip skipped {}: {}", path, exc)
    return f"{arc_root}.zip", buf.getvalue()
