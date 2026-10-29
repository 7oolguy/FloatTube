#!/usr/bin/env python3
"""Check manifest scope and tracked files before publication."""
import json
from pathlib import Path
import re
import subprocess
ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "extension/manifest.json").read_text())
assert manifest["manifest_version"] == 3
assert manifest["content_scripts"][0]["matches"] == ["https://www.youtube.com/*", "https://m.youtube.com/*"]
assert not manifest.get("permissions") and not manifest.get("host_permissions")
assert not manifest.get("background")
files = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"], text=True).split("\0")
for name in filter(None, files):
    assert not re.search(r"(^|/)(build|dist|node_modules|xcuserdata|work)/|\.(p12|p8|pem|key|log|mobileprovision|zip|dmg)$|(^|/)\.env", name), "Forbidden tracked file: " + name
    data = (ROOT / name).read_bytes()
    assert len(data) < 1_000_000, "Unexpected large file: " + name
    text = data.decode("utf-8", errors="replace")
    assert not re.search(r"/(?:Users|home)/[A-Za-z0-9_.-]+/", text), "Personal absolute path: " + name
print("Manifest permissions and tracked-file checks passed.")
