#!/bin/zsh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$DIR/CHDMAN.app"
RES="$APP/Contents/Resources"
MACOS="$APP/Contents/MacOS"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

echo "→ Cleaning old build..."
rm -rf "$APP"

echo "→ Creating bundle structure..."
mkdir -p "$RES" "$MACOS"

# ── Copy resources ────────────────────────────────────────────────────────────
cp "$DIR/chdman_tool.py"                                        "$RES/"
cp "$DIR/Picture.jpg"                                           "$RES/"
cp "$DIR/Crash Bandicoot The Wrath of Cortex Theme.mp3"         "$RES/"

# ── Generate icon from Picture.jpg ───────────────────────────────────────────
echo "→ Building icon..."
ICONSET="$DIR/AppIcon.iconset"
mkdir -p "$ICONSET"
for SIZE in 16 32 64 128 256 512; do
    sips -s format png -z $SIZE $SIZE "$DIR/Picture.jpg" \
         --out "$ICONSET/icon_${SIZE}x${SIZE}.png" > /dev/null
    sips -s format png -z $((SIZE*2)) $((SIZE*2)) "$DIR/Picture.jpg" \
         --out "$ICONSET/icon_${SIZE}x${SIZE}@2x.png" > /dev/null
done
iconutil -c icns "$ICONSET" -o "$RES/AppIcon.icns"
rm -rf "$ICONSET"

# ── Launcher script ───────────────────────────────────────────────────────────
cat > "$MACOS/CHDMAN" << 'EOF'
#!/bin/zsh
SCRIPT_DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
exec arch -arm64 /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
     "$SCRIPT_DIR/chdman_tool.py"
EOF
chmod +x "$MACOS/CHDMAN"

# ── Info.plist ────────────────────────────────────────────────────────────────
cat > "$APP/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>CHDMAN</string>
    <key>CFBundleDisplayName</key>
    <string>CHDMAN</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.chdman-createcd</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>CHDMAN</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF

echo "→ Clearing quarantine flag..."
xattr -cr "$APP"

echo ""
echo "✓ Built: $APP"
echo "  Drag it to /Applications or double-click to run."
