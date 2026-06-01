"""Guarded in-workspace code runner (cp-0035).

Runs a SINGLE generated file from the project workspace and returns its captured output —
the user's "run the program" feature, built to the project's hard constraints (NO Docker/VM):

  * PATH-JAILED: only a real file inside workspace/projects/<id>/ can be run (FileManager).
  * ALLOWLISTED: only an interpreter we map from the file extension (.py -> the venv python
    in isolated mode, .js/.mjs -> node if installed). Anything else is refused.
  * BOUNDED: a hard wall-clock timeout, captured + truncated stdout/stderr, no shell (argv list,
    so no shell-injection), cwd pinned to the file's folder, and a MINIMAL env (PATH essentials
    only) so the subprocess never inherits app/provider secrets.
  * NEVER RAISES: every failure (missing interpreter, timeout, IO) becomes a result with ok=False.

This is a guarded LOCAL subprocess, not an OS-level sandbox: generated code still runs with the
server user's privileges. It is opt-in (require_user) and single-admin by design.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from app.core.logging import logger
from app.services.artifacts import get_artifact_service
from app.workspace_fs.file_manager import WorkspaceViolationError
from app.workspace_fs.paths import safe_project_id

_TIMEOUT_SEC = 15.0          # hard wall-clock cap (keep < the frontend per-call axios timeout)
_OUTPUT_CAP = 20_000         # truncate captured stdout/stderr to keep responses sane

# extension -> argv prefix. Python uses -I (isolated: ignore env + user site) and -B (no .pyc).
_INTERPRETERS: dict[str, list[str]] = {
    ".py": [sys.executable, "-I", "-B"],
    ".js": ["node"],
    ".mjs": ["node"],
}

# A minimal env so interpreters resolve but NO app/provider secrets leak into the subprocess.
_ENV_KEEP = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "HOME", "LANG", "LC_ALL")


def _minimal_env() -> dict[str, str]:
    return {k: os.environ[k] for k in _ENV_KEEP if k in os.environ}


def _truncate(text: str) -> str:
    text = text or ""
    return text if len(text) <= _OUTPUT_CAP else text[:_OUTPUT_CAP] + f"\n…(truncated, {len(text)} chars total)"


def run_workspace_file(rel_path: str, project_id: str | None = None) -> dict:
    """Run one workspace file and return {path, command, ok, exitCode, timedOut, durationMs, stdout, stderr, note}.

    Never raises: an escape attempt / missing file / unsupported type / missing interpreter /
    timeout all return ``ok=False`` with an explanatory ``note``.
    """
    result = {
        "path": rel_path, "command": "", "ok": False, "exit_code": None,
        "timed_out": False, "duration_ms": 0, "stdout": "", "stderr": "", "note": "",
    }

    # 1) Resolve + jail the target (must be a real file inside this project's workspace).
    #    Kept inside try so even a bad project_id or an FS error degrades to ok=False (never raises).
    try:
        pid = safe_project_id(project_id)
        fm = get_artifact_service(pid).fm
        target = fm.media_file(rel_path)  # path-jailed; raises if it escapes or isn't a file
    except WorkspaceViolationError:
        result["note"] = "Path escapes the workspace sandbox."
        return result
    except FileNotFoundError:
        result["note"] = f"No such workspace file: {rel_path}"
        return result
    except Exception as exc:  # noqa: BLE001 - bad project id / FS error -> degrade, never raise
        result["note"] = f"Could not resolve file: {type(exc).__name__}"
        return result

    # 2) Allowlist by extension.
    argv = _INTERPRETERS.get(target.suffix.lower())
    if argv is None:
        result["note"] = f"Cannot run {target.suffix or 'this file type'}; runnable: {', '.join(sorted(_INTERPRETERS))}."
        return result
    interp = argv[0]
    if interp != sys.executable and shutil_which(interp) is None:
        result["note"] = f"Interpreter {interp!r} is not installed on this machine."
        return result

    cmd = [*argv, str(target)]
    result["command"] = f"{Path(interp).name} {' '.join(argv[1:])} {target.name}".strip()
    started = time.monotonic()
    try:
        # Launch in its OWN process group/session so the timeout can kill the WHOLE tree — a
        # grandchild the generated code spawns must not outlive the wall-clock cap as an orphan.
        spawn: dict = {}
        if os.name == "nt":
            spawn["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            spawn["start_new_session"] = True
        proc = subprocess.Popen(  # noqa: S603 - argv list (no shell), jailed path, minimal env
            cmd, cwd=str(target.parent), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=_minimal_env(), **spawn,
        )
        try:
            out, err = proc.communicate(timeout=_TIMEOUT_SEC)
            result["exit_code"] = proc.returncode
            result["stdout"] = _truncate(out)
            result["stderr"] = _truncate(err)
            result["ok"] = proc.returncode == 0
            result["note"] = "Ran successfully." if result["ok"] else f"Exited with code {proc.returncode}."
        except subprocess.TimeoutExpired:
            _kill_tree(proc)  # kill the process AND its descendants, not just the direct child
            try:
                out, err = proc.communicate(timeout=5)
            except Exception:  # noqa: BLE001 - reap best-effort after the kill
                out, err = "", ""
            result["timed_out"] = True
            result["stdout"] = _truncate(out or "")
            result["stderr"] = _truncate(err or "")
            result["note"] = f"Killed after the {_TIMEOUT_SEC:.0f}s time limit (process tree terminated)."
    except FileNotFoundError:
        result["note"] = f"Interpreter not available for {target.suffix}."
    except Exception as exc:  # noqa: BLE001 - never let a run crash the request
        logger.warning("code_runner failed for {}: {}", rel_path, repr(exc))
        result["note"] = f"Could not run: {type(exc).__name__}: {str(exc)[:160]}"
    result["duration_ms"] = int((time.monotonic() - started) * 1000)
    return result


def _kill_tree(proc: subprocess.Popen) -> None:
    """Terminate the launched process AND all its descendants.

    A plain ``proc.kill()`` leaves grandchildren running (Windows does no parent->child reaping),
    so a timed-out run could leave orphans past the cap. taskkill /T (Windows) / killpg (POSIX)
    take down the whole tree; fall back to a single-process kill if that fails.
    """
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, timeout=10, check=False)
        else:
            import os as _os
            import signal as _signal

            _os.killpg(_os.getpgid(proc.pid), _signal.SIGKILL)
    except Exception:  # noqa: BLE001 - last-resort single-process kill
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass


def shutil_which(name: str) -> str | None:
    import shutil

    return shutil.which(name)
