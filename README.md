# CHDMAN — Batch Disc Image Converter

A retro PS1-themed macOS app for batch converting `.cue` and `.iso` disc images to `.chd` format using [chdman](https://docs.mamedev.org/tools/chdman.html).

![CHDMAN Banner](Picture.jpg)

---

## Download

👉 **[Download latest release (DMG)](https://github.com/bumsar1/CHDMAN-Mac/releases/latest)**

Open the `.dmg`, drag **CHDMAN.app** into your Applications folder, and you're done. No Python or Homebrew required — everything is bundled inside the app.

The app includes a pre-flight check on startup that will guide you if `chdman` is missing.

---

## Features

- Batch queue — add multiple files at once
- Drag & drop support for `.cue` and `.iso` files
- PS1-style UI with custom gradient widgets and glow effects
- Crash Bandicoot theme music with mute toggle
- Pre-flight system check (Homebrew + chdman) on startup
- One-click install shortcut if chdman is missing
- Console output log for each conversion
- Saves `.chd` next to the source file, or to a custom output folder

---

## Supported formats

| Format | Description |
|---|---|
| `.cue` | CUE sheet + associated audio/data tracks |
| `.iso` | Standard ISO disc image |

Output is always `.chd` (Compressed Hunks of Data) — a lossless compressed format commonly used in emulators like RetroArch and MAME.

---

## Build it yourself

If you prefer to run from source:

**Requirements:**
- macOS
- Python 3.13 — [python.org](https://www.python.org/downloads/)
- Homebrew — [brew.sh](https://brew.sh)
- chdman: `brew install mame`
- Python packages: `pip3 install pillow tkinterdnd2`

**Option A — Build the .app**
```bash
git clone https://github.com/bumsar1/CHDMAN-Mac.git
cd CHDMAN-Mac
bash build_app.sh
```
This generates `CHDMAN.app` in the folder. Drag it to `/Applications` to install.

**Option B — Run directly from Terminal**
```bash
python3 chdman_tool.py
```

**Option C — Double-click launcher**
Double-click `chdman_tool.command` in Finder.

---

## Project structure

```
CHDMAN/
├── chdman_tool.py           # Main application source
├── build_app.sh             # Script to build the .app bundle
├── chdman_tool.command      # Double-click Terminal launcher
├── Picture.jpg              # Banner image used in the UI
└── Crash Bandicoot ....mp3  # Background music
```

---

## License

Personal use. chdman is part of [MAME](https://www.mamedev.org/) and subject to its own license.
