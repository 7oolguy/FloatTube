# macOS builds and updates

## Development (no paid Apple account)

Install full Xcode, accept its license, and have Python 3 and Node.js 22+ available. Run:

```sh
npm test
npm run check
python3 -m unittest discover -s tests -p '*_test.py'
./build-safari.command --universal
./scripts/install-local.sh
```

The build generates a macOS-only Xcode project with Apple's converter. The project, DerivedData, build logs and artifacts are ignored. CI runs checks and compiles both Apple Silicon and Intel on every push/PR. Download the ZIP inside the Actions artifact; it is a development build, not notarized public software. Do not remove quarantine to bypass Gatekeeper. For personal use, build locally and enable Safari's developer setting for unsigned extensions.

## Versions

`scripts/version.py` calculates the next version from the latest reachable `vX.Y.Z` tag and Conventional Commits: `fix` increases patch, `feat` increases minor, and `!` or `BREAKING CHANGE:` increases major. Nonrelease commits retain the latest tagged version. The version is injected only into generated build inputs. Build numbers come from GitHub's run number or the local commit count. Do not edit package/manifest versions or manually create release tags as part of ordinary changes.

## Signed production releases (not configured yet)

A paid Apple Developer Program membership and Developer ID Application certificate are needed for direct distribution. Configure the identity in your login Keychain and store notarization credentials using `xcrun notarytool store-credentials`. Keep credentials outside this repo. Then:

```sh
export FLOATTUBE_SIGN_IDENTITY='Developer ID Application: YOUR NAME (TEAMID)'
export FLOATTUBE_NOTARY_PROFILE='floattube-notary'
./build-safari.command --signed --universal
```

The script signs the app and extension, submits the ZIP for notarization, staples the ticket, and assesses it with Gatekeeper before creating `dist/FloatTube-macOS.zip`. Publishing a production release is a separate authorized action. Publish this exact asset on a stable GitHub release whose tag is the calculated `vX.Y.Z`; the updater intentionally ignores prereleases and development artifacts. A future release workflow should create this tag only after the signed build passes. Automated signed publishing is not enabled without a signing account.

## Optional automatic updater

The updater is delivered but cannot install today's unsigned development builds. Once signed releases exist, run:

```sh
python3 scripts/update.py --install-agent --team YOUR_APPLE_TEAM_ID
```

This installs an hourly per-user LaunchAgent and a private copy of the updater under the user's Application Support folder. It uses that Python interpreter, which must remain installed, plus Apple command-line tools providing codesign, spctl, and xcrun stapler. It only updates `/Applications/FloatTube.app`; that location must be writable by the current user. It never uses sudo or prompts for credentials. It does not change Safari's permissions, quit Safari, or automatically launch an app. Safari may need a reload or restart to pick up new extension resources.

To check/install once: `python3 scripts/update.py --team YOUR_APPLE_TEAM_ID`.
To remove the scheduled updater: `python3 scripts/update.py --remove-agent`.
The updater verifies signed release contents before replacing the app, keeps one rollback copy next to it, and restores it if replacement fails. If Safari is actively using the app, macOS may defer updated resources until Safari restarts. New website permissions always remain a Safari/user decision.

Apple documentation: [Safari distribution](https://developer.apple.com/documentation/safariservices/distributing-your-safari-web-extension), [Developer ID](https://developer.apple.com/developer-id/).
