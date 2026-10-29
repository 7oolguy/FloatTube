#!/bin/zsh
set -eu
cd "${0:A:h:h}"
APP="build/DerivedData/Build/Products/Release/FloatTube.app"
[[ -d "$APP" ]] || { echo "Run ./build-safari.command first."; exit 1; }
codesign --verify --deep --strict "$APP"
ditto "$APP" /Applications/FloatTube.app
pluginkit -r "$PWD/$APP/Contents/PlugIns/FloatTube Extension.appex" || true
pluginkit -a "/Applications/FloatTube.app/Contents/PlugIns/FloatTube Extension.appex"
echo "Installed /Applications/FloatTube.app. Enable it in Safari Settings → Extensions."
echo "For development builds, Safari must allow unsigned extensions. Reload YouTube after updating."
