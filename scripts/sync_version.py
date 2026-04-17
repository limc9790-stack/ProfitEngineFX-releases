#!/usr/bin/env python3
"""
sync_version.py — Keeps ProfitEngineFX landing page in sync with the latest release.

Usage:
    python sync_version.py

Reads the latest release tag from ProfitEngineFX-releases, compares it with
the version embedded in landing-page/index.html (or index.html at root of the
releases repo), and pushes an update if they differ.

Requirements:
    - GitHub CLI (`gh`) installed and authenticated
    - Python 3.7+
"""

import base64
import json
import re
import subprocess
import sys


RELEASES_REPO = "limc9790-stack/ProfitEngineFX-releases"
LANDING_REPO  = "limc9790-stack/ProfitEngineFX-releases"  # landing page lives here
LANDING_PATH  = "index.html"

DOWNLOAD_URL_TEMPLATE = (
    "https://github.com/limc9790-stack/ProfitEngineFX-releases"
    "/releases/download/v{ver}/ProfitEngineFX.Setup.{ver}.exe"
)


def gh(*args) -> str:
    """Run a gh command and return stdout. Raises on non-zero exit."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR running: gh {' '.join(args)}", file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_latest_version() -> str:
    """Return the version string (without leading 'v') of the latest release."""
    tag = gh("api", f"repos/{RELEASES_REPO}/releases/latest", "--jq", ".tag_name")
    return tag.lstrip("v")


def get_file(repo: str, path: str) -> tuple[str, str]:
    """Return (decoded_content, sha) for a file in a GitHub repo."""
    raw = gh("api", f"repos/{repo}/contents/{path}")
    data = json.loads(raw)
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def find_html_version(html: str) -> str | None:
    """
    Detect the version currently embedded in the HTML.
    Looks for patterns like  v1.0.8  or  1.0.8  near download/version context.
    Returns the version string without leading 'v', or None if not found.
    """
    # Try explicit download URL first (most reliable)
    m = re.search(
        r"releases/download/v(\d+\.\d+\.\d+)/ProfitEngineFX",
        html,
    )
    if m:
        return m.group(1)

    # Fall back to any semver in the file
    m = re.search(r"\bv?(\d+\.\d+\.\d+)\b", html)
    if m:
        return m.group(1)

    return None


def update_html(html: str, old_ver: str, new_ver: str) -> str:
    """Replace all references to old_ver with new_ver and fix the download URL."""
    # Replace bare version numbers (e.g. 1.0.8 → 1.0.9)
    updated = html.replace(old_ver, new_ver)

    # Ensure the download URL matches the canonical template
    old_url_pattern = re.compile(
        r"https://github\.com/limc9790-stack/ProfitEngineFX-releases"
        r"/releases/download/v" + re.escape(new_ver) +
        r"/ProfitEngineFX\.Setup\." + re.escape(new_ver) + r"\.exe"
    )
    new_url = DOWNLOAD_URL_TEMPLATE.format(ver=new_ver)
    # If the URL is already correct this is a no-op
    if not old_url_pattern.search(updated):
        # Reconstruct any malformed download URL
        updated = re.sub(
            r"https://github\.com/limc9790-stack/ProfitEngineFX-releases"
            r"/releases/download/v[^/]+/ProfitEngineFX\.Setup\.[^\"]+\.exe",
            new_url,
            updated,
        )

    return updated


def put_file(repo: str, path: str, sha: str, content: str, message: str) -> str:
    """Push updated file content back to GitHub. Returns new commit SHA."""
    payload = {
        "message": message,
        "sha": sha,
        "content": base64.b64encode(content.encode("utf-8")).decode(),
    }

    import tempfile, os
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(payload, tmp)
        tmp_path = tmp.name

    try:
        result = gh(
            "api", "--method", "PUT",
            f"repos/{repo}/contents/{path}",
            "--input", tmp_path,
            "--jq", ".commit.sha",
        )
    finally:
        os.unlink(tmp_path)

    return result


def main():
    print("Fetching latest release tag…")
    latest_ver = get_latest_version()
    print(f"  Latest release : v{latest_ver}")

    print(f"Fetching {LANDING_PATH} from {LANDING_REPO}…")
    html, sha = get_file(LANDING_REPO, LANDING_PATH)

    html_ver = find_html_version(html)
    if html_ver is None:
        print("ERROR: Could not detect current version in HTML.", file=sys.stderr)
        sys.exit(1)

    print(f"  HTML version   : v{html_ver}")

    if html_ver == latest_ver:
        print(f"\nAlready up to date (v{latest_ver}). Nothing to do.")
        return

    print(f"\nUpdating landing page from v{html_ver} to v{latest_ver}…")
    updated_html = update_html(html, html_ver, latest_ver)

    commit_sha = put_file(
        LANDING_REPO,
        LANDING_PATH,
        sha,
        updated_html,
        f"fix: update landing page version from v{html_ver} to v{latest_ver}",
    )

    print(f"Updated landing page from v{html_ver} to v{latest_ver}")
    print(f"Commit: {commit_sha}")


if __name__ == "__main__":
    main()
