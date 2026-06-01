# CHDMAN — Batch Disc Image Converter

A retro PS1-themed macOS app for batch converting `.cue` and `.iso` disc images to `.chd` format using [chdman](https://docs.mamedev.org/tools/chdman.html).

![CHDMAN Banner](Picture.jpg)

---

## Features

- Batch queue — add multiple files at once
- Drag & drop support for `.cue` and `.iso` files
- PS1-style UI with custom gradient widgets and glow effects
- Crash Bandicoot theme music with mute toggle
- Pre-flight system check (Homebrew + chdman)
- One-click install shortcut if chdman is missing
- Console output log for each conversion
- Saves `.chd` next to the source file, or to a custom output folder

---

## Requirements

| Requirement | How to install |
|---|---|
| macOS | — |
| Python 3.13 | [python.org](https://www.python.org/downloads/) |
| Homebrew | [brew.sh](https://brew.sh) |
| chdman (MAME) | `brew install mame` |

Python packages (installed automatically if missing):
```bash
pip3 install pillow tkinterdnd2
```

---

## Usage

### Option A — Run the .app directly
1. Download or clone this repo
2. Open `CHDMAN.app` (double-click)
3. If macOS blocks it: right-click → Open → Open anyway
4. The pre-flight check will guide you if anything is missing

### Option B — Run from Terminal
```bash
python3 chdman_tool.py
```

### Option C — Double-click launcher
Double-click `chdman_tool.command` in Finder.

---

## Build the .app yourself

```bash
bash build_app.sh
```

This creates `CHDMAN.app` in the current folder. Drag it to `/Applications` to install.

---

## Supported formats

| Format | Description |
|---|---|
| `.cue` | CUE sheet + associated audio/data tracks |
| `.iso` | Standard ISO disc image |

Output is always `.chd` (Compressed Hunks of Data) — a lossless compressed format commonly used in emulators like RetroArch and MAME.

---

## Project structure

```
CHDMAN/
├── CHDMAN.app/              # Pre-built macOS app bundle
├── chdman_tool.py           # Main application source
├── build_app.sh             # Script to rebuild the .app bundle
├── chdman_tool.command      # Double-click Terminal launcher
├── Picture.jpg              # Banner image used in the UI
└── Crash Bandicoot ....mp3  # Background music
```

---

## License

Personal use. chdman is part of [MAME](https://www.mamedev.org/) and subject to its own license.
