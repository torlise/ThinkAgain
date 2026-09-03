from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = "https://api.github.com/repositories/1354812594"
TOKEN = os.environ.get("GITHUB_TOKEN")


def request(method: str, path: str, payload: dict | None = None) -> dict:
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is not set")

    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "codex-thinkagain-publisher",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    last_error = None
    for attempt in range(3):
        req = urllib.request.Request(
            f"{API_ROOT}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                text = response.read().decode("utf-8")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {body}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 + attempt * 3)
                continue
    raise RuntimeError(str(last_error))


def git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("utf-8")
    return hashlib.sha1(header + raw).hexdigest()


def iter_files() -> list[Path]:
    excluded_dirs = {".git", "__pycache__"}
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded_dirs for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def upsert_file(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    api_path = "/contents/" + urllib.parse.quote(rel, safe="/")
    raw = path.read_bytes()
    payload = {
        "message": f"Add Think Again reader file: {rel}",
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": "main",
    }
    try:
        current = request("GET", api_path + "?ref=main")
        if current.get("sha") == git_blob_sha(raw):
            print(f"skip {rel}")
            return current["sha"]
        payload["sha"] = current["sha"]
        payload["message"] = f"Update Think Again reader file: {rel}"
    except RuntimeError as exc:
        if " 404 " not in str(exc):
            raise
    result = request("PUT", api_path, payload)
    print(f"upload {rel}")
    return result["commit"]["sha"]


def enable_pages() -> dict:
    try:
        result = request(
            "POST",
            "/pages",
            {
                "source": {
                    "branch": "main",
                    "path": "/",
                },
            },
        )
        return {"enabled": True, "html_url": result.get("html_url")}
    except Exception as exc:
        return {"enabled": False, "note": str(exc)}


def main() -> None:
    uploaded = []
    for path in iter_files():
        commit_sha = upsert_file(path)
        uploaded.append({"path": path.relative_to(ROOT).as_posix(), "commit_sha": commit_sha})

    print(
        json.dumps(
            {
                "commit_sha": uploaded[-1]["commit_sha"] if uploaded else None,
                "file_count": len(uploaded),
                "pages": enable_pages(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
