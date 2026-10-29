#!/usr/bin/env python3
"""Derive SemVer from conventional commits; never edit tracked version files."""
import re
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def git(*args):
    result = subprocess.run(["git", "-C", str(ROOT), *args], text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else ""

def next_version(tag, messages):
    version = tuple(map(int, tag.removeprefix("v").split("."))) if tag else (0, 0, 0)
    breaking = any("BREAKING CHANGE:" in m or re.match(r"^[a-z]+(?:\([^)]*\))?!:", m) for m in messages)
    feature = any(re.match(r"^feat(?:\([^)]*\))?:", m) for m in messages)
    fix = any(re.match(r"^fix(?:\([^)]*\))?:", m) for m in messages)
    major, minor, patch = version
    if breaking: return f"{major + 1}.0.0"
    if feature: return f"{major}.{minor + 1}.0"
    if fix: return f"{major}.{minor}.{patch + 1}"
    return ".".join(map(str, version)) if tag else "0.1.0"

def main():
    tags = git("tag", "--merged", "HEAD", "--sort=-version:refname").splitlines()
    tag = next((t for t in tags if re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", t)), "")
    revision = tag + "..HEAD" if tag else "HEAD"
    messages = [m.strip() for m in git("log", "--format=%B%x00", revision).split("\0") if m.strip()]
    print(next_version(tag, messages))

if __name__ == "__main__": main()
