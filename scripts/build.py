#!/usr/bin/env python3
"""Generate a macOS-only Safari app, compile it, and package an explicit artifact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def git(*args):
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signed", action="store_true", help="Require Developer ID signing and notarization")
    parser.add_argument("--universal", action="store_true", help="Compile arm64 and x86_64")
    args = parser.parse_args()
    if platform.system() != "Darwin":
        parser.error("Safari builds require macOS and full Xcode.")
    if not os.environ.get("DEVELOPER_DIR") and Path("/Applications/Xcode.app/Contents/Developer").exists():
        os.environ["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"
    run("xcrun", "--find", "safari-web-extension-converter", stdout=subprocess.DEVNULL)
    version = subprocess.check_output([sys.executable, str(ROOT / "scripts/version.py")], text=True).strip()
    build_number = os.environ.get("GITHUB_RUN_NUMBER", git("rev-list", "--count", "HEAD") or "1")
    if not build_number.isdigit():
        parser.error("Build number must be numeric.")
    identity = os.environ.get("FLOATTUBE_SIGN_IDENTITY", "")
    profile = os.environ.get("FLOATTUBE_NOTARY_PROFILE", "")
    if args.signed and (not identity.startswith("Developer ID Application:") or not profile):
        parser.error("Set FLOATTUBE_SIGN_IDENTITY and FLOATTUBE_NOTARY_PROFILE for signed builds.")
    build = ROOT / "build"
    resources = build / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    # Only the browser extension goes into the Safari bundle, never the repository.
    for path in (ROOT / "extension").iterdir():
        if path.is_file():
            shutil.copy2(path, resources / path.name)
    manifest = json.loads((resources / "manifest.json").read_text())
    manifest["version"] = version
    (resources / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    run("xcrun", "safari-web-extension-converter", str(resources),
        "--project-location", str(build / "generated"), "--app-name", "FloatTube",
        "--bundle-identifier", "com.yansilva.FloatTube", "--macos-only", "--swift",
        "--copy-resources", "--no-open", "--no-prompt", "--force")
    project = build / "generated/FloatTube/FloatTube.xcodeproj"
    log = build / "compile.log"
    command = ["xcodebuild", "-project", str(project), "-scheme", "FloatTube",
        "-configuration", "Release", "-derivedDataPath", str(build / "DerivedData"),
        "MACOSX_DEPLOYMENT_TARGET=13.0", "MARKETING_VERSION=" + version,
        "CURRENT_PROJECT_VERSION=" + build_number, "CODE_SIGN_IDENTITY=" + (identity if args.signed else "-"),
        "CODE_SIGN_STYLE=Manual", "CODE_SIGNING_ALLOWED=YES",
        "GCC_GENERATE_DEBUGGING_SYMBOLS=NO", "SWIFT_SERIALIZE_DEBUGGING_OPTIONS=NO",
        "COPY_PHASE_STRIP=YES", "STRIP_INSTALLED_PRODUCT=YES"]
    if args.universal:
        command += ["ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO"]
    if args.signed:
        command += ["ENABLE_HARDENED_RUNTIME=YES"]
    with log.open("w") as output:
        try:
            run(*command, "build", stdout=output, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            print("Build failed. See build/compile.log", file=sys.stderr)
            raise
    app = build / "DerivedData/Build/Products/Release/FloatTube.app"
    run("codesign", "--verify", "--deep", "--strict", str(app))
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    channel = "macOS" if args.signed else "macOS-development"
    archive = dist / ("FloatTube-" + channel + ".zip")
    run("ditto", "-c", "-k", "--keepParent", str(app), str(archive))
    if args.signed:
        run("xcrun", "notarytool", "submit", str(archive), "--keychain-profile", profile, "--wait")
        run("xcrun", "stapler", "staple", str(app))
        run("spctl", "--assess", "--type", "execute", str(app))
        run("ditto", "-c", "-k", "--keepParent", str(app), str(archive))
    # Reject accidental local home paths in public artifacts.
    with zipfile.ZipFile(archive) as package:
        private_prefix = str(Path.home()).encode() + b"/"
        for name in package.namelist():
            if private_prefix in package.read(name):
                archive.unlink()
                raise RuntimeError("Packaged app contains a local home path; distribution stopped")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / (archive.name + ".sha256")).write_text(digest + "  " + archive.name + "\n")
    metadata = {"version": version, "build": build_number, "commit": git("rev-parse", "HEAD"),
        "signed": args.signed, "architecture": "universal" if args.universal else platform.machine()}
    (dist / "build-info.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Built " + archive.name + " (" + version + ")")

if __name__ == "__main__":
    main()
