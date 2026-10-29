#!/usr/bin/env python3
"""Opt-in macOS updater. Only trusted, notarized Developer ID releases install."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import platform
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import uuid
import zipfile

REPOSITORY = "7oolguy/FloatTube"
BUNDLE_ID = "com.yansilva.FloatTube"
APP = Path("/Applications/FloatTube.app")
LABEL = "com.yansilva.FloatTube.updater"
SUPPORT = Path.home() / "Library/Application Support/FloatTube"
AGENT = Path.home() / "Library/LaunchAgents" / (LABEL + ".plist")
MAX_DOWNLOAD = 128 * 1024 * 1024

def version(value):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise ValueError("Expected stable semantic version")
    return tuple(map(int, value.split(".")))

def read_info(app):
    with (app / "Contents/Info.plist").open("rb") as source:
        return plistlib.load(source)

def fetch(url, destination=None):
    request = urllib.request.Request(url, headers={"User-Agent": "FloatTube-Updater", "Accept": "application/vnd.github+json" if destination is None else "application/octet-stream"})
    with urllib.request.urlopen(request, timeout=30) as response:
        final = urllib.parse.urlparse(response.url)
        if final.scheme != "https" or final.hostname not in {"api.github.com", "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}:
            raise ValueError("Unexpected update host")
        limit = MAX_DOWNLOAD if destination else 2 * 1024 * 1024
        if destination:
            with destination.open("wb") as output:
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk: break
                    total += len(chunk)
                    if total > limit: raise ValueError("Update exceeds size limit")
                    output.write(chunk)
        else:
            data = response.read(limit + 1)
            if len(data) > limit: raise ValueError("Release metadata exceeds size limit")
            return json.loads(data)

def validate_archive(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 10000 or sum(i.file_size for i in entries) > 512 * 1024 * 1024:
            raise ValueError("Archive exceeds extraction limits")
        names = set()
        for item in entries:
            name = PurePosixPath(item.filename)
            if name.is_absolute() or ".." in name.parts or "\\" in item.filename or not name.parts or name.parts[0] != "FloatTube.app":
                raise ValueError("Unexpected archive path")
            if item.filename in names: raise ValueError("Duplicate archive entry")
            names.add(item.filename)
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("Update archive may not contain symbolic links")

def verify(app, team, expected_version):
    info = read_info(app)
    if info.get("CFBundleIdentifier") != BUNDLE_ID or info.get("CFBundleShortVersionString") != expected_version:
        raise ValueError("Update identity/version mismatch")
    requirement = f'anchor apple generic and identifier "{BUNDLE_ID}" and certificate leaf[subject.OU] = "{team}"'
    subprocess.run(["codesign", "--verify", "--deep", "--strict", "-R", requirement, str(app)], check=True)
    subprocess.run(["spctl", "--assess", "--type", "execute", str(app)], check=True)
    subprocess.run(["xcrun", "stapler", "validate", str(app)], check=True)

def install_agent(team):
    SUPPORT.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = SUPPORT / "update.py"
    if Path(__file__).resolve() != target.resolve(): shutil.copy2(__file__, target)
    AGENT.parent.mkdir(parents=True, exist_ok=True)
    config = {"Label": LABEL, "ProgramArguments": [sys.executable, str(target), "--team", team],
        "StartInterval": 3600, "RunAtLoad": True, "ProcessType": "Background",
        "StandardOutPath": str(SUPPORT / "updater.log"), "StandardErrorPath": str(SUPPORT / "updater-error.log")}
    AGENT.write_bytes(plistlib.dumps(config))
    AGENT.chmod(0o600)
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(AGENT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(AGENT)], check=True)
    print("Hourly signed updates enabled.")

def update(team):
    if not APP.is_dir() or APP.is_symlink(): raise ValueError("Install FloatTube in Applications first; symbolic links are not supported")
    current = read_info(APP)
    if current.get("CFBundleIdentifier") != BUNDLE_ID: raise ValueError("Installed app identity mismatch")
    release = fetch(f"https://api.github.com/repos/{REPOSITORY}/releases/latest")
    tag = release.get("tag_name", "")
    if release.get("draft") or release.get("prerelease") or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Expected a stable published release")
    remote_version = tag[1:]
    if version(remote_version) <= version(current["CFBundleShortVersionString"]):
        print("Already up to date."); return
    asset = next((a for a in release.get("assets", []) if a.get("name") == "FloatTube-macOS.zip"), None)
    if not asset or asset.get("size", 0) > MAX_DOWNLOAD: raise ValueError("No suitable signed release asset")
    url = asset.get("browser_download_url", "")
    if url != f"https://github.com/{REPOSITORY}/releases/download/{tag}/FloatTube-macOS.zip":
        raise ValueError("Unexpected asset URL")
    if not os.access(APP.parent, os.W_OK): raise ValueError("Applications folder is not writable; update manually")
    with tempfile.TemporaryDirectory(prefix="floattube-update-") as temporary:
        folder = Path(temporary)
        archive = folder / "update.zip"
        fetch(url, archive)
        validate_archive(archive)
        extracted = folder / "extracted"
        subprocess.run(["ditto", "-x", "-k", str(archive), str(extracted)], check=True)
        candidate = extracted / "FloatTube.app"
        verify(candidate, team, remote_version)
        staging = APP.parent / (".FloatTube-update-" + uuid.uuid4().hex + ".app")
        backup = APP.parent / ("FloatTube-previous-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8] + ".app")
        try:
            shutil.copytree(candidate, staging)
            verify(staging, team, remote_version)
            APP.rename(backup)
            try: staging.rename(APP)
            except OSError:
                backup.rename(APP)
                raise
        finally:
            if staging.exists(): shutil.rmtree(staging)
        print("Updated to " + remote_version + ". Previous app retained at " + backup.name)
        print("Reload YouTube or restart Safari to load updated extension resources.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", help="Expected 10-character Apple Team ID")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--install-agent", action="store_true")
    group.add_argument("--remove-agent", action="store_true")
    args = parser.parse_args()
    if platform.system() != "Darwin": parser.error("This updater is macOS-only")
    if args.remove_agent:
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(AGENT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        AGENT.unlink(missing_ok=True)
        print("Automatic updates disabled. Logs and updater copy retained."); return
    if not args.team or not re.fullmatch(r"[A-Z0-9]{10}", args.team): parser.error("Configure the expected Apple Team ID; unsigned updates are not supported")
    if args.install_agent: install_agent(args.team); return
    SUPPORT.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = SUPPORT / "update.lock"
    try: lock.mkdir(mode=0o700)
    except FileExistsError: raise SystemExit("Another update is running, or a stale update.lock needs manual removal")
    try: update(args.team)
    finally: lock.rmdir()

if __name__ == "__main__":
    try: main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print("Update stopped: " + str(error), file=sys.stderr)
        sys.exit(1)
