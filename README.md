# FloatTube

A lightweight **macOS Safari extension** that opens YouTube in Safari's native Picture in Picture window. Click the PiP icon in YouTube's player controls, move or resize the floating video, and keep watching while using other apps and desktop Spaces.

The button matches YouTube's player controls. FloatTube reuses the original video element: no second stream, screen capture, re-encoding, analytics, or third-party runtime dependencies. Video aspect ratio and Safari's system controls are preserved. Window sizes and full-screen behavior are governed by macOS; zero playback issues cannot be guaranteed.

## Install on your Mac

Requirements: macOS 13 or later, Safari with native PiP support, full Xcode with its initial setup completed, Python 3, and Node.js 22 or later for development checks. This project targets **macOS only**; it does not build iPhone/iPad or other-browser packages.

```sh
git clone https://github.com/7oolguy/FloatTube.git
cd FloatTube
npm test
npm run check
./build-safari.command
./scripts/install-local.sh
```

Open FloatTube from Applications, then enable it in Safari Settings → Extensions and allow access to youtube.com. Reload YouTube, play a video, and click the PiP icon in the right-hand player controls. Keep the YouTube tab open. Drag the floating window's edges to resize it.

Personal development builds do not require a paid developer membership. They require Safari's **Allow unsigned extensions** developer setting, which may reset when Safari restarts. Enabling that setting relaxes Safari's extension signature checks. Build local source you trust; downloaded CI builds are development artifacts and may be blocked by Gatekeeper. A ZIP containing extension JavaScript alone is not directly installable in Safari.

## Automatic builds

GitHub Actions runs tests, permission/tracked-file checks, a redacted secret scan, and a universal macOS Release compilation on every push and pull request. Download `FloatTube-macOS-development` from a successful Actions run. It contains the app ZIP, SHA-256 checksum, and public build metadata. Both Apple Silicon and Intel are compiled; Intel runtime behavior still requires hardware testing.

```sh
./build-safari.command --universal
```

Build outputs live in ignored `build/` and `dist/` directories. No dependency installation is required for the JavaScript tests. GitHub Actions dependencies are pinned to commit hashes and Dependabot checks weekly for updates.

## Updates

For the current unsigned development install, pull reviewed source changes, rebuild, and run the installer again. Safari may cache extension resources; reopen FloatTube and reload YouTube, or toggle the extension/restart Safari if necessary.

An optional hourly updater is included for **future signed and notarized releases**. It requires an explicitly configured Apple Team ID and refuses unsigned downloads, mismatched app identities, unsafe archives, and updates rejected by Gatekeeper. It is **not enabled** for the current development build. A paid Apple Developer membership is needed to publish compatible signed releases. See [builds, versioning, and updater setup](docs/RELEASING.md).

## Project layout

| Path | Purpose |
| --- | --- |
| `extension/` | YouTube content script, native PiP adapter, and styles |
| `scripts/build.py` | Generate, compile, verify, and package the macOS app |
| `scripts/install-local.sh` | Install a locally built app |
| `scripts/version.py` | Derive SemVer from Conventional Commits |
| `scripts/update.py` | Opt-in updater for signed releases |
| `tests/` | Playback API, release version, and archive safety tests |
| `.github/` | macOS CI and dependency update configuration |

## Checks and privacy

```sh
npm test
npm run check
python3 -m unittest discover -s tests -p '*_test.py'
python3 scripts/check.py
gitleaks git --redact --no-banner .
```

The extension requests no extra API permissions and runs only on HTTPS YouTube pages. The optional updater contacts GitHub only when invoked or explicitly scheduled. Certificates, credentials, local paths, build logs, generated projects, and editor state must not be committed. See [security and privacy](SECURITY.md).

Manual acceptance: verify PiP entry/return, player alignment, YouTube navigation, resizing, switching apps/Spaces/full-screen apps, and external monitors if used. Mock API tests do not measure playback performance. Safari PiP was exercised locally; comprehensive full-screen, Intel, and performance testing has not been completed.

Built using [Apple's Safari extension packaging](https://developer.apple.com/documentation/safariservices/packaging-a-web-extension-for-safari) and [native PiP](https://developer.apple.com/documentation/webkitjs/adding_picture_in_picture_to_your_safari_media_controls). FloatTube is independent of YouTube and is not affiliated with Google or Apple.
